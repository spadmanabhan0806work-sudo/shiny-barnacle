from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases import UploadCallUseCase
from src.application.use_cases.batch_upload import BatchUploadUseCase
from src.application.use_cases.ingest_from_url import (
    BatchIngestFromUrlsUseCase,
    IngestCallFromUrlUseCase,
)
from src.application.use_cases.process_call import ProcessCallUseCase, _build_orchestrator
from src.domain.entities.call_recording import CallRecording
from src.domain.entities.intent_extraction import IntentExtraction
from src.domain.entities.transcript import Transcript
from src.infrastructure.config.settings import get_settings
from src.infrastructure.di.container import ProviderFactory
from src.infrastructure.persistence.database import get_db_session
from src.infrastructure.persistence.repositories import (
    SqlAlchemyCallRecordingRepository,
    SqlAlchemyIntentExtractionRepository,
    SqlAlchemyReviewQueueRepository,
    SqlAlchemyTranscriptRepository,
)

router = APIRouter(prefix="/calls", tags=["calls"])


async def _process_calls_inline(
    session: AsyncSession,
    call_ids: list[UUID],
    *,
    prompt_version: str | None = None,
) -> None:
    """Run the full STT + extraction pipeline in-process (no background queue).

    Uses the request session so ingested rows are visible without a cross-connection
    commit (required for SQLite file databases under concurrent HTTP load).
    """
    settings = get_settings()
    for call_id in call_ids:
        orchestrator = _build_orchestrator(session, settings)
        use_case = ProcessCallUseCase(orchestrator)
        await use_case.execute(call_id, prompt_version=prompt_version)


async def _response_after_processing(
    session: AsyncSession,
    call_id: UUID,
) -> CallResponse:
    details = await _load_call_details(session, call_id)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Call not found: {call_id}")
    recording, transcript, extraction, review = details
    return CallResponse.from_entity(recording, transcript, extraction, review)


class TranscriptResponse(BaseModel):
    id: UUID
    full_text: str
    segments: list[dict]
    stt_provider: str
    stt_model: str

    @classmethod
    def from_entity(cls, transcript: Transcript) -> "TranscriptResponse":
        return cls(
            id=transcript.id,
            full_text=transcript.full_text,
            segments=[
                {
                    "start": s.start,
                    "end": s.end,
                    "text": s.text,
                    "confidence": s.confidence,
                }
                for s in transcript.segments
            ],
            stt_provider=transcript.stt_provider,
            stt_model=transcript.stt_model,
        )


class IntentExtractionResponse(BaseModel):
    id: UUID
    side: str
    stock_symbol: str
    quantity: int
    price: float
    exchange: str
    confidence: float
    prompt_version: str
    llm_provider: str

    @classmethod
    def from_entity(cls, extraction: IntentExtraction) -> "IntentExtractionResponse":
        return cls(
            id=extraction.id,
            side=extraction.side,
            stock_symbol=extraction.stock_symbol,
            quantity=extraction.quantity,
            price=extraction.price,
            exchange=extraction.exchange,
            confidence=extraction.confidence,
            prompt_version=extraction.prompt_version,
            llm_provider=extraction.llm_provider,
        )


class ReviewStatusResponse(BaseModel):
    id: UUID
    status: str
    corrected_fields: dict | None = None


class CallResponse(BaseModel):
    id: UUID
    tenant_id: str
    storage_key: str
    status: str
    detected_language: str | None = None
    duration_sec: float | None = None
    transcript: TranscriptResponse | None = None
    intent_extraction: IntentExtractionResponse | None = None
    review: ReviewStatusResponse | None = None

    @classmethod
    def from_entity(
        cls,
        recording: CallRecording,
        transcript: Transcript | None = None,
        extraction: IntentExtraction | None = None,
        review: ReviewStatusResponse | None = None,
    ) -> "CallResponse":
        return cls(
            id=recording.id,
            tenant_id=recording.tenant_id,
            storage_key=recording.storage_key,
            status=recording.status.value,
            detected_language=recording.detected_language,
            duration_sec=recording.duration_sec,
            transcript=TranscriptResponse.from_entity(transcript) if transcript else None,
            intent_extraction=IntentExtractionResponse.from_entity(extraction)
            if extraction
            else None,
            review=review,
        )


class CallListResponse(BaseModel):
    calls: list[CallResponse]
    total: int


class ReprocessRequest(BaseModel):
    prompt_version: str | None = None


class BatchUploadResponse(BaseModel):
    batch_id: UUID
    call_ids: list[UUID]
    total: int
    errors: list[str] = Field(default_factory=list)


class FromUrlRequest(BaseModel):
    url: HttpUrl


class BatchFromUrlsRequest(BaseModel):
    urls: list[HttpUrl] = Field(..., min_length=1, max_length=100)


@router.post("/from-url", response_model=CallResponse, status_code=201)
async def ingest_call_from_url(
    body: FromUrlRequest,
    session: AsyncSession = Depends(get_db_session),
) -> CallResponse:
    settings = get_settings()
    factory = ProviderFactory.from_config(settings)
    storage = factory.create_storage()

    use_case = IngestCallFromUrlUseCase(session, storage, settings)
    try:
        result = await use_case.execute(str(body.url))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _process_calls_inline(session, [result.recording.id])
    return await _response_after_processing(session, result.recording.id)


