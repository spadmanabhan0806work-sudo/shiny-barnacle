from __future__ import annotations

import asyncio
from uuid import UUID

from src.application.orchestrators.call_processing_orchestrator import CallProcessingOrchestrator
from src.infrastructure.config.settings import Settings, get_settings
from src.infrastructure.di.container import ProviderFactory
from src.infrastructure.persistence.database import get_session_factory
from src.infrastructure.persistence.repositories import (
    SqlAlchemyCallRecordingRepository,
    SqlAlchemyIntentExtractionRepository,
    SqlAlchemyReviewQueueRepository,
    SqlAlchemyTranscriptRepository,
)


class ProcessCallUseCase:
    """Application use case entry point for full call processing."""

    def __init__(self, orchestrator: CallProcessingOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def execute(
        self,
        call_id: UUID,
        *,
        prompt_version: str | None = None,
    ) -> tuple:
        return await self._orchestrator.process_call(call_id, prompt_version=prompt_version)


def _build_orchestrator(session, settings: Settings) -> CallProcessingOrchestrator:
    factory = ProviderFactory.from_config(settings)
    return CallProcessingOrchestrator(
        SqlAlchemyCallRecordingRepository(session),
        SqlAlchemyTranscriptRepository(session),
        SqlAlchemyIntentExtractionRepository(session),
        SqlAlchemyReviewQueueRepository(session),
        factory.create_storage(),
        factory.create_stt(),
        factory.create_llm(),
        factory.create_prompt_registry(),
        factory.create_intent_validator(),
        factory.create_confidence_router(),
        factory.create_audio_preprocessor(),
    )


async def process_call_async(
    call_id: UUID,
    settings: Settings | None = None,
    *,
    prompt_version: str | None = None,
) -> tuple:
    settings = settings or get_settings()
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            orchestrator = _build_orchestrator(session, settings)
            use_case = ProcessCallUseCase(orchestrator)
            result = await use_case.execute(call_id, prompt_version=prompt_version)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


def process_call_sync(
    call_id: str,
    settings: Settings | None = None,
    *,
    prompt_version: str | None = None,
) -> dict:
    """Synchronous entry point for scripts and CLI tools."""
    transcript, extraction, review_item = asyncio.run(
        process_call_async(UUID(call_id), settings, prompt_version=prompt_version)
    )
    return {
        "call_id": call_id,
        "status": "review_required" if review_item else "completed",
        "transcript_id": str(transcript.id),
        "extraction_id": str(extraction.id),
        "stt_provider": transcript.stt_provider,
        "llm_provider": extraction.llm_provider,
        "confidence": extraction.confidence,
    }
