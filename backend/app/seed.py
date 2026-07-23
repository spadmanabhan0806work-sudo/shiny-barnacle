import csv
import json
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import Base, SessionLocal, engine
from app.models import (
    Inventory,
    Order,
    SalesHistory,
    Shipment,
    Supplier,
    Vehicle,
    Warehouse,
)

settings = get_settings()


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value[:10])


def seed_database(db: Session) -> None:
    if db.query(Supplier).count() > 0:
        return

    from app.config import DATA_DIR

    suppliers_path = DATA_DIR / "suppliers.json"
    if suppliers_path.exists():
        suppliers = json.loads(suppliers_path.read_text(encoding="utf-8"))
        for s in suppliers:
            db.add(Supplier(
                id=s["id"], name=s["name"], country=s.get("country", ""),
                category=s.get("category", ""), risk_score=s.get("risk_score", 0),
                risk_level=s.get("risk_level", "low"),
                contract_expiry=_parse_date(s.get("contract_expiry")),
                on_time_delivery_pct=s.get("on_time_delivery_pct", 100),
                quality_incidents=s.get("quality_incidents", 0),
                financial_health=s.get("financial_health", "stable"),
                delay_count=s.get("delay_count", 0),
                contact_email=s.get("contact_email", ""),
            ))

    orders_path = DATA_DIR / "purchase_orders.json"
    if orders_path.exists():
        orders = json.loads(orders_path.read_text(encoding="utf-8"))
        for o in orders:
            db.add(Order(
                id=o["id"], po_number=o["po_number"], supplier_id=o["supplier_id"],
                supplier_name=o["supplier_name"], status=o.get("status", "pending"),
                total_amount=o.get("total_amount", 0), currency=o.get("currency", "USD"),
                order_date=_parse_date(o.get("order_date")),
                expected_delivery=_parse_date(o.get("expected_delivery")),
                items_count=o.get("items_count", 0),
            ))

    wh_path = DATA_DIR / "warehouse_inventory.json"
    if wh_path.exists():
        wh_data = json.loads(wh_path.read_text(encoding="utf-8"))
        for w in wh_data.get("warehouses", []):
            db.add(Warehouse(
                id=w["id"], name=w["name"], location=w.get("location", ""),
                capacity_units=w.get("capacity_units", 0), used_units=w.get("used_units", 0),
                utilization_pct=w.get("utilization_pct", 0), manager=w.get("manager", ""),
            ))
        for item in wh_data.get("inventory", []):
            db.add(Inventory(
                id=item["id"], sku=item["sku"], product_name=item.get("product_name", ""),
                warehouse_id=item["warehouse_id"], warehouse_name=item.get("warehouse_name", ""),
                quantity=item.get("quantity", 0), unit_value=item.get("unit_value", 0),
                reorder_point=item.get("reorder_point", 0), category=item.get("category", ""),
            ))

    shipments_path = DATA_DIR / "shipments.json"
    if shipments_path.exists():
        shipments = json.loads(shipments_path.read_text(encoding="utf-8"))
        for s in shipments:
            db.add(Shipment(
                id=s["id"], tracking_number=s["tracking_number"],
                order_id=s.get("order_id"), supplier_name=s.get("supplier_name", ""),
                origin=s.get("origin", ""), destination=s.get("destination", ""),
                status=s.get("status", "in_transit"), eta=_parse_date(s.get("eta")),
                carrier=s.get("carrier", ""), risk_flag=s.get("risk_flag", "none"),
            ))

    sales_path = DATA_DIR / "sales_history.csv"
    if sales_path.exists():
        with sales_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            row_id = 1
            for row in reader:
                db.add(SalesHistory(
                    id=row_id, sku=row["sku"], product_name=row.get("product_name", ""),
                    month=row["month"], year=int(row["year"]),
                    units_sold=int(row["units_sold"]), revenue=float(row.get("revenue", 0)),
                ))
                row_id += 1

    vehicles = [
        {"id": 1, "vehicle_id": "TRK-001", "type": "Semi-Trailer", "status": "in_transit",
         "location": "I-80 near Des Moines, IA", "driver": "James Wilson", "capacity_tons": 22, "current_load_tons": 18},
        {"id": 2, "vehicle_id": "TRK-002", "type": "Box Truck", "status": "available",
         "location": "Chicago Central DC", "driver": "Unassigned", "capacity_tons": 8, "current_load_tons": 0},
        {"id": 3, "vehicle_id": "TRK-003", "type": "Semi-Trailer", "status": "delayed",
         "location": "I-35 near Oklahoma City, OK", "driver": "Maria Santos", "capacity_tons": 22, "current_load_tons": 20},
        {"id": 4, "vehicle_id": "VAN-001", "type": "Delivery Van", "status": "in_transit",
         "location": "Downtown Dallas, TX", "driver": "Kevin Brown", "capacity_tons": 2, "current_load_tons": 1.5},
        {"id": 5, "vehicle_id": "TRK-004", "type": "Flatbed", "status": "maintenance",
         "location": "Newark East Coast DC", "driver": "Unassigned", "capacity_tons": 18, "current_load_tons": 0},
        {"id": 6, "vehicle_id": "TRK-005", "type": "Semi-Trailer", "status": "in_transit",
         "location": "I-95 near Baltimore, MD", "driver": "David Kim", "capacity_tons": 22, "current_load_tons": 19},
    ]
    for v in vehicles:
        db.add(Vehicle(**v))

    db.commit()


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
