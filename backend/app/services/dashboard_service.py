from sqlalchemy.orm import Session

from app.models import Inventory, Order, Shipment, Supplier, Vehicle, Warehouse


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_kpis(self) -> dict:
        total_orders = self.db.query(Order).count()
        inventory_value = sum(i.quantity * i.unit_value for i in self.db.query(Inventory).all())
        delayed_shipments = self.db.query(Shipment).filter(Shipment.status == "delayed").count()
        suppliers = self.db.query(Supplier).all()
        avg_risk = sum(s.risk_score for s in suppliers) / len(suppliers) if suppliers else 0
        warehouses = self.db.query(Warehouse).all()
        avg_util = sum(w.utilization_pct for w in warehouses) / len(warehouses) if warehouses else 0
        vehicles = self.db.query(Vehicle).all()
        active = sum(1 for v in vehicles if v.status == "in_transit")
        delayed_vehicles = sum(1 for v in vehicles if v.status == "delayed")

        return {
            "total_orders": total_orders,
            "inventory_value": round(inventory_value, 2),
            "delayed_shipments": delayed_shipments,
            "avg_supplier_risk": round(avg_risk, 1),
            "warehouse_utilization": round(avg_util, 1),
            "transportation_active": active,
            "transportation_delayed": delayed_vehicles,
        }

    def get_charts(self) -> dict:
        from app.models import SalesHistory
        from collections import defaultdict

        sales = self.db.query(SalesHistory).all()
        period_totals: dict[str, int] = defaultdict(int)
        for s in sales:
            period_totals[f"{s.year}-{s.month}"] += s.units_sold

        months_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        forecast_data = []
        for period, total in sorted(period_totals.items(), key=lambda x: (int(x[0].split("-")[0]), months_order.index(x[0].split("-")[1]))):
            forecast_data.append({"period": period, "actual": total, "forecast": int(total * 1.05)})

        last_periods = forecast_data[-6:]
        for i, p in enumerate(last_periods):
            p["forecast"] = int(p["actual"] * (1.03 + i * 0.01))

        warehouses = self.db.query(Warehouse).all()
        utilization_data = [{"name": w.name, "utilization": w.utilization_pct, "used": w.used_units, "capacity": w.capacity_units} for w in warehouses]

        vehicles = self.db.query(Vehicle).all()
        status_counts: dict[str, int] = {}
        for v in vehicles:
            status_counts[v.status] = status_counts.get(v.status, 0) + 1
        transport_data = [{"status": k.replace("_", " ").title(), "count": v} for k, v in status_counts.items()]

        return {
            "inventory_forecast": forecast_data[-12:],
            "warehouse_utilization": utilization_data,
            "transportation_status": transport_data,
        }
