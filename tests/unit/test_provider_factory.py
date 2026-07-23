
import pytest

from src.infrastructure.di.container import ProviderFactory
from src.infrastructure.config.settings import Settings


class TestProviderFactorySTT:
    def test_create_mock_stt(self):
        settings = Settings(stt_provider="mock")
        factory = ProviderFactory(settings)
        stt = factory.create_stt()
        assert stt.__class__.__name__ == "MockSTTAdapter"

    def test_whisperx_disabled_falls_back_to_mock(self):
        settings = Settings(stt_provider="whisperx", whisperx_enabled=False)
        factory = ProviderFactory(settings)
        stt = factory.create_stt()
        assert stt.__class__.__name__ == "MockSTTAdapter"

    def test_unsupported_provider_raises(self):
        settings = Settings(_env_file=None)
        settings.stt_provider = "unknown"
        factory = ProviderFactory(settings)
        with pytest.raises(ValueError, match="Unsupported STT provider"):
            factory.create_stt()


class TestProviderFactoryLLM:
    def test_create_mock_llm(self):
        settings = Settings(llm_provider="mock")
        factory = ProviderFactory(settings)
        llm = factory.create_llm()
        assert llm.__class__.__name__ == "MockLLMAdapter"

    def test_create_ollama_llm(self):
        settings = Settings(llm_provider="ollama")
        settings.load_yaml()
        factory = ProviderFactory(settings)
        llm = factory.create_llm()
        assert llm.__class__.__name__ == "OllamaLLMAdapter"

    def test_create_gemini_llm(self):
        settings = Settings(llm_provider="gemini")
        settings.load_yaml()
        factory = ProviderFactory(settings)
        llm = factory.create_llm()
        assert llm.__class__.__name__ == "GeminiLLMAdapter"

    def test_unsupported_llm_raises(self):
        settings = Settings(_env_file=None)
        settings.llm_provider = "unknown"
        factory = ProviderFactory(settings)
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            factory.create_llm()
