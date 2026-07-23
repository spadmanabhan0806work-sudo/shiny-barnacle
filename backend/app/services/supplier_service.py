from sqlalchemy.orm import Session

from app.models import Supplier
from app.services.ai_service import AIService


class SupplierService:
    def __init__(self, db: Session):
        self.db = db
        self.ai = AIService(db)

    def list_suppliers(self, risk_level: str | None = None) -> list[Supplier]:
        query = self.db.query(Supplier)
        if risk_level:
            query = query.filter(Supplier.risk_level == risk_level)
        return query.order_by(Supplier.risk_score.desc()).all()

    async def analyze_supplier(self, supplier_id: int) -> dict:
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise ValueError(f"Supplier {supplier_id} not found")

        risk_factors = []
        if supplier.risk_score >= 70:
            risk_factors.append(f"Elevated risk score: {supplier.risk_score}")
        if supplier.on_time_delivery_pct < 80:
            risk_factors.append(f"Low on-time delivery: {supplier.on_time_delivery_pct}%")
        if supplier.quality_incidents > 2:
            risk_factors.append(f"{supplier.quality_incidents} quality incidents reported")
        if supplier.financial_health in ("stressed", "at_risk"):
            risk_factors.append(f"Financial health: {supplier.financial_health}")
        if supplier.delay_count > 3:
            risk_factors.append(f"{supplier.delay_count} delivery delays in past 12 months")
        if not risk_factors:
            risk_factors.append("No significant risk factors identified")

        recommendations = []
        if supplier.risk_level == "high":
            recommendations.extend([
                "Identify and qualify backup suppliers for critical SKUs",
                "Schedule executive review of contract terms before expiry",
                "Implement enhanced quality inspection on incoming shipments",
                "Consider reducing order volumes by 20% while evaluating alternatives",
            ])
        elif supplier.risk_level == "medium":
            recommendations.extend([
                "Monitor delivery performance weekly",
                "Request updated financial statements",
                "Review contract renewal timeline",
            ])
        else:
            recommendations.extend([
                "Maintain current partnership level",
                "Consider volume consolidation for better pricing",
            ])

        ai_analysis = await self.ai.generate(
            f"Analyze supplier risk for {supplier.name}",
            context={
                "name": supplier.name,
                "risk_score": supplier.risk_score,
                "risk_level": supplier.risk_level,
                "on_time_delivery": supplier.on_time_delivery_pct,
                "quality_incidents": supplier.quality_incidents,
            },
            system="supplier risk analysis",
        )

        return {
            "supplier": supplier,
            "risk_factors": risk_factors,
            "recommendations": recommendations,
            "ai_analysis": ai_analysis,
        }
