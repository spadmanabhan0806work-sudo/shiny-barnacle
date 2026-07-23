import uuid

import pytest


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_upload_call(client):
    audio_data = b"RIFF" + b"\x00" * 40
    response = await client.post(
        "/api/v1/calls",
        files={"file": ("recording.wav", audio_data, "audio/wav")},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["tenant_id"] == "default"
    uuid.UUID(data["id"])


@pytest.mark.asyncio
async def test_upload_unsupported_format(client):
    response = await client.post(
        "/api/v1/calls",
        files={"file": ("recording.flac", b"data", "audio/flac")},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_and_get_annotation(client, call_id):
    payload = {
        "call_id": str(call_id),
        "annotator_id": "annotator-1",
        "ground_truth": {
            "side": "BUY",
            "stock_symbol": "RELIANCE",
            "quantity": 100,
            "price": 2500.50,
            "exchange": "NSE",
        },
    }
    create_response = await client.post("/api/v1/annotations", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["call_id"] == str(call_id)
    assert created["ground_truth"]["side"] == "BUY"
    assert created["status"] == "submitted"

    get_response = await client.get(f"/api/v1/annotations/{call_id}")
    assert get_response.status_code == 200
    fetched = get_response.json()
    assert fetched["id"] == created["id"]
    assert fetched["ground_truth"]["stock_symbol"] == "RELIANCE"


@pytest.mark.asyncio
async def test_get_annotation_not_found(client):
    random_id = uuid.uuid4()
    response = await client.get(f"/api/v1/annotations/{random_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_annotation_call_not_found(client):
    payload = {
        "call_id": str(uuid.uuid4()),
        "annotator_id": "annotator-1",
        "ground_truth": {
            "side": "SELL",
            "stock_symbol": "TCS",
            "quantity": 50,
            "price": 3500.0,
            "exchange": "NSE",
        },
    }
    response = await client.post("/api/v1/annotations", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_calls(client, call_id):
    response = await client.get("/api/v1/calls")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert any(c["id"] == str(call_id) for c in data["calls"])
