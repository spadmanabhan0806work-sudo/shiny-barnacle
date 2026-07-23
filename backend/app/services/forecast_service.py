from collections import defaultdict
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Inventory, SalesHistory
from app.services.ai_service import AIService


MONTH_ORDER = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _period_key(year: int, month: str) -> str:
    return f"{year}-{month}"


def _sort_periods(periods: list[str]) -> list[str]:
    def key(p: str) -> tuple[int, int]:
        year_str, month = p.split("-")
        return int(year_str), MONTH_ORDER.index(month)

    return sorted(periods, key=key)


class ForecastService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService(db)

    def get_available_skus(self) -> list[dict[str, str]]:
        rows = self.db.query(SalesHistory.sku, SalesHistory.product_name).distinct().all()
        return [{"sku": r.sku, "product_name": r.product_name} for r in rows]

    def upload_csv(self, content: str) -> dict[str, Any]:
        from io import StringIO

        df = pd.read_csv(StringIO(content))
        required = {"sku", "month", "year", "units_sold"}
        if not required.issubset(df.columns):
            raise ValueError(f"CSV must contain columns: {required}")

        self.db.query(SalesHistory).delete()
        for idx, row in df.iterrows():
            self.db.add(SalesHistory(
                id=idx + 1,
                sku=str(row["sku"]),
                product_name=str(row.get("product_name", row["sku"])),
                month=str(row["month"]),
                year=int(row["year"]),
                units_sold=int(row["units_sold"]),
                revenue=float(row.get("revenue", 0)),
            ))
        self.db.commit()
        return {"rows_imported": len(df), "skus": df["sku"].nunique()}

    async def generate_forecast(self, sku: str | None = None, horizon_months: int = 6) -> dict[str, Any]:
        if not sku:
            first = self.db.query(SalesHistory).first()
            sku = first.sku if first else "SKU-001"

        rows = self.db.query(SalesHistory).filter(SalesHistory.sku == sku).all()
        if not rows:
            raise ValueError(f"No sales data for SKU {sku}")

        product_name = rows[0].product_name
        period_data: dict[str, int] = defaultdict(int)
        for r in rows:
            period_data[_period_key(r.year, r.month)] += r.units_sold

        periods = _sort_periods(list(period_data.keys()))
        values = [period_data[p] for p in periods]

        window = min(3, len(values))
        ma = sum(values[-window:]) / window if values else 0

        seasonal_factors = self._compute_seasonality(periods, values)
        last_period = periods[-1]
        last_year, last_month = last_period.split("-")
        last_month_idx = MONTH_ORDER.index(last_month)

        forecast_points = []
        for i, p in enumerate(periods):
            v = period_data[p]
            forecast_points.append({
                "period": p, "actual": float(v), "forecast": float(v),
                "lower_bound": float(v * 0.9), "upper_bound": float(v * 1.1),
            })

        current_year = int(last_year)
        month_idx = last_month_idx
        for h in range(1, horizon_months + 1):
            month_idx += 1
            if month_idx >= 12:
                month_idx = 0
                current_year += 1
            month = MONTH_ORDER[month_idx]
            period = _period_key(current_year, month)
            seasonal = seasonal_factors.get(month, 1.0)
            trend = 1.0 + 0.02 * h
            predicted = ma * seasonal * trend
            std_dev = max(predicted * 0.12, 10)
            forecast_points.append({
                "period": period, "actual": None, "forecast": round(predicted, 1),
                "lower_bound": round(predicted - 1.96 * std_dev, 1),
                "upper_bound": round(predicted + 1.96 * std_dev, 1),
            })

        avg_demand = sum(values[-6:]) / min(6, len(values)) if values else ma
        safety_stock = int(avg_demand * 1.5)
        confidence = min(0.95, 0.7 + len(values) * 0.01)

        inventory_recs = self._inventory_recommendations(sku, safety_stock, avg_demand)

        ai_summary = await self.ai.generate(
            f"Provide demand forecast narrative for {sku}",
            context={"sku": sku, "product_name": product_name, "avg_demand": round(avg_demand, 1),
                     "safety_stock": safety_stock, "horizon": horizon_months},
            system="forecast analysis",
        )

        return {
            "sku": sku,
            "product_name": product_name,
            "forecast": forecast_points,
            "safety_stock": safety_stock,
            "confidence": round(confidence, 2),
            "ai_summary": ai_summary,
            "recommended_inventory": inventory_recs,
        }

    def _compute_seasonality(self, periods: list[str], values: list[int]) -> dict[str, float]:
        month_totals: dict[str, list[int]] = defaultdict(list)
        for p, v in zip(periods, values):
            month = p.split("-")[1]
            month_totals[month].append(v)
        overall_avg = sum(values) / len(values) if values else 1
        factors = {}
        for month, vals in month_totals.items():
            month_avg = sum(vals) / len(vals)
            factors[month] = month_avg / overall_avg if overall_avg else 1.0
        return factors

    def _inventory_recommendations(self, sku: str, safety_stock: int, avg_demand: float) -> list[dict]:
        inv_rows = self.db.query(Inventory).filter(Inventory.sku == sku).all()
        recs = []
        target = int(safety_stock + avg_demand)
        for inv in inv_rows:
            gap = target - inv.quantity
            recs.append({
                "warehouse": inv.warehouse_name,
                "current_stock": inv.quantity,
                "recommended_stock": target,
                "action": "replenish" if gap > 0 else "adequate",
                "gap": max(gap, 0),
            })
        if not recs:
            recs.append({
                "warehouse": "All Warehouses",
                "current_stock": 0,
                "recommended_stock": target,
                "action": "replenish",
                "gap": target,
            })
        return recs
