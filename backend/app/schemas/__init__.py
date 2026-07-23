from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class KPIResponse(BaseModel):
    total_orders: int
    inventory_value: float
    delayed_shipments: int
    avg_supplier_risk: float
    warehouse_utilization: float
    transportation_active: int
    transportation_delayed: int


class ChartSeries(BaseModel):
    label: str
    data: list[dict[str, Any]]


class DashboardChartsResponse(BaseModel):
    inventory_forecast: list[dict[str, Any]]
    warehouse_utilization: list[dict[str, Any]]
    transportation_status: list[dict[str, Any]]


class InsightItem(BaseModel):
    title: str
    description: str
    severity: str
    category: str


class ForecastRequest(BaseModel):
    sku: str | None = None
    horizon_months: int = 6


class ForecastPoint(BaseModel):
    period: str
    actual: float | None = None
    forecast: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    sku: str
    product_name: str
    forecast: list[ForecastPoint]
    safety_stock: int
    confidence: float
    ai_summary: str
    recommended_inventory: list[dict[str, Any]]


class SupplierResponse(BaseModel):
    id: int
    name: str
    country: str
    category: str
    risk_score: float
    risk_level: str
    contract_expiry: date | None
    on_time_delivery_pct: float
    quality_incidents: int
    financial_health: str
    delay_count: int

    model_config = {"from_attributes": True}


class SupplierAnalysisResponse(BaseModel):
    supplier: SupplierResponse
    risk_factors: list[str]
    recommendations: list[str]
    ai_analysis: str


class ChatMessage(BaseModel):
    role: str
    content: str


class CopilotRequest(BaseModel):
    message: str
    history: list[ChatMessage] = Field(default_factory=list)


class CopilotResponse(BaseModel):
    reply: str
    suggested_followups: list[str] = Field(default_factory=list)


class ShipmentResponse(BaseModel):
    id: int
    tracking_number: str
    supplier_name: str
    origin: str
    destination: str
    status: str
    eta: date | None
    carrier: str
    risk_flag: str

    model_config = {"from_attributes": True}


class WarehouseResponse(BaseModel):
    id: int
    name: str
    location: str
    capacity_units: int
    used_units: int
    utilization_pct: float
    manager: str

    model_config = {"from_attributes": True}


class VehicleResponse(BaseModel):
    id: int
    vehicle_id: str
    type: str
    status: str
    location: str
    driver: str
    capacity_tons: float
    current_load_tons: float

    model_config = {"from_attributes": True}


class LogisticsAlert(BaseModel):
    id: str
    severity: str
    title: str
    description: str
    timestamp: str


class DocumentExtractRequest(BaseModel):
    document_id: int | None = None
    filename: str | None = None


class ExtractedField(BaseModel):
    field: str
    value: str
    confidence: float


class DocumentExtractResponse(BaseModel):
    document_id: int | None
    filename: str
    doc_type: str
    fields: list[ExtractedField]
    line_items: list[dict[str, Any]]
    ai_summary: str


class ExecutiveReportResponse(BaseModel):
    business_summary: str
    risks: list[str]
    recommendations: list[str]
    predicted_issues: list[str]
    next_actions: list[str]
    generated_at: str
