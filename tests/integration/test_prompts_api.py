from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_list_prompts(client):
    response = await client.get("/api/v1/prompts")
    assert response.status_code == 200
    data = response.json()
    assert data["active_version"] == "v1.0.0"
    versions = {p["version"] for p in data["prompts"]}
    assert "v1.0.0" in versions
    assert "v1.1.0" in versions


@pytest.mark.asyncio
async def test_set_active_prompt(client):
    response = await client.patch(
        "/api/v1/prompts/active",
        json={"active_version": "v1.1.0"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["active_version"] == "v1.1.0"
    active = [p for p in data["prompts"] if p["is_active"]]
    assert len(active) == 1
    assert active[0]["version"] == "v1.1.0"

    # Restore default for other tests
    await client.patch(
        "/api/v1/prompts/active",
        json={"active_version": "v1.0.0"},
    )


@pytest.mark.asyncio
async def test_update_ab_weights(client):
    response = await client.patch(
        "/api/v1/prompts/active",
        json={"weights": [{"version": "v1.1.0", "ab_weight": 0.5}]},
    )
    assert response.status_code == 200
    v11 = next(p for p in response.json()["prompts"] if p["version"] == "v1.1.0")
    assert v11["ab_weight"] == 0.5
