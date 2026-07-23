import pytest

from src.adapters.stt.mock_stt_adapter import MockSTTAdapter


@pytest.mark.asyncio
class TestMockSTTAdapter:
    async def test_transcribe_returns_english_by_default(self, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"fake audio")
        adapter = MockSTTAdapter(default_language="en")

        result = await adapter.transcribe(audio)

        assert result.provider == "mock"
        assert result.model == "mock-v1"
        assert result.detected_language == "en"
        assert "Reliance" in result.full_text
        assert len(result.segments) == 1
        assert result.segments[0]["confidence"] == 0.95

    async def test_transcribe_hindi_language(self, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"fake")
        adapter = MockSTTAdapter()

        result = await adapter.transcribe(audio, language="hi")

        assert result.detected_language == "hi"
        assert "Reliance" in result.full_text

    async def test_transcribe_mixed_language(self, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"fake")
        adapter = MockSTTAdapter()

        result = await adapter.transcribe(audio, language="mixed")

        assert result.detected_language == "mixed"
        assert "Reliance" in result.full_text

    async def test_transcribe_malayalam_language(self, tmp_path):
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"fake")
        adapter = MockSTTAdapter()

        result = await adapter.transcribe(audio, language="ml")

        assert result.detected_language == "ml"
