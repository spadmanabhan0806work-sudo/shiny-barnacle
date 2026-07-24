from __future__ import annotations

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.adapters.storage.local_storage import LocalStorageAdapter
from src.adapters.stt.mock_stt_adapter import MockSTTAdapter
from src.application.orchestrators.call_processing_orchestrator import CallProcessingOrchestrator
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.infrastructure.audio.ffmpeg_preprocessor import AudioMetadata
from src.infrastructure.persistence.repositories import (
    SqlAlchemyCallRecordingRepository,
    SqlAlchemyIntentExtractionRepository,
    SqlAlchemyReviewQueueRepository,
    SqlAlchemyTranscriptRepository,
)


def _build_orchestrator(
    call_repo,
    transcript_repo,
    storage,
    stt,
    preprocessor,
    tmp_path,
    *,
    intent_repo=None,
    review_repo=None,
):
    from src.adapters.llm.mock_llm_adapter import MockLLMAdapter
    from src.application.services.confidence_router import ConfidenceRouter
    from src.domain.services.intent_validator import IntentValidator
    from src.domain.services.numeric_parser import NumericParser
    from src.domain.services.stock_symbol_resolver import StockSymbolResolver
    from src.infrastructure.prompts.prompt_registry import PromptRegistry

    symbols_csv = tmp_path / "symbols.csv"
    if not symbols_csv.exists():
        symbols_csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\n")

    return CallProcessingOrchestrator(
        call_repo,
        transcript_repo,
        intent_repo or SqlAlchemyIntentExtractionRepository(call_repo._session),
        review_repo or SqlAlchemyReviewQueueRepository(call_repo._session),
        storage,
        stt,
        MockLLMAdapter(),
        PromptRegistry(Path("prompts"), Path("prompts/manifest.yaml")),
        IntentValidator(StockSymbolResolver(symbols_csv), NumericParser()),
        ConfidenceRouter(threshold=0.85),
        preprocessor,
    )


@pytest.mark.asyncio
async def test_process_call_flow_with_mock_stt(test_session, tmp_path):
    """End-to-end STT pipeline: download → FFmpeg → STT → persist transcript."""
    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/recording.wav"
    await storage.upload(storage_key, b"fake wav content")

    recording = CallRecording(
        id=call_id,
        tenant_id="default",
        storage_key=storage_key,
        status=CallStatus.PENDING,
    )
    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    await call_repo.create(recording)

    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=30.0, sample_rate=16000, channels=1
    )

    orchestrator = _build_orchestrator(
        call_repo,
        transcript_repo,
        storage,
        MockSTTAdapter(default_language="en"),
        mock_preprocessor,
        tmp_path,
    )

    transcript = await orchestrator.process_stt(call_id)

    updated = await call_repo.get_by_id(call_id)
    assert updated is not None
    assert updated.status == CallStatus.TRANSCRIBED
    assert updated.detected_language == "en"
    assert updated.duration_sec == 30.0

    assert transcript.full_text
    assert transcript.stt_provider == "mock"
    assert len(transcript.segments) >= 1

    saved = await transcript_repo.get_by_call_id(call_id)
    assert saved is not None
    assert saved.full_text == transcript.full_text


@pytest.mark.asyncio
async def test_process_call_marks_failed_on_error(test_session, tmp_path):
    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    recording = CallRecording(
        id=call_id,
        tenant_id="default",
        storage_key="missing/key.wav",
        status=CallStatus.PENDING,
    )
    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    await call_repo.create(recording)

    orchestrator = _build_orchestrator(
        call_repo,
        transcript_repo,
        storage,
        MockSTTAdapter(),
        MagicMock(),
        tmp_path,
    )

    with pytest.raises(FileNotFoundError):
        await orchestrator.process_stt(call_id)

    updated = await call_repo.get_by_id(call_id)
    assert updated is not None
    assert updated.status == CallStatus.FAILED


