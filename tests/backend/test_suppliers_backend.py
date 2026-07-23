import pytest
from app.services.supplier_service import SupplierService

@pytest.mark.asyncio
async def test_list_suppliers_all(backend_client):
    response = await backend_client.get("/api/suppliers")
    assert response.status_code == 200
    suppliers = response.json()
    assert isinstance(suppliers, list)
    assert len(suppliers) > 0

@pytest.mark.asyncio
async def test_list_suppliers_filter_by_risk(backend_client):
    response = await backend_client.get("/api/suppliers?risk_level=high")
    assert response.status_code == 200
    suppliers = response.json()
    assert isinstance(suppliers, list)
    for s in suppliers:
        assert s["risk_level"] == "high"

@pytest.mark.asyncio
async def test_analyze_supplier_endpoint(backend_client):
    response = await backend_client.get("/api/suppliers/1/analysis")
    assert response.status_code == 200
    data = response.json()
    assert "supplier" in data
    assert "risk_factors" in data
    assert "recommendations" in data

def test_supplier_service_unit(db_session):
    service = SupplierService(db_session)
    suppliers = service.list_suppliers(risk_level=None)
    assert len(suppliers) > 0
