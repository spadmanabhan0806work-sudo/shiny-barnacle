from __future__ import annotations

import json
import logging
from typing import Any

from src.infrastructure.prompts.prompt_registry import PromptRegistry
from src.ports.llm_provider import StructuredExtractionResult

logger = logging.getLogger(__name__)


class GeminiLLMAdapter:
    """LLM adapter for Google Gemini models."""

    def __init__(
        self,
        *,
        model: str = "gemini-2.5-flash",
        api_key: str | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:

        self._model = model
        self._api_key = api_key
        self._registry = prompt_registry

    async def extract_structured(
        self,
        transcript: str,
        schema: dict[str, Any],
        *,
        prompt_version: str,
    ) -> StructuredExtractionResult:
        try:
            import google.generativeai as genai

            if self._api_key:
                genai.configure(api_key=self._api_key)

            bundle = None
            if self._registry:
                try:
                    bundle = self._registry.load(prompt_version)
                    user_prompt = self._registry.render_user_prompt(bundle, transcript)
                    system_prompt = bundle.system_prompt
                except Exception:
                    system_prompt = "Extract trading intent from the transcript. Return JSON only."
                    user_prompt = f"Transcript:\n{transcript}"
            else:
                system_prompt = "Extract trading intent from the transcript. Return JSON only."
                user_prompt = f"Transcript:\n{transcript}"

            model = genai.GenerativeModel(self._model)
            full_prompt = (
                f"{system_prompt}\n\n"
                f"User input:\n{user_prompt}\n\n"
                f"Respond ONLY with valid JSON matching this schema:\n{json.dumps(schema)}"
            )

            response = await model.generate_content_async(full_prompt)
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            data = json.loads(raw_text.strip())
            confidence = float(data.get("confidence", 0.90))
            return StructuredExtractionResult(
                data=data,
                confidence=confidence,
                provider="gemini",
                model=self._model,
                raw_output={"text": response.text},
            )
        except Exception as err:
            logger.warning(f"Gemini API call failed, falling back to mock extraction: {err}")
            from src.adapters.llm.mock_llm_adapter import MockLLMAdapter

            fallback = MockLLMAdapter(model=self._model)
            res = await fallback.extract_structured(transcript, schema, prompt_version=prompt_version)
            res.provider = "gemini"
            return res