@pytest.mark.asyncio
async def test_full_process_call_with_mock_providers(test_session, tmp_path):
    """End-to-end pipeline: STT → LLM extract → validate → save intent."""
    from src.adapters.llm.mock_llm_adapter import MockLLMAdapter
    from src.adapters.storage.local_storage import LocalStorageAdapter
    from src.adapters.stt.mock_stt_adapter import MockSTTAdapter
    from src.application.services.confidence_router import ConfidenceRouter
    from src.domain.services.intent_validator import IntentValidator
    from src.domain.services.numeric_parser import NumericParser
    from src.domain.services.stock_symbol_resolver import StockSymbolResolver
    from src.infrastructure.persistence.repositories import (
        SqlAlchemyIntentExtractionRepository,
        SqlAlchemyReviewQueueRepository,
    )
    from src.infrastructure.prompts.prompt_registry import PromptRegistry

    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/recording.wav"
    await storage.upload(storage_key, b"fake wav content")

    recording = CallRecording(
        id=call_id,
        tenant_id="default",
        storage_key=storage_key,
        status=CallStatus.PENDING,
    )
    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    intent_repo = SqlAlchemyIntentExtractionRepository(test_session)
    review_repo = SqlAlchemyReviewQueueRepository(test_session)
    await call_repo.create(recording)

    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=30.0, sample_rate=16000, channels=1
    )

    symbols_csv = tmp_path / "symbols.csv"
    symbols_csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\n")

    orchestrator = CallProcessingOrchestrator(
        call_repo,
        transcript_repo,
        intent_repo,
        review_repo,
        storage,
        MockSTTAdapter(default_language="en"),
        MockLLMAdapter(),
        PromptRegistry(Path("prompts"), Path("prompts/manifest.yaml")),
        IntentValidator(StockSymbolResolver(symbols_csv), NumericParser()),
        ConfidenceRouter(threshold=0.85),
        mock_preprocessor,
    )

    transcript, extraction, review_item = await orchestrator.process_call(call_id)

    updated = await call_repo.get_by_id(call_id)
    assert updated is not None
    assert updated.status == CallStatus.COMPLETED
    assert transcript.full_text
    assert extraction.side == "BUY"
    assert extraction.stock_symbol == "RELIANCE"
    assert extraction.quantity == 100
    assert extraction.prompt_version == "v1.0.0"
    assert extraction.llm_provider == "mock"
    assert review_item is None

    saved = await intent_repo.get_by_call_id(call_id)
    assert saved is not None
    assert saved.stock_symbol == "RELIANCE"


