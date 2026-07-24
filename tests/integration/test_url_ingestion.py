from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import httpx
import pytest
from httpx import AsyncClient

from src.infrastructure.audio.audio_downloader import (
    AudioDownloader,
    AudioDownloadError,
    DownloadedAudio,
)


class TestAudioDownloader:
    def test_extension_from_magic_wav(self):
        assert AudioDownloader._extension_from_magic(b"RIFF....WAVE") == "wav"

    def test_extension_from_magic_mp3(self):
        assert AudioDownloader._extension_from_magic(b"ID3\x03") == "mp3"

    def test_resolve_filename_from_callid_query(self):
        downloader = AudioDownloader()
        filename = downloader._resolve_filename(
            "https://example.com/vr/fetchsound/?callid=abc-123",
            httpx.Headers({}),
            "audio/mpeg",
            b"ID3" + b"\x00" * 10,
        )
        assert filename == "abc-123.mp3"


@pytest.mark.asyncio
async def test_ingest_call_from_url(client: AsyncClient):
    wav_bytes = b"RIFF" + b"\x00" * 40
    downloaded = DownloadedAudio(
        url="https://example.com/audio?callid=test-call",
        data=wav_bytes,
        filename="test-call.wav",
        content_type="audio/wav",
    )

    mock_downloader = AsyncMock(spec=AudioDownloader)
    mock_downloader.download = AsyncMock(return_value=downloaded)

    with (
        patch("src.api.routes.calls.IngestCallFromUrlUseCase") as mock_use_case_cls,
        patch("src.api.routes.calls._response_after_processing", new_callable=AsyncMock) as mock_response,
    ):
        recording = MagicMock()
        recording.id = UUID("11111111-1111-1111-1111-111111111111")
        recording.tenant_id = "default"
        recording.storage_key = "default/111/test-call.wav"
        recording.status.value = "completed"
        recording.detected_language = "en"
        recording.duration_sec = 12.0

        instance = mock_use_case_cls.return_value
        result = MagicMock()
        result.recording = recording
        instance.execute = AsyncMock(return_value=result)

        from src.api.routes.calls import CallResponse

        mock_response.return_value = CallResponse(
            id=recording.id,
            tenant_id="default",
            storage_key=recording.storage_key,
            status="completed",
            detected_language="en",
            duration_sec=12.0,
        )

        response = await client.post(
            "/api/v1/calls/from-url",
            json={"url": "https://example.com/audio?callid=test-call"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "11111111-1111-1111-1111-111111111111"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_batch_ingest_from_urls(client: AsyncClient):
    with patch(
        "src.api.routes.calls.BatchIngestFromUrlsUseCase"
    ) as mock_use_case_cls:
        batch_id = UUID("22222222-2222-2222-2222-222222222222")
        call_ids = [
            UUID("33333333-3333-3333-3333-333333333333"),
            UUID("44444444-4444-4444-4444-444444444444"),
        ]
        result = MagicMock()
        result.batch_id = batch_id
        result.call_ids = call_ids
        result.errors = ["https://bad.example/x: HTTP 404"]

        instance = mock_use_case_cls.return_value
        instance.execute = AsyncMock(return_value=result)

        response = await client.post(
            "/api/v1/calls/batch/from-urls",
            json={
                "urls": [
                    "https://example.com/a?callid=1",
                    "https://example.com/b?callid=2",
                ]
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["batch_id"] == str(batch_id)
    assert data["total"] == 2
    assert len(data["errors"]) == 1


@pytest.mark.asyncio
async def test_ingest_from_url_use_case_download_failure(test_session, tmp_path):
    from src.adapters.storage.local_storage import LocalStorageAdapter
    from src.application.use_cases.ingest_from_url import IngestCallFromUrlUseCase
    from src.infrastructure.config.settings import Settings

    settings = Settings(
        tenant_id="default",
        storage_local_path=str(tmp_path),
    )
    storage = LocalStorageAdapter(tmp_path)

    mock_downloader = AsyncMock(spec=AudioDownloader)
    mock_downloader.download = AsyncMock(
        side_effect=AudioDownloadError("Failed to download https://x: HTTP 500")
    )

    use_case = IngestCallFromUrlUseCase(
        test_session,
        storage,
        settings,
        downloader=mock_downloader,
    )

    with pytest.raises(ValueError, match="Failed to download"):
        await use_case.execute("https://example.com/missing")


@pytest.mark.asyncio
async def test_batch_ingest_from_urls_use_case(test_session, tmp_path):
    from src.adapters.storage.local_storage import LocalStorageAdapter
    from src.application.use_cases.ingest_from_url import BatchIngestFromUrlsUseCase
    from src.infrastructure.config.settings import Settings

    settings = Settings(tenant_id="default", storage_local_path=str(tmp_path))
    storage = LocalStorageAdapter(tmp_path)
    wav_bytes = b"RIFF" + b"\x00" * 40

    mock_downloader = AsyncMock(spec=AudioDownloader)
    mock_downloader.download = AsyncMock(
        side_effect=[
            DownloadedAudio(
                url="https://example.com/a?callid=1",
                data=wav_bytes,
                filename="1.wav",
                content_type="audio/wav",
            ),
            DownloadedAudio(
                url="https://example.com/b?callid=2",
                data=wav_bytes,
                filename="2.wav",
                content_type="audio/wav",
            ),
        ]
    )

    use_case = BatchIngestFromUrlsUseCase(
        test_session,
        storage,
        settings,
        downloader=mock_downloader,
    )
    result = await use_case.execute(
        [
            "https://example.com/a?callid=1",
            "https://example.com/b?callid=2",
        ]
    )

    assert len(result.call_ids) == 2
    assert result.batch_id is not None
    assert result.errors == []


@pytest.mark.asyncio
async def test_language_analysis_distribution(test_session):
    import uuid

    from src.application.use_cases.language_analysis import LanguageAnalysisUseCase
    from src.domain.entities.call_recording import CallRecording, CallStatus
    from src.domain.entities.transcript import Transcript, TranscriptSegment
    from src.infrastructure.persistence.models import BatchUploadModel
    from src.infrastructure.persistence.repositories import (
        SqlAlchemyCallRecordingRepository,
        SqlAlchemyTranscriptRepository,
    )

    call_id = uuid.uuid4()
    batch_id = uuid.uuid4()

    batch = BatchUploadModel(
        id=batch_id,
        tenant_id="default",
        call_ids=[str(call_id)],
    )
    test_session.add(batch)

    call_repo = SqlAlchemyCallRecordingRepository(test_session)
    transcript_repo = SqlAlchemyTranscriptRepository(test_session)

    recording = CallRecording(
        id=call_id,
        tenant_id="default",
        storage_key="default/x/test.wav",
        status=CallStatus.COMPLETED,
        detected_language="hi",
    )
    await call_repo.create(recording)
    await transcript_repo.create(
        Transcript(
            call_id=call_id,
            full_text="मुझे शेयर खरीदने हैं",
            segments=[
                TranscriptSegment(start=0.0, end=1.0, text="मुझे", confidence=0.9),
            ],
            stt_provider="mock",
            stt_model="mock-v1",
        )
    )
    await test_session.flush()

    use_case = LanguageAnalysisUseCase(test_session)
    report = await use_case.execute(batch_id=batch_id)

    assert report.processed_calls == 1
    assert report.distribution["hi"] == 1
    assert report.needs_review == []
