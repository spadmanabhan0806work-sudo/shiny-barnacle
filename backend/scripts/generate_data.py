"""Generate sample data files for Operyx Supply Chain PoC."""
import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
(DATA_DIR / "invoices").mkdir(exist_ok=True)

SKUS = [
    ("SKU-001", "Industrial Bearing A"),
    ("SKU-002", "Hydraulic Pump B"),
    ("SKU-003", "Steel Plate C"),
    ("SKU-004", "Copper Wire D"),
    ("SKU-005", "Aluminum Sheet E"),
    ("SKU-006", "Rubber Gasket F"),
    ("SKU-007", "Circuit Board G"),
    ("SKU-008", "Motor Assembly H"),
    ("SKU-009", "Valve Kit I"),
    ("SKU-010", "Filter Element J"),
    ("SKU-011", "Gear Box K"),
    ("SKU-012", "Conveyor Belt L"),
    ("SKU-013", "Sensor Module M"),
    ("SKU-014", "Control Panel N"),
    ("SKU-015", "Pneumatic Cylinder O"),
    ("SKU-016", "Heat Exchanger P"),
    ("SKU-017", "Compressor Unit Q"),
    ("SKU-018", "Drive Belt R"),
    ("SKU-019", "Lubricant Oil S"),
    ("SKU-020", "Safety Valve T"),
]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def generate_sales_history():
    rows = []
    base_year = 2024
    for year_offset in range(2):
        year = base_year + year_offset
        for month_idx, month in enumerate(MONTHS):
            for sku, name in SKUS:
                seasonal = 1.0 + 0.2 * (month_idx % 6) / 5
                trend = 1.0 + year_offset * 0.08
                base = random.randint(80, 400)
                units = int(base * seasonal * trend)
                revenue = round(units * random.uniform(12.5, 85.0), 2)
                rows.append({
                    "sku": sku, "product_name": name, "month": month,
                    "year": year, "units_sold": units, "revenue": revenue,
                })
    path = DATA_DIR / "sales_history.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sku", "product_name", "month", "year", "units_sold", "revenue"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {path} ({len(rows)} rows)")


def generate_suppliers():
    suppliers = [
        {"name": "Pacific Metals Corp", "country": "China", "category": "Raw Materials", "risk_score": 82, "risk_level": "high",
         "contract_expiry": "2025-08-15", "on_time_delivery_pct": 72, "quality_incidents": 5, "financial_health": "stressed", "delay_count": 8},
        {"name": "GlobalChem Industries", "country": "India", "category": "Chemicals", "risk_score": 78, "risk_level": "high",
         "contract_expiry": "2025-06-30", "on_time_delivery_pct": 68, "quality_incidents": 4, "financial_health": "at_risk", "delay_count": 6},
        {"name": "Eastern Components Ltd", "country": "Vietnam", "category": "Electronics", "risk_score": 75, "risk_level": "high",
         "contract_expiry": "2025-09-01", "on_time_delivery_pct": 75, "quality_incidents": 3, "financial_health": "stable", "delay_count": 5},
        {"name": "Midwest Steel Supply", "country": "USA", "category": "Steel", "risk_score": 55, "risk_level": "medium",
         "contract_expiry": "2026-03-15", "on_time_delivery_pct": 85, "quality_incidents": 2, "financial_health": "stable", "delay_count": 3},
        {"name": "EuroParts GmbH", "country": "Germany", "category": "Automotive", "risk_score": 48, "risk_level": "medium",
         "contract_expiry": "2026-01-20", "on_time_delivery_pct": 88, "quality_incidents": 1, "financial_health": "stable", "delay_count": 2},
        {"name": "Nordic Logistics AB", "country": "Sweden", "category": "Logistics", "risk_score": 52, "risk_level": "medium",
         "contract_expiry": "2025-12-31", "on_time_delivery_pct": 82, "quality_incidents": 2, "financial_health": "stable", "delay_count": 4},
        {"name": "Atlantic Rubber Co", "country": "Brazil", "category": "Rubber", "risk_score": 58, "risk_level": "medium",
         "contract_expiry": "2026-06-01", "on_time_delivery_pct": 80, "quality_incidents": 2, "financial_health": "stable", "delay_count": 3},
        {"name": "Precision Tools Inc", "country": "USA", "category": "Tools", "risk_score": 22, "risk_level": "low",
         "contract_expiry": "2027-01-15", "on_time_delivery_pct": 96, "quality_incidents": 0, "financial_health": "strong", "delay_count": 0},
        {"name": "Quality Fasteners Co", "country": "Canada", "category": "Hardware", "risk_score": 18, "risk_level": "low",
         "contract_expiry": "2027-03-01", "on_time_delivery_pct": 97, "quality_incidents": 0, "financial_health": "strong", "delay_count": 0},
        {"name": "Summit Packaging", "country": "USA", "category": "Packaging", "risk_score": 25, "risk_level": "low",
         "contract_expiry": "2026-11-30", "on_time_delivery_pct": 94, "quality_incidents": 1, "financial_health": "stable", "delay_count": 1},
        {"name": "Green Valley Plastics", "country": "Mexico", "category": "Plastics", "risk_score": 30, "risk_level": "low",
         "contract_expiry": "2026-08-15", "on_time_delivery_pct": 91, "quality_incidents": 1, "financial_health": "stable", "delay_count": 1},
        {"name": "TechCircuits SA", "country": "France", "category": "Electronics", "risk_score": 20, "risk_level": "low",
         "contract_expiry": "2027-06-01", "on_time_delivery_pct": 98, "quality_incidents": 0, "financial_health": "strong", "delay_count": 0},
        {"name": "Harbor Shipping LLC", "country": "USA", "category": "Freight", "risk_score": 28, "risk_level": "low",
         "contract_expiry": "2026-04-30", "on_time_delivery_pct": 92, "quality_incidents": 0, "financial_health": "stable", "delay_count": 1},
        {"name": "Alpine Materials AG", "country": "Switzerland", "category": "Specialty Metals", "risk_score": 15, "risk_level": "low",
         "contract_expiry": "2027-12-31", "on_time_delivery_pct": 99, "quality_incidents": 0, "financial_health": "strong", "delay_count": 0},
        {"name": "Southern Bearings Ltd", "country": "UK", "category": "Bearings", "risk_score": 24, "risk_level": "low",
         "contract_expiry": "2026-09-15", "on_time_delivery_pct": 95, "quality_incidents": 0, "financial_health": "stable", "delay_count": 0},
    ]
    for i, s in enumerate(suppliers, 1):
        s["id"] = i
        s["contact_email"] = f"procurement@{s['name'].lower().replace(' ', '').replace('.', '')[:20]}.com"
    path = DATA_DIR / "suppliers.json"
    path.write_text(json.dumps(suppliers, indent=2), encoding="utf-8")
    print(f"Created {path}")


