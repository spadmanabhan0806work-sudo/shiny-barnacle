import pytest

@pytest.mark.asyncio
async def test_executive_report_generation(backend_client):
    response = await backend_client.post("/api/reports/executive")
    assert response.status_code == 200
    data = response.json()
    assert "business_summary" in data
    assert "risks" in data
    assert "recommendations" in data
    assert isinstance(data["risks"], list)
    assert isinstance(data["recommendations"], list)
