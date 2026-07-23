from __future__ import annotations

import json

import httpx

from src.infrastructure.prompts.prompt_registry import PromptRegistry
from src.ports.llm_provider import StructuredExtractionResult


class OllamaLLMAdapter:
    """LLM adapter for Ollama-hosted models (Llama, Qwen, Mistral)."""

    def __init__(
        self,
        *,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        prompt_registry: PromptRegistry | None = None,
        timeout: float = 120.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._registry = prompt_registry
        self._timeout = timeout

    async def extract_structured(
        self,
        transcript: str,
        schema: dict,
        *,
        prompt_version: str,
    ) -> StructuredExtractionResult:
        bundle = None
        if self._registry:
            bundle = self._registry.load(prompt_version)
            user_prompt = self._registry.render_user_prompt(bundle, transcript)
            system_prompt = bundle.system_prompt
        else:
            system_prompt = (
                "Extract trading intent from the transcript. "
                "Do not translate the transcript. Return JSON only."
            )
            user_prompt = f"Transcript:\n{transcript}\n\nReturn JSON matching schema."

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": schema,
            "stream": False,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(f"{self._base_url}/api/chat", json=payload)
            response.raise_for_status()
            body = response.json()

        content = body.get("message", {}).get("content", "{}")
        data = json.loads(content) if isinstance(content, str) else content
        confidence = float(data.get("confidence", 0.8))

        return StructuredExtractionResult(
            data=data,
            confidence=confidence,
            provider="ollama",
            model=self._model,
            raw_output=body,
        )
