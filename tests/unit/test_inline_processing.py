from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.adapters.storage.local_storage import LocalStorageAdapter
from src.api.routes.calls import _process_calls_inline
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.infrastructure.audio.ffmpeg_preprocessor import AudioMetadata
from src.infrastructure.config.settings import Settings
from src.infrastructure.di.container import ProviderFactory
from src.infrastructure.persistence.repositories import (
    SqlAlchemyCallRecordingRepository,
    SqlAlchemyTranscriptRepository,
)


@pytest.mark.asyncio
async def test_process_calls_inline_uses_request_session(test_session, tmp_path):
    """Ingested rows must be visible to inline STT without a separate DB session."""
    upload_dir = tmp_path / "uploads"
    storage = LocalStorageAdapter(upload_dir)
    call_id = uuid.uuid4()
    storage_key = f"default/{call_id}/recording.wav"
    await storage.upload(storage_key, b"fake wav content")

    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    await call_repo.create(
        CallRecording(
            id=call_id,
            tenant_id="default",
            storage_key=storage_key,
            status=CallStatus.PENDING,
        )
    )

    settings = Settings(tenant_id="default", storage_local_path=str(upload_dir))
    mock_preprocessor = MagicMock()
    mock_preprocessor.normalize.return_value = AudioMetadata(
        duration_sec=30.0, sample_rate=16000, channels=1
    )

    def factory_from_config(_settings=None):
        factory = ProviderFactory(_settings or settings)
        factory.create_storage = lambda: storage  # type: ignore[method-assign]
        factory.create_audio_preprocessor = lambda: mock_preprocessor  # type: ignore[method-assign]
        return factory

    with (
        patch(
            "src.application.use_cases.process_call.ProviderFactory.from_config",
            side_effect=factory_from_config,
        ),
        patch("src.api.routes.calls.get_settings", return_value=settings),
    ):
        await _process_calls_inline(test_session, [call_id])

    transcript_repo = SqlAlchemyTranscriptRepository(test_session)
    updated = await call_repo.get_by_id(call_id)
    transcript = await transcript_repo.get_by_call_id(call_id)

    assert updated is not None
    assert updated.status == CallStatus.COMPLETED
    assert transcript is not None
    assert transcript.stt_provider == "mock"
