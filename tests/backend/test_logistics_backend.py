import pytest
from app.services.logistics_service import LogisticsService

@pytest.mark.asyncio
async def test_list_shipments_all(backend_client):
    response = await backend_client.get("/api/logistics/shipments")
    assert response.status_code == 200
    shipments = response.json()
    assert isinstance(shipments, list)
    assert len(shipments) > 0

@pytest.mark.asyncio
async def test_list_shipments_filtered(backend_client):
    response = await backend_client.get("/api/logistics/shipments?status=delayed")
    assert response.status_code == 200
    shipments = response.json()
    assert isinstance(shipments, list)
    for s in shipments:
        assert s["status"] == "delayed"

@pytest.mark.asyncio
async def test_list_warehouses(backend_client):
    response = await backend_client.get("/api/logistics/warehouses")
    assert response.status_code == 200
    warehouses = response.json()
    assert isinstance(warehouses, list)
    assert len(warehouses) > 0

@pytest.mark.asyncio
async def test_list_vehicles(backend_client):
    response = await backend_client.get("/api/logistics/vehicles")
    assert response.status_code == 200
    vehicles = response.json()
    assert isinstance(vehicles, list)
    assert len(vehicles) > 0

@pytest.mark.asyncio
async def test_get_logistics_alerts(backend_client):
    response = await backend_client.get("/api/logistics/alerts")
    assert response.status_code == 200
    alerts = response.json()
    assert isinstance(alerts, list)

def test_logistics_service_unit(db_session):
    service = LogisticsService(db_session)
    shipments = service.list_shipments()
    assert len(shipments) > 0
    warehouses = service.list_warehouses()
    assert len(warehouses) > 0
    vehicles = service.list_vehicles()
    assert len(vehicles) > 0