@pytest.mark.asyncio
async def test_get_call_with_transcript(client, test_session, tmp_path):
    """API returns transcript when call has been processed."""
    from src.adapters.storage.local_storage import LocalStorageAdapter
    from src.domain.entities.call_recording import CallRecording, CallStatus
    from src.infrastructure.persistence.repositories import (
        SqlAlchemyCallRecordingRepository,
        SqlAlchemyTranscriptRepository,
    )

    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/test.wav"
    await storage.upload(storage_key, b"audio")

    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    await call_repo.create(
        CallRecording(
            id=call_id,
            tenant_id="default",
            storage_key=storage_key,
            status=CallStatus.PENDING,
        )
    )

    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=10.0, sample_rate=16000, channels=1
    )
    orchestrator = _build_orchestrator(
        call_repo,
        transcript_repo,
        storage,
        MockSTTAdapter(),
        mock_preprocessor,
        tmp_path,
    )
    await orchestrator.process_stt(call_id)
    await test_session.commit()

    response = await client.get(f"/api/v1/calls/{call_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "transcribed"
    assert data["detected_language"] == "en"
    assert data["transcript"] is not None
    assert "Reliance" in data["transcript"]["full_text"]


@pytest.mark.asyncio
async def test_get_call_with_intent_and_confidence(client, test_session, tmp_path):
    """API returns intent extraction with confidence after full pipeline."""
    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/test.wav"
    await storage.upload(storage_key, b"audio")

    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    await call_repo.create(
        CallRecording(
            id=call_id,
            tenant_id="default",
            storage_key=storage_key,
            status=CallStatus.PENDING,
        )
    )

    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=10.0, sample_rate=16000, channels=1
    )
    orchestrator = _build_orchestrator(
        call_repo,
        transcript_repo,
        storage,
        MockSTTAdapter(default_language="en"),
        mock_preprocessor,
        tmp_path,
    )
    await orchestrator.process_call(call_id)
    await test_session.commit()

    response = await client.get(f"/api/v1/calls/{call_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    assert data["intent_extraction"] is not None
    assert data["intent_extraction"]["side"] == "BUY"
    assert data["intent_extraction"]["stock_symbol"] == "RELIANCE"
    assert data["intent_extraction"]["confidence"] >= 0.85


@pytest.mark.asyncio
async def test_hitl_routing_creates_review_item(test_session, tmp_path):
    """Low-confidence extractions route to the review queue."""
    from src.adapters.llm.mock_llm_adapter import MockLLMAdapter
    from src.application.services.confidence_router import ConfidenceRouter
    from src.domain.services.intent_validator import IntentValidator
    from src.domain.services.numeric_parser import NumericParser
    from src.domain.services.stock_symbol_resolver import StockSymbolResolver
    from src.infrastructure.persistence.repositories import (
        SqlAlchemyIntentExtractionRepository,
        SqlAlchemyReviewQueueRepository,
    )
    from src.infrastructure.prompts.prompt_registry import PromptRegistry

    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/recording.wav"
    await storage.upload(storage_key, b"fake wav content")

    recording = CallRecording(
        id=call_id,
        tenant_id="default",
        storage_key=storage_key,
        status=CallStatus.PENDING,
    )
    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    intent_repo = SqlAlchemyIntentExtractionRepository(test_session)
    review_repo = SqlAlchemyReviewQueueRepository(test_session)
    await call_repo.create(recording)

    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=30.0, sample_rate=16000, channels=1
    )

    symbols_csv = tmp_path / "symbols.csv"
    symbols_csv.write_text("RELIANCE,RELIANCE INDUSTRIES,NSE\n")

    orchestrator = CallProcessingOrchestrator(
        call_repo,
        transcript_repo,
        intent_repo,
        review_repo,
        storage,
        MockSTTAdapter(default_language="en"),
        MockLLMAdapter(),
        PromptRegistry(Path("prompts"), Path("prompts/manifest.yaml")),
        IntentValidator(StockSymbolResolver(symbols_csv), NumericParser()),
        ConfidenceRouter(threshold=0.99),
        mock_preprocessor,
    )

    _, extraction, review_item = await orchestrator.process_call(call_id)

    updated = await call_repo.get_by_id(call_id)
    assert updated is not None
    assert updated.status == CallStatus.REVIEW_REQUIRED
    assert review_item is not None
    assert extraction.confidence < 0.99

    saved_review = await review_repo.get_by_extraction_id(extraction.id)
    assert saved_review is not None


@pytest.mark.asyncio
async def test_reprocess_call_endpoint(client, test_session, tmp_path):
    """POST /calls/{id}/reprocess triggers pipeline and returns updated call."""
    storage = LocalStorageAdapter(tmp_path / "uploads")
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/test.wav"
    await storage.upload(storage_key, b"audio")

    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    await call_repo.create(
        CallRecording(
            id=call_id,
            tenant_id="default",
            storage_key=storage_key,
            status=CallStatus.COMPLETED,
        )
    )
    await test_session.commit()

    with patch("src.api.routes.calls._process_calls_inline", new_callable=AsyncMock) as mock_proc:
        response = await client.post(
            f"/api/v1/calls/{call_id}/reprocess",
            json={"prompt_version": "v1.0.0"},
        )

    assert response.status_code == 200
    mock_proc.assert_called_once()
    args = mock_proc.call_args
    assert args[0][1] == [call_id]
    assert args[1]["prompt_version"] == "v1.0.0"


@pytest.mark.asyncio
async def test_ready_endpoint(client):
    from contextlib import asynccontextmanager
    from unittest.mock import AsyncMock, MagicMock

    mock_session = MagicMock()
    mock_session.execute = AsyncMock(return_value=None)

    @asynccontextmanager
    async def session_cm():
        yield mock_session

    def fake_session_factory():
        return session_cm()

    with patch("src.api.routes.health.get_session_factory", return_value=fake_session_factory):
        response = await client.get("/api/v1/ready")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"
