import pytest
from app.services.dashboard_service import DashboardService
from app.models import Supplier, Warehouse, Order, SalesHistory

@pytest.mark.asyncio
async def test_dashboard_kpis_endpoint(backend_client):
    response = await backend_client.get("/api/dashboard/kpis")
    assert response.status_code == 200
    data = response.json()
    assert "total_orders" in data
    assert "inventory_value" in data
    assert "avg_supplier_risk" in data
    assert "warehouse_utilization" in data

@pytest.mark.asyncio
async def test_dashboard_charts_endpoint(backend_client):
    response = await backend_client.get("/api/dashboard/charts")
    assert response.status_code == 200
    data = response.json()
    assert "inventory_forecast" in data
    assert "warehouse_utilization" in data
    assert "transportation_status" in data

@pytest.mark.asyncio
async def test_dashboard_insights_endpoint(backend_client):
    response = await backend_client.get("/api/dashboard/insights")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

def test_dashboard_service_unit(db_session):
    service = DashboardService(db_session)
    kpis = service.get_kpis()
    assert "total_orders" in kpis
    charts = service.get_charts()
    assert "warehouse_utilization" in charts
