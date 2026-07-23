import json
import uuid

import pytest
from sqlalchemy import select

from src.infrastructure.persistence.models import AuditLogModel, BatchUploadModel


@pytest.mark.asyncio
async def test_batch_upload(client):
    audio_data = b"RIFF" + b"\x00" * 40
    response = await client.post(
        "/api/v1/calls/batch",
        files=[
            ("files", ("a.wav", audio_data, "audio/wav")),
            ("files", ("b.wav", audio_data, "audio/wav")),
        ],
    )
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 2
    assert len(data["call_ids"]) == 2
    uuid.UUID(data["batch_id"])


@pytest.mark.asyncio
async def test_batch_upload_empty_rejected(client):
    response = await client.post("/api/v1/calls/batch", files=[])
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_batch_upload_max_limit(client):
    audio_data = b"RIFF" + b"\x00" * 40
    files = [("files", (f"f{i}.wav", audio_data, "audio/wav")) for i in range(101)]
    response = await client.post("/api/v1/calls/batch", files=files)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_export_json(client, test_session):
    batch_id = uuid.uuid4()
    call_id = uuid.uuid4()
    batch = BatchUploadModel(
        id=batch_id,
        tenant_id="default",
        call_ids=[str(call_id)],
    )
    test_session.add(batch)
    await test_session.flush()

    response = await client.get(f"/api/v1/exports/{batch_id}?format=json")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    payload = json.loads(response.content)
    assert payload["batch_id"] == str(batch_id)


@pytest.mark.asyncio
async def test_export_xlsx(client, test_session):
    batch_id = uuid.uuid4()
    batch = BatchUploadModel(
        id=batch_id,
        tenant_id="default",
        call_ids=[],
    )
    test_session.add(batch)
    await test_session.flush()

    response = await client.get(f"/api/v1/exports/{batch_id}?format=xlsx")
    assert response.status_code == 200
    assert "spreadsheetml" in response.headers["content-type"]
    assert len(response.content) > 100


@pytest.mark.asyncio
async def test_export_not_found(client):
    response = await client.get(f"/api/v1/exports/{uuid.uuid4()}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_audit_log(client, test_session, call_id):
    from src.infrastructure.persistence.models import IntentExtractionModel, ReviewQueueItemModel

    extraction = IntentExtractionModel(
        call_id=call_id,
        side="BUY",
        stock_symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        exchange="NSE",
        confidence=0.5,
        prompt_version="v1.0.0",
        llm_provider="mock",
    )
    test_session.add(extraction)
    await test_session.flush()

    review = ReviewQueueItemModel(extraction_id=extraction.id, status="pending")
    test_session.add(review)
    await test_session.flush()

    response = await client.patch(
        f"/api/v1/reviews/{review.id}",
        json={"action": "approve", "reviewer_id": "test-reviewer"},
    )
    assert response.status_code == 200

    result = await test_session.execute(select(AuditLogModel))
    logs = result.scalars().all()
    assert any(log.action == "approve" for log in logs)
