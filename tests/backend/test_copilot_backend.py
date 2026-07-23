import pytest

@pytest.mark.asyncio
async def test_copilot_chat(backend_client):
    payload = {
        "message": "Which suppliers are currently at high risk?",
        "history": []
    }
    response = await backend_client.post("/api/copilot/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "suggested_followups" in data
    assert len(data["suggested_followups"]) <= 3
