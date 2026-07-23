from __future__ import annotations

from src.ports.llm_provider import StructuredExtractionResult


class OpenAILLMAdapter:
    """Stub OpenAI adapter for future production use."""

    def __init__(self, *, model: str = "gpt-4o-mini", api_key: str | None = None) -> None:
        self._model = model
        self._api_key = api_key

    async def extract_structured(
        self,
        transcript: str,
        schema: dict,
        *,
        prompt_version: str,
    ) -> StructuredExtractionResult:
        raise NotImplementedError(
            "OpenAI LLM adapter is a stub — configure Ollama or mock for M3 PoC"
        )
