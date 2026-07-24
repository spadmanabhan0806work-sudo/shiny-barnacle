import pytest


@pytest.mark.asyncio
async def test_list_skus(backend_client):
    response = await backend_client.get("/api/forecast/skus")
    assert response.status_code == 200
    skus = response.json()
    assert isinstance(skus, list)
    assert len(skus) > 0

@pytest.mark.asyncio
async def test_generate_forecast(backend_client):
    payload = {"horizon_months": 3}
    response = await backend_client.post("/api/forecast/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sku" in data
    assert len(data["forecast"]) > 0

@pytest.mark.asyncio
async def test_upload_sales_csv(backend_client):
    csv_content = "sku,product_name,month,year,units_sold,revenue\nSKU-TEST,Test Product,Jan,2026,100,5000\n"
    files = {"file": ("test.csv", csv_content.encode("utf-8"), "text/csv")}
    response = await backend_client.post("/api/forecast/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "rows_imported" in data
    assert data["rows_imported"] == 1
