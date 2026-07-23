from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(100), default="")
    category: Mapped[str] = mapped_column(String(100), default="")
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(20), default="low")
    contract_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    on_time_delivery_pct: Mapped[float] = mapped_column(Float, default=100.0)
    quality_incidents: Mapped[int] = mapped_column(Integer, default=0)
    financial_health: Mapped[str] = mapped_column(String(50), default="stable")
    delay_count: Mapped[int] = mapped_column(Integer, default=0)
    contact_email: Mapped[str] = mapped_column(String(200), default="")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    po_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    supplier_id: Mapped[int] = mapped_column(Integer, index=True)
    supplier_name: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="pending")
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    order_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expected_delivery: Mapped[date | None] = mapped_column(Date, nullable=True)
    items_count: Mapped[int] = mapped_column(Integer, default=0)


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), index=True)
    product_name: Mapped[str] = mapped_column(String(200))
    warehouse_id: Mapped[int] = mapped_column(Integer, index=True)
    warehouse_name: Mapped[str] = mapped_column(String(100))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_value: Mapped[float] = mapped_column(Float, default=0.0)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(100), default="")


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(200))
    capacity_units: Mapped[int] = mapped_column(Integer, default=0)
    used_units: Mapped[int] = mapped_column(Integer, default=0)
    utilization_pct: Mapped[float] = mapped_column(Float, default=0.0)
    manager: Mapped[str] = mapped_column(String(100), default="")


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tracking_number: Mapped[str] = mapped_column(String(50), unique=True)
    order_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(200), default="")
    origin: Mapped[str] = mapped_column(String(200))
    destination: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default="in_transit")
    eta: Mapped[date | None] = mapped_column(Date, nullable=True)
    carrier: Mapped[str] = mapped_column(String(100), default="")
    risk_flag: Mapped[str] = mapped_column(String(20), default="none")


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    vehicle_id: Mapped[str] = mapped_column(String(50), unique=True)
    type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(50), default="available")
    location: Mapped[str] = mapped_column(String(200), default="")
    driver: Mapped[str] = mapped_column(String(100), default="")
    capacity_tons: Mapped[float] = mapped_column(Float, default=0.0)
    current_load_tons: Mapped[float] = mapped_column(Float, default=0.0)


class SalesHistory(Base):
    __tablename__ = "sales_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), index=True)
    product_name: Mapped[str] = mapped_column(String(200))
    month: Mapped[str] = mapped_column(String(10), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    units_sold: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255))
    doc_type: Mapped[str] = mapped_column(String(50), default="invoice")
    file_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
