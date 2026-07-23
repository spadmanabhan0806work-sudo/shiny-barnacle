from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases import UploadCallUseCase
from src.domain.entities.call_recording import CallRecording
from src.infrastructure.audio.audio_downloader import AudioDownloader, AudioDownloadError
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.repositories import (
    SqlAlchemyBatchUploadRepository,
    SqlAlchemyCallRecordingRepository,
)
from src.ports.storage_provider import StorageProvider


@dataclass
class UrlIngestResult:
    recording: CallRecording
    source_url: str


@dataclass
class BatchUrlIngestResult:
    batch_id: uuid.UUID
    call_ids: list[uuid.UUID] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    source_urls: dict[str, str] = field(default_factory=dict)


class IngestCallFromUrlUseCase:
    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        settings: Settings,
        downloader: AudioDownloader | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._downloader = downloader or AudioDownloader()
        self._upload = UploadCallUseCase(
            SqlAlchemyCallRecordingRepository(session),
            storage,
            settings,
        )

    async def execute(self, url: str) -> UrlIngestResult:
        url = url.strip()
        if not url:
            raise ValueError("URL is required")

        try:
            downloaded = await self._downloader.download(url)
        except AudioDownloadError as exc:
            raise ValueError(str(exc)) from exc

        recording = await self._upload.execute(
            filename=downloaded.filename,
            data=downloaded.data,
            content_type=downloaded.content_type,
        )
        return UrlIngestResult(recording=recording, source_url=url)


class BatchIngestFromUrlsUseCase:
    MAX_URLS = 100

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        settings: Settings,
        downloader: AudioDownloader | None = None,
    ) -> None:
        self._session = session
        self._settings = settings
        self._ingest = IngestCallFromUrlUseCase(session, storage, settings, downloader)

    async def execute(self, urls: list[str]) -> BatchUrlIngestResult:
        cleaned = [u.strip() for u in urls if u.strip()]
        if not cleaned:
            raise ValueError("At least one URL is required")
        if len(cleaned) > self.MAX_URLS:
            raise ValueError(f"Maximum {self.MAX_URLS} URLs per batch")

        call_ids: list[uuid.UUID] = []
        errors: list[str] = []
        source_urls: dict[str, str] = {}

        for url in cleaned:
            try:
                result = await self._ingest.execute(url)
                call_ids.append(result.recording.id)
                source_urls[str(result.recording.id)] = result.source_url
            except ValueError as exc:
                errors.append(f"{url}: {exc}")

        if not call_ids:
            raise ValueError("No URLs were ingested successfully")

        batch_repo = SqlAlchemyBatchUploadRepository(self._session)
        batch = await batch_repo.create(
            tenant_id=self._settings.tenant_id,
            call_ids=call_ids,
        )

        return BatchUrlIngestResult(
            batch_id=batch.id,
            call_ids=call_ids,
            errors=errors,
            source_urls=source_urls,
        )
