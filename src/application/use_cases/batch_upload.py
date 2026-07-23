from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases import UploadCallUseCase
from src.infrastructure.config.settings import Settings
from src.infrastructure.persistence.models import BatchModel
from src.infrastructure.persistence.repositories import SqlAlchemyCallRecordingRepository
from src.ports.storage_provider import StorageProvider


@dataclass
class BatchUploadResult:
    batch_id: uuid.UUID
    call_ids: list[uuid.UUID] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    total: int = 0


class BatchUploadUseCase:
    """Upload up to 100 audio files as a single batch."""

    MAX_FILES = 100

    def __init__(
        self,
        session: AsyncSession,
        storage: StorageProvider,
        settings: Settings,
    ) -> None:
        self._session = session
        self._settings = settings
        self._upload = UploadCallUseCase(
            SqlAlchemyCallRecordingRepository(session),
            storage,
            settings,
        )

    async def execute(
        self,
        files: list[tuple[str, bytes, str | None]],
    ) -> BatchUploadResult:
        if not files:
            raise ValueError("At least one file is required")
        if len(files) > self.MAX_FILES:
            raise ValueError(f"Maximum {self.MAX_FILES} files per batch")

        batch_id = uuid.uuid4()
        call_ids: list[uuid.UUID] = []
        errors: list[str] = []

        for filename, data, content_type in files:
            if not data:
                errors.append(f"{filename}: empty file")
                continue
            try:
                recording = await self._upload.execute(
                    filename=filename,
                    data=data,
                    content_type=content_type,
                )
                call_ids.append(recording.id)
            except ValueError as exc:
                errors.append(f"{filename}: {exc}")

        if not call_ids:
            raise ValueError("No files were uploaded successfully")

        batch = BatchModel(
            id=batch_id,
            tenant_id=self._settings.tenant_id,
            status="pending",
            call_ids=[str(cid) for cid in call_ids],
        )
        self._session.add(batch)
        await self._session.flush()

        return BatchUploadResult(
            batch_id=batch_id,
            call_ids=call_ids,
            errors=errors,
            total=len(call_ids),
        )
