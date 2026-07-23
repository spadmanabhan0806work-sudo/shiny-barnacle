# API Documentation

Base URL: `http://localhost:8000`

Interactive docs: http://localhost:8000/docs

## Health

### GET /api/health

```json
{
  "status": "ok",
  "ai_provider": "mock"
}
```

---

## Dashboard

### GET /api/dashboard/kpis

Returns executive KPI metrics.

**Response:**
```json
{
  "total_orders": 30,
  "inventory_value": 9140441.22,
  "delayed_shipments": 5,
  "avg_supplier_risk": 42.0,
  "warehouse_utilization": 78.5,
  "transportation_active": 3,
  "transportation_delayed": 1
}
```

### GET /api/dashboard/charts

Returns chart data for forecast, utilization, and transport.

**Response:**
```json
{
  "inventory_forecast": [
    { "period": "2024-Jan", "actual": 4200, "forecast": 4410 }
  ],
  "warehouse_utilization": [
    { "name": "Chicago Central DC", "utilization": 82.5, "used": 41250, "capacity": 50000 }
  ],
  "transportation_status": [
    { "status": "In Transit", "count": 3 }
  ]
}
```

### GET /api/dashboard/insights

Returns AI-generated insight bullets.

**Response:**
```json
[
  {
    "title": "Shipment Delays Detected",
    "description": "5 shipments are currently delayed.",
    "severity": "high",
    "category": "logistics"
  }
]
```

---

## Forecast

### POST /api/forecast/upload

Upload sales history CSV (multipart/form-data).

**Form fields:**
- `file` — CSV with columns: sku, product_name, month, year, units_sold, revenue

**Response:**
```json
{
  "rows_imported": 480,
  "skus": 20
}
```

### POST /api/forecast/generate

Generate demand forecast.

**Request:**
```json
{
  "sku": "SKU-001",
  "horizon_months": 6
}
```

**Response:**
```json
{
  "sku": "SKU-001",
  "product_name": "Industrial Bearing A",
  "forecast": [
    {
      "period": "2024-Jan",
      "actual": 320,
      "forecast": 320,
      "lower_bound": 288,
      "upper_bound": 352
    }
  ],
  "safety_stock": 450,
  "confidence": 0.94,
  "ai_summary": "Demand forecast analysis for SKU-001...",
  "recommended_inventory": [
    {
      "warehouse": "Chicago Central DC",
      "current_stock": 1200,
      "recommended_stock": 750,
      "action": "adequate",
      "gap": 0
    }
  ]
}
```

### GET /api/forecast/skus

List available SKUs for forecasting.

---

## Suppliers

### GET /api/suppliers

**Query params:** `risk_level` (optional): `high`, `medium`, `low`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Pacific Metals Corp",
    "country": "China",
    "category": "Raw Materials",
    "risk_score": 82,
    "risk_level": "high",
    "contract_expiry": "2025-08-15",
    "on_time_delivery_pct": 72,
    "quality_incidents": 5,
    "financial_health": "stressed",
    "delay_count": 8
  }
]
```

### GET /api/suppliers/{id}/analysis

**Response:**
```json
{
  "supplier": { "...": "..." },
  "risk_factors": ["Elevated risk score: 82"],
  "recommendations": ["Identify backup suppliers"],
  "ai_analysis": "Supplier risk assessment..."
}
```

---

## Copilot

### POST /api/copilot/chat

**Request:**
```json
{
  "message": "Which suppliers are delayed?",
  "history": [
    { "role": "user", "content": "Hello" },
    { "role": "assistant", "content": "Hi!" }
  ]
}
```

**Response:**
```json
{
  "reply": "Currently tracking 5 delayed shipments...",
  "suggested_followups": ["Show high risk vendors.", "What inventory is low?"]
}
```

---

## Logistics

### GET /api/logistics/shipments

**Query params:** `status` (optional)

### GET /api/logistics/warehouses

### GET /api/logistics/vehicles

### GET /api/logistics/alerts

**Alert response:**
```json
[
  {
    "id": "ship-delay-1",
    "severity": "high",
    "title": "Delayed Shipment: SHP-2025001",
    "description": "Pacific Metals Corp shipment to Chicago DC is delayed.",
    "timestamp": "2025-04-18T12:00:00"
  }
]
```

---

## Documents

### POST /api/documents/upload

**Form fields:**
- `file` — PDF, PNG, JPG, or TXT
- `doc_type` — `invoice`, `po`, or `contract`

**Response:**
```json
{
  "document_id": 1,
  "filename": "invoice.txt",
  "doc_type": "invoice"
}
```

### POST /api/documents/extract

**Request:**
```json
{
  "document_id": 1,
  "filename": "invoice_acme_2025_001.txt"
}
```

**Response:**
```json
{
  "document_id": null,
  "filename": "invoice_acme_2025_001.txt",
  "doc_type": "invoice",
  "fields": [
    { "field": "vendor", "value": "Pacific Metals Corp", "confidence": 0.92 }
  ],
  "line_items": [
    { "line": 1, "description": "Steel Plate C (SKU-003)", "quantity": 500, "unit_price": 45.0, "total": 22500.0 }
  ],
  "ai_summary": "Document analysis complete..."
}
```

### GET /api/documents/samples

List sample invoice files from `data/invoices/`.

---

## Reports

### POST /api/reports/executive

Generate full executive summary.

**Response:**
```json
{
  "business_summary": "Operyx supply chain overview...",
  "risks": ["Pacific Metals Corp: Risk score 82"],
  "recommendations": ["Initiate backup sourcing plan"],
  "predicted_issues": ["Shipment SHP-2025001 may miss SLA"],
  "next_actions": ["Escalate SHP-2025001 with FedEx Freight"],
  "generated_at": "2025-04-18T12:00:00.000000"
}
```

---

## Error Responses

```json
{
  "detail": "Supplier 99 not found"
}
```

HTTP status codes: 400 (bad request), 404 (not found), 422 (validation error), 500 (server error).
