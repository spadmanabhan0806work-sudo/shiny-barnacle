from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Shipment, Vehicle, Warehouse


class LogisticsService:
    def __init__(self, db: Session):
        self.db = db

    def list_shipments(self, status: str | None = None) -> list[Shipment]:
        query = self.db.query(Shipment)
        if status:
            query = query.filter(Shipment.status == status)
        return query.order_by(Shipment.eta).all()

    def list_warehouses(self) -> list[Warehouse]:
        return self.db.query(Warehouse).all()

    def list_vehicles(self) -> list[Vehicle]:
        return self.db.query(Vehicle).all()

    def get_alerts(self) -> list[dict]:
        alerts = []
        today = date.today()

        delayed = self.db.query(Shipment).filter(Shipment.status == "delayed").all()
        for s in delayed:
            alerts.append({
                "id": f"ship-delay-{s.id}",
                "severity": "high",
                "title": f"Delayed Shipment: {s.tracking_number}",
                "description": f"{s.supplier_name} shipment to {s.destination} is delayed. ETA was {s.eta}.",
                "timestamp": datetime.utcnow().isoformat(),
            })

        at_risk = self.db.query(Shipment).filter(Shipment.status == "at_risk").all()
        for s in at_risk:
            alerts.append({
                "id": f"ship-risk-{s.id}",
                "severity": "medium",
                "title": f"At-Risk Shipment: {s.tracking_number}",
                "description": f"Shipment from {s.origin} may miss delivery window.",
                "timestamp": datetime.utcnow().isoformat(),
            })

        warehouses = self.db.query(Warehouse).filter(Warehouse.utilization_pct > 85).all()
        for w in warehouses:
            alerts.append({
                "id": f"wh-cap-{w.id}",
                "severity": "medium",
                "title": f"Warehouse Capacity Alert: {w.name}",
                "description": f"Utilization at {w.utilization_pct}% — approaching capacity limits.",
                "timestamp": datetime.utcnow().isoformat(),
            })

        vehicles = self.db.query(Vehicle).filter(Vehicle.status == "delayed").all()
        for v in vehicles:
            alerts.append({
                "id": f"veh-delay-{v.id}",
                "severity": "high",
                "title": f"Vehicle Delayed: {v.vehicle_id}",
                "description": f"{v.driver} reports delay at {v.location}.",
                "timestamp": datetime.utcnow().isoformat(),
            })

        overdue = self.db.query(Shipment).filter(
            Shipment.eta < today,
            Shipment.status.notin_(["delivered"]),
        ).all()
        for s in overdue:
            if not any(a["id"] == f"ship-delay-{s.id}" for a in alerts):
                alerts.append({
                    "id": f"ship-overdue-{s.id}",
                    "severity": "high",
                    "title": f"Overdue Delivery: {s.tracking_number}",
                    "description": f"Past ETA ({s.eta}). Carrier: {s.carrier}.",
                    "timestamp": datetime.utcnow().isoformat(),
                })

        return alerts