def generate_shipments():
    statuses = ["in_transit", "delivered", "delayed", "at_risk", "pending"]
    carriers = ["FedEx Freight", "DHL Supply Chain", "Maersk", "UPS Freight", "XPO Logistics"]
    origins = ["Shanghai, CN", "Mumbai, IN", "Hamburg, DE", "Los Angeles, US", "São Paulo, BR"]
    destinations = ["Chicago DC", "Dallas DC", "Atlanta DC", "Newark DC", "Seattle DC"]
    supplier_names = ["Pacific Metals Corp", "GlobalChem Industries", "EuroParts GmbH", "Midwest Steel Supply", "Precision Tools Inc"]
    shipments = []
    today = date.today()
    for i in range(1, 26):
        status = random.choice(statuses)
        if i <= 5:
            status = "delayed"
        elif i <= 8:
            status = "at_risk"
        eta = today + timedelta(days=random.randint(-5, 20))
        risk = "high" if status in ("delayed", "at_risk") else "none"
        shipments.append({
            "id": i,
            "tracking_number": f"SHP-{2025000 + i}",
            "order_id": random.randint(1, 30),
            "supplier_name": random.choice(supplier_names),
            "origin": random.choice(origins),
            "destination": random.choice(destinations),
            "status": status,
            "eta": eta.isoformat(),
            "carrier": random.choice(carriers),
            "risk_flag": risk,
        })
    path = DATA_DIR / "shipments.json"
    path.write_text(json.dumps(shipments, indent=2), encoding="utf-8")
    print(f"Created {path}")


def generate_purchase_orders():
    statuses = ["pending", "approved", "shipped", "delivered", "cancelled"]
    orders = []
    today = date.today()
    supplier_ids = list(range(1, 16))
    supplier_names = [
        "Pacific Metals Corp", "GlobalChem Industries", "Eastern Components Ltd",
        "Midwest Steel Supply", "EuroParts GmbH", "Nordic Logistics AB", "Atlantic Rubber Co",
        "Precision Tools Inc", "Quality Fasteners Co", "Summit Packaging",
        "Green Valley Plastics", "TechCircuits SA", "Harbor Shipping LLC",
        "Alpine Materials AG", "Southern Bearings Ltd",
    ]
    for i in range(1, 31):
        sid = random.choice(supplier_ids)
        order_date = today - timedelta(days=random.randint(5, 120))
        orders.append({
            "id": i,
            "po_number": f"PO-2025-{i:04d}",
            "supplier_id": sid,
            "supplier_name": supplier_names[sid - 1],
            "status": random.choice(statuses),
            "total_amount": round(random.uniform(5000, 250000), 2),
            "currency": "USD",
            "order_date": order_date.isoformat(),
            "expected_delivery": (order_date + timedelta(days=random.randint(14, 45))).isoformat(),
            "items_count": random.randint(3, 25),
        })
    path = DATA_DIR / "purchase_orders.json"
    path.write_text(json.dumps(orders, indent=2), encoding="utf-8")
    print(f"Created {path}")


