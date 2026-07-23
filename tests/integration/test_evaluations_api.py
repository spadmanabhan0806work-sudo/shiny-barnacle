from __future__ import annotations

import uuid

import pytest

from src.domain.entities.annotation import Annotation, AnnotationStatus, GroundTruth
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.domain.entities.intent_extraction import IntentExtraction
from src.infrastructure.persistence.repositories import (
    SqlAlchemyAnnotationRepository,
    SqlAlchemyCallRecordingRepository,
    SqlAlchemyIntentExtractionRepository,
)


@pytest.mark.asyncio
async def test_create_evaluation_from_dataset(client):
    response = await client.post(
        "/api/v1/evaluations",
        json={
            "dataset_path": "eval/datasets/sample_gold.json",
            "use_db_annotations": False,
            "prompt_version": "v1.0.0",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["prompt_version"] == "v1.0.0"
    assert data["aggregate_metrics"]["summary"]["total"] == 4
    assert "fields" in data["aggregate_metrics"]
    assert data["report_path"].endswith(".html")

    eval_id = data["id"]
    get_response = await client.get(f"/api/v1/evaluations/{eval_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == eval_id


@pytest.mark.asyncio
async def test_list_evaluations(client):
    await client.post(
        "/api/v1/evaluations",
        json={
            "dataset_path": "eval/datasets/sample_gold.json",
            "use_db_annotations": False,
        },
    )
    response = await client.get("/api/v1/evaluations")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["evaluations"]) >= 1


@pytest.mark.asyncio
async def test_evaluation_from_db_annotations(client, test_session):
    call_id = uuid.uuid4()
    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    annotation_repo = SqlAlchemyAnnotationRepository(test_session)
    intent_repo = SqlAlchemyIntentExtractionRepository(test_session)

    await call_repo.create(
        CallRecording(
            id=call_id,
            tenant_id="default",
            storage_key="test/key.wav",
            status=CallStatus.COMPLETED,
        )
    )
    await annotation_repo.create(
        Annotation(
            call_id=call_id,
            annotator_id="tester",
            ground_truth=GroundTruth(
                side="BUY",
                stock_symbol="RELIANCE",
                quantity=100,
                price=2500.0,
                exchange="NSE",
            ),
            status=AnnotationStatus.SUBMITTED,
        )
    )
    await intent_repo.create(
        IntentExtraction(
            call_id=call_id,
            side="BUY",
            stock_symbol="RELIANCE",
            quantity=100,
            price=2500.0,
            exchange="NSE",
            confidence=0.95,
            prompt_version="v1.0.0",
            llm_provider="mock",
        )
    )
    await test_session.commit()

    response = await client.post(
        "/api/v1/evaluations",
        json={"use_db_annotations": True},
    )
    assert response.status_code == 201
    metrics = response.json()["aggregate_metrics"]
    assert metrics["summary"]["total"] == 1
    assert metrics["summary"]["matched_all_fields"] == 1