@router.post("/batch/from-urls", response_model=BatchUploadResponse, status_code=201)
async def batch_ingest_from_urls(
    body: BatchFromUrlsRequest,
    session: AsyncSession = Depends(get_db_session),
) -> BatchUploadResponse:
    settings = get_settings()
    factory = ProviderFactory.from_config(settings)
    storage = factory.create_storage()

    use_case = BatchIngestFromUrlsUseCase(session, storage, settings)
    try:
        result = await use_case.execute([str(url) for url in body.urls])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _process_calls_inline(session, result.call_ids)

    return BatchUploadResponse(
        batch_id=result.batch_id,
        call_ids=result.call_ids,
        total=len(result.call_ids),
        errors=result.errors,
    )


@router.post("/batch", response_model=BatchUploadResponse, status_code=201)
async def batch_upload_calls(
    files: list[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> BatchUploadResponse:
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 files per batch")

    settings = get_settings()
    factory = ProviderFactory.from_config(settings)
    storage = factory.create_storage()

    file_tuples: list[tuple[str, bytes, str | None]] = []
    for f in files:
        data = await f.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"Empty file: {f.filename}")
        file_tuples.append((f.filename or "audio.wav", data, f.content_type))

    use_case = BatchUploadUseCase(session, storage, settings)
    try:
        result = await use_case.execute(file_tuples)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _process_calls_inline(session, result.call_ids)

    return BatchUploadResponse(
        batch_id=result.batch_id,
        call_ids=result.call_ids,
        total=len(result.call_ids),
        errors=result.errors,
    )


@router.post("", response_model=CallResponse, status_code=201)
async def upload_call(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_db_session),
) -> CallResponse:
    settings = get_settings()
    factory = ProviderFactory.from_config(settings)
    storage = factory.create_storage()

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Empty file")

    use_case = UploadCallUseCase(
        SqlAlchemyCallRecordingRepository(session),
        storage,
        settings,
    )
    try:
        recording = await use_case.execute(
            filename=file.filename or "audio.wav",
            data=data,
            content_type=file.content_type,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await _process_calls_inline(session, [recording.id])
    return await _response_after_processing(session, recording.id)


@router.get("", response_model=CallListResponse)
async def list_calls(
    session: AsyncSession = Depends(get_db_session),
    limit: int = 100,
    offset: int = 0,
) -> CallListResponse:
    repo = SqlAlchemyCallRecordingRepository(session)
    calls = await repo.list_all(limit=limit, offset=offset)
    return CallListResponse(
        calls=[CallResponse.from_entity(c) for c in calls],
        total=len(calls),
    )


async def _load_call_details(session: AsyncSession, call_id: UUID):
    call_repo = SqlAlchemyCallRecordingRepository(session)
    transcript_repo = SqlAlchemyTranscriptRepository(session)
    intent_repo = SqlAlchemyIntentExtractionRepository(session)
    review_repo = SqlAlchemyReviewQueueRepository(session)

    recording = await call_repo.get_by_id(call_id)
    if recording is None:
        return None

    transcript = await transcript_repo.get_by_call_id(call_id)
    extraction = await intent_repo.get_by_call_id(call_id)

    review_response = None
    if extraction:
        review_item = await review_repo.get_by_extraction_id(extraction.id)
        if review_item:
            review_response = ReviewStatusResponse(
                id=review_item.id,
                status=review_item.status.value,
                corrected_fields=review_item.corrected_fields,
            )

    return recording, transcript, extraction, review_response


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> CallResponse:
    details = await _load_call_details(session, call_id)
    if details is None:
        raise HTTPException(status_code=404, detail=f"Call not found: {call_id}")

    recording, transcript, extraction, review = details
    return CallResponse.from_entity(recording, transcript, extraction, review)


@router.post("/{call_id}/reprocess", response_model=CallResponse)
async def reprocess_call(
    call_id: UUID,
    body: ReprocessRequest | None = None,
    session: AsyncSession = Depends(get_db_session),
) -> CallResponse:
    call_repo = SqlAlchemyCallRecordingRepository(session)
    recording = await call_repo.get_by_id(call_id)
    if recording is None:
        raise HTTPException(status_code=404, detail=f"Call not found: {call_id}")

    prompt_version = body.prompt_version if body else None
    await _process_calls_inline(session, [call_id], prompt_version=prompt_version)

    return await _response_after_processing(session, call_id)


@router.get("/{call_id}/audio")
async def get_call_audio(
    call_id: UUID,
    session: AsyncSession = Depends(get_db_session),
) -> Response:
    call_repo = SqlAlchemyCallRecordingRepository(session)
    recording = await call_repo.get_by_id(call_id)
    if recording is None:
        raise HTTPException(status_code=404, detail=f"Call not found: {call_id}")

    settings = get_settings()
    factory = ProviderFactory.from_config(settings)
    storage = factory.create_storage()

    try:
        data = await storage.download(recording.storage_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Audio file not found") from exc

    suffix = recording.storage_key.rsplit(".", 1)[-1].lower()
    media_types = {
        "wav": "audio/wav",
        "mp3": "audio/mpeg",
        "m4a": "audio/mp4",
    }
    media_type = media_types.get(suffix, "application/octet-stream")
    return Response(content=data, media_type=media_type)