def generate_warehouse_inventory():
    warehouses = [
        {"id": 1, "name": "Chicago Central DC", "location": "Chicago, IL", "capacity_units": 50000, "manager": "Sarah Chen"},
        {"id": 2, "name": "Dallas Regional DC", "location": "Dallas, TX", "capacity_units": 35000, "manager": "Mike Rodriguez"},
        {"id": 3, "name": "Newark East Coast DC", "location": "Newark, NJ", "capacity_units": 42000, "manager": "Lisa Park"},
    ]
    categories = ["Raw Materials", "Components", "Finished Goods", "MRO", "Packaging"]
    inventory = []
    item_id = 1
    for wh in warehouses:
        used = 0
        for idx in range(17 if wh["id"] < 3 else 16):
            sku, name = SKUS[idx % len(SKUS)]
            qty = random.randint(100, 5000)
            unit_val = round(random.uniform(5, 150), 2)
            used += qty
            inventory.append({
                "id": item_id, "sku": sku, "product_name": name,
                "warehouse_id": wh["id"], "warehouse_name": wh["name"],
                "quantity": qty, "unit_value": unit_val,
                "reorder_point": int(qty * 0.2), "category": random.choice(categories),
            })
            item_id += 1
        wh["used_units"] = used
        wh["utilization_pct"] = round(used / wh["capacity_units"] * 100, 1)
    data = {"warehouses": warehouses, "inventory": inventory}
    path = DATA_DIR / "warehouse_inventory.json"
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Created {path}")


def generate_invoices():
    invoices = [
        {
            "filename": "invoice_acme_2025_001.txt",
            "content": """INVOICE
Invoice Number: INV-2025-0847
Date: March 15, 2025
Due Date: April 14, 2025

Vendor: Pacific Metals Corp
123 Industrial Blvd, Shanghai, China
Tax ID: CN-8847291

Bill To:
Operyx Manufacturing Inc.
500 Supply Chain Way
Chicago, IL 60601

Line Items:
1. Steel Plate C (SKU-003) - Qty: 500 @ $45.00 = $22,500.00
2. Copper Wire D (SKU-004) - Qty: 1200 @ $12.50 = $15,000.00
3. Aluminum Sheet E (SKU-005) - Qty: 800 @ $28.00 = $22,400.00

Subtotal: $59,900.00
Tax (8%): $4,792.00
Shipping: $1,250.00
TOTAL DUE: $65,942.00

Payment Terms: Net 30
PO Reference: PO-2025-0012
""",
        },
        {
            "filename": "invoice_globalchem_2025_002.txt",
            "content": """INVOICE
Invoice Number: GC-INV-4421
Date: April 2, 2025
Due Date: May 2, 2025

Vendor: GlobalChem Industries
45 Chemical Park, Mumbai, India

Bill To:
Operyx Manufacturing Inc.
500 Supply Chain Way
Chicago, IL 60601

Line Items:
1. Lubricant Oil S (SKU-019) - Qty: 200 @ $85.00 = $17,000.00
2. Rubber Gasket F (SKU-006) - Qty: 3000 @ $2.50 = $7,500.00
3. Filter Element J (SKU-010) - Qty: 150 @ $42.00 = $6,300.00

Subtotal: $30,800.00
Tax (5%): $1,540.00
TOTAL DUE: $32,340.00

Payment Terms: Net 45
PO Reference: PO-2025-0008
Contract: Annual Supply Agreement #GC-2024-112
""",
        },
        {
            "filename": "invoice_precision_2025_003.txt",
            "content": """INVOICE
Invoice Number: PT-2025-1199
Date: April 18, 2025
Due Date: May 18, 2025

Vendor: Precision Tools Inc
890 Toolmaker Drive, Detroit, MI 48201

Bill To:
Operyx Manufacturing Inc.
500 Supply Chain Way
Chicago, IL 60601

Line Items:
1. Industrial Bearing A (SKU-001) - Qty: 250 @ $125.00 = $31,250.00
2. Gear Box K (SKU-011) - Qty: 45 @ $890.00 = $40,050.00
3. Drive Belt R (SKU-018) - Qty: 600 @ $18.50 = $11,100.00

Subtotal: $82,400.00
Tax (6%): $4,944.00
TOTAL DUE: $87,344.00

Payment Terms: Net 30
PO Reference: PO-2025-0025
""",
        },
    ]
    for inv in invoices:
        path = DATA_DIR / "invoices" / inv["filename"]
        path.write_text(inv["content"], encoding="utf-8")
        print(f"Created {path}")


if __name__ == "__main__":
    random.seed(42)
    generate_sales_history()
    generate_suppliers()
    generate_shipments()
    generate_purchase_orders()
    generate_warehouse_inventory()
    generate_invoices()
    print("All sample data generated.")
