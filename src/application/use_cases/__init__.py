from __future__ import annotations

import uuid
from pathlib import Path

from src.domain.entities.annotation import Annotation, AnnotationStatus, GroundTruth
from src.domain.entities.call_recording import CallRecording, CallStatus
from src.domain.repositories.annotation_repository import AnnotationRepository
from src.domain.repositories.call_recording_repository import CallRecordingRepository
from src.infrastructure.config.settings import Settings
from src.ports.storage_provider import StorageProvider


class UploadCallUseCase:
    def __init__(
        self,
        call_repo: CallRecordingRepository,
        storage: StorageProvider,
        settings: Settings,
    ) -> None:
        self._call_repo = call_repo
        self._storage = storage
        self._settings = settings

    async def execute(
        self,
        filename: str,
        data: bytes,
        *,
        content_type: str | None = None,
    ) -> CallRecording:
        ext = Path(filename).suffix.lstrip(".").lower()
        supported = self._settings.get(
            "processing.supported_audio_formats", ["wav", "mp3", "m4a"]
        )
        if ext not in supported:
            raise ValueError(f"Unsupported audio format: {ext}. Supported: {supported}")

        call_id = uuid.uuid4()
        storage_key = f"{self._settings.tenant_id}/{call_id}/{filename}"
        await self._storage.upload(storage_key, data)

        recording = CallRecording(
            id=call_id,
            tenant_id=self._settings.tenant_id,
            storage_key=storage_key,
            status=CallStatus.PENDING,
        )
        return await self._call_repo.create(recording)


class CreateAnnotationUseCase:
    def __init__(
        self,
        annotation_repo: AnnotationRepository,
        call_repo: CallRecordingRepository,
    ) -> None:
        self._annotation_repo = annotation_repo
        self._call_repo = call_repo

    async def execute(
        self,
        call_id: uuid.UUID,
        annotator_id: str,
        ground_truth: dict,
    ) -> Annotation:
        call = await self._call_repo.get_by_id(call_id)
        if call is None:
            raise ValueError(f"Call recording not found: {call_id}")

        existing = await self._annotation_repo.get_by_call_id(call_id)
        gt = GroundTruth(
            side=ground_truth["side"],
            stock_symbol=ground_truth["stock_symbol"],
            quantity=ground_truth["quantity"],
            price=ground_truth["price"],
            exchange=ground_truth["exchange"],
        )

        if existing:
            existing.ground_truth = gt
            existing.annotator_id = annotator_id
            existing.submit()
            return await self._annotation_repo.update(existing)

        annotation = Annotation(
            call_id=call_id,
            annotator_id=annotator_id,
            ground_truth=gt,
            status=AnnotationStatus.SUBMITTED,
        )
        return await self._annotation_repo.create(annotation)


class GetAnnotationUseCase:
    def __init__(self, annotation_repo: AnnotationRepository) -> None:
        self._annotation_repo = annotation_repo

    async def execute(self, call_id: uuid.UUID) -> Annotation | None:
        return await self._annotation_repo.get_by_call_id(call_id)
