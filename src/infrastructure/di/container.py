from __future__ import annotations

from pathlib import Path

from src.infrastructure.config.settings import Settings
from src.ports.llm_provider import LLMProvider
from src.ports.stt_provider import SpeechToTextProvider
from src.ports.storage_provider import StorageProvider


class ProviderFactory:
    """Factory for creating provider adapters based on configuration."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @classmethod
    def from_config(cls, settings: Settings | None = None) -> "ProviderFactory":
        from src.infrastructure.config.settings import get_settings

        return cls(settings or get_settings())

    def create_storage(self) -> StorageProvider:
        backend = self._settings.storage_backend
        if backend == "local":
            from src.adapters.storage.local_storage import LocalStorageAdapter

            base_path = Path(self._settings.storage_local_path)
            return LocalStorageAdapter(base_path)
        raise ValueError(f"Unsupported storage backend: {backend}")

    def create_stt(self) -> SpeechToTextProvider:
        provider = self._settings.stt_provider
        if provider == "mock" or (
            provider == "whisperx" and not self._settings.whisperx_enabled
        ):
            from src.adapters.stt.mock_stt_adapter import MockSTTAdapter

            mock_cfg = self._settings.get("providers.stt.mock", {}) or {}
            return MockSTTAdapter(
                default_language=mock_cfg.get("default_language", "en"),
                model=mock_cfg.get("model", "mock-v1"),
            )
        if provider == "whisperx":
            from src.adapters.stt.whisperx_adapter import WhisperXSTTAdapter

            wx_cfg = self._settings.get("providers.stt.whisperx", {}) or {}
            return WhisperXSTTAdapter(
                model=wx_cfg.get("model", "large-v3"),
                device=wx_cfg.get("device", "cpu"),
                compute_type=wx_cfg.get("compute_type", "int8"),
                batch_size=wx_cfg.get("batch_size", 8),
            )
        if provider == "google":
            from src.adapters.stt.google_stt_adapter import GoogleSTTAdapter

            g_cfg = self._settings.get("providers.stt.google", {}) or {}
            return GoogleSTTAdapter(
                language_codes=g_cfg.get("language_codes"),
                model=g_cfg.get("model", "latest_long"),
                credentials_path=g_cfg.get("credentials_path"),
            )
        raise ValueError(f"Unsupported STT provider: {provider}")

    def create_audio_preprocessor(self):
        from src.infrastructure.audio.ffmpeg_preprocessor import FFmpegPreprocessor

        audio_cfg = self._settings.get("processing.audio", {}) or {}
        return FFmpegPreprocessor(
            sample_rate=audio_cfg.get("sample_rate", 16000),
            channels=audio_cfg.get("channels", 1),
            ffmpeg_path=audio_cfg.get("ffmpeg_path", "ffmpeg"),
            ffprobe_path=audio_cfg.get("ffprobe_path", "ffprobe"),
        )

    def create_llm(self) -> LLMProvider:
        provider = self._settings.llm_provider
        if provider == "mock":
            from src.adapters.llm.mock_llm_adapter import MockLLMAdapter

            mock_cfg = self._settings.get("providers.llm.mock", {}) or {}
            return MockLLMAdapter(model=mock_cfg.get("model", "mock-llm-v1"))
        if provider == "ollama":
            from src.adapters.llm.ollama_adapter import OllamaLLMAdapter
            from src.infrastructure.prompts.prompt_registry import PromptRegistry

            ollama_cfg = self._settings.get("providers.llm.ollama", {}) or {}
            prompts_base = Path(self._settings.get("prompts.base_path", "./prompts"))
            manifest = self._settings.get("prompts.manifest_path", "./prompts/manifest.yaml")
            registry = PromptRegistry(prompts_base, Path(manifest))
            return OllamaLLMAdapter(
                base_url=ollama_cfg.get("base_url", "http://localhost:11434"),
                model=ollama_cfg.get("model", "qwen2.5:7b"),
                prompt_registry=registry,
            )
        if provider == "gemini":
            from src.adapters.llm.gemini_adapter import GeminiLLMAdapter
            from src.infrastructure.prompts.prompt_registry import PromptRegistry

            gemini_cfg = self._settings.get("providers.llm.gemini", {}) or {}
            prompts_base = Path(self._settings.get("prompts.base_path", "./prompts"))
            manifest = self._settings.get("prompts.manifest_path", "./prompts/manifest.yaml")
            registry = PromptRegistry(prompts_base, Path(manifest))
            return GeminiLLMAdapter(
                model=gemini_cfg.get("model", "gemini-1.5-flash"),
                api_key=self._settings.google_api_key,
                prompt_registry=registry,
            )
        if provider == "openai":
            from src.adapters.llm.openai_adapter import OpenAILLMAdapter

            openai_cfg = self._settings.get("providers.llm.openai", {}) or {}
            return OpenAILLMAdapter(model=openai_cfg.get("model", "gpt-4o-mini"))
        raise ValueError(f"Unsupported LLM provider: {provider}")

    def create_prompt_registry(self):
        from src.infrastructure.prompts.prompt_registry import PromptRegistry

        prompts_base = Path(self._settings.get("prompts.base_path", "./prompts"))
        manifest = self._settings.get("prompts.manifest_path", "./prompts/manifest.yaml")
        return PromptRegistry(prompts_base, Path(manifest))

    def create_symbol_resolver(self):
        from src.domain.services.stock_symbol_resolver import StockSymbolResolver

        csv_path = Path(self._settings.get("stock_symbols.csv_path", "./data/stock_symbols/nse_symbols.csv"))
        return StockSymbolResolver(csv_path)

    def create_intent_validator(self):
        from src.domain.services.intent_validator import IntentValidator
        from src.domain.services.numeric_parser import NumericParser

        return IntentValidator(self.create_symbol_resolver(), NumericParser())

    def create_confidence_router(self):
        from src.application.services.confidence_router import ConfidenceRouter

        threshold = float(self._settings.get("processing.confidence_threshold", 0.85))
        return ConfidenceRouter(threshold=threshold)

    def get_stt_provider_name(self) -> str:
        return self._settings.get("providers.stt.default", self._settings.stt_provider)

    def get_llm_provider_name(self) -> str:
        return self._settings.get("providers.llm.default", self._settings.llm_provider)
