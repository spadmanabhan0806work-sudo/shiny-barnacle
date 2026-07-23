from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_analytics_empty(client):
    response = await client.get("/api/v1/analytics")
    assert response.status_code == 200
    data = response.json()
    assert "volume" in data
    assert "confidence_distribution" in data
    assert "language_breakdown" in data
    assert data["volume"]["total_calls"] >= 0


@pytest.mark.asyncio
async def test_analytics_after_upload(client):
    await client.get("/api/v1/analytics")
    audio_data = b"RIFF" + b"\x00" * 40
    await client.post(
        "/api/v1/calls",
        files={"file": ("test.wav", audio_data, "audio/wav")},
    )
    response = await client.get("/api/v1/analytics")
    assert response.status_code == 200
    assert response.json()["volume"]["total_calls"] >= 1
