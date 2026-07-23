from __future__ import annotations

import httpx
import pytest

from src.infrastructure.audio.audio_downloader import (
    AudioDownloader,
    AudioDownloadError,
)


class TestAudioDownloaderHelpers:
    def test_extension_from_magic_wav(self):
        assert AudioDownloader._extension_from_magic(b"RIFF....WAVE") == "wav"

    def test_extension_from_magic_mp3_id3(self):
        assert AudioDownloader._extension_from_magic(b"ID3\x03") == "mp3"

    def test_extension_from_magic_mp3_frame_sync(self):
        assert AudioDownloader._extension_from_magic(b"\xff\xfb\x90") == "mp3"

    def test_extension_from_magic_m4a(self):
        assert AudioDownloader._extension_from_magic(b"\x00\x00\x00\x18ftypmp42") == "m4a"

    def test_extension_from_content_type(self):
        assert AudioDownloader._extension_from_content_type("audio/mpeg") == "mp3"
        assert AudioDownloader._extension_from_content_type("audio/x-wav") == "wav"
        assert AudioDownloader._extension_from_content_type(None) is None

    def test_resolve_filename_from_callid_query(self):
        downloader = AudioDownloader()
        filename = downloader._resolve_filename(
            "https://example.com/vr/fetchsound/?callid=abc-123",
            httpx.Headers({}),
            "audio/mpeg",
            b"ID3" + b"\x00" * 10,
        )
        assert filename == "abc-123.mp3"

    def test_resolve_filename_from_content_disposition(self):
        downloader = AudioDownloader()
        filename = downloader._resolve_filename(
            "https://example.com/audio",
            httpx.Headers({"content-disposition": 'attachment; filename="call.wav"'}),
            "application/octet-stream",
            b"RIFF" + b"\x00" * 40,
        )
        assert filename == "call.wav"

    def test_resolve_filename_defaults_to_wav_for_unknown_binary(self):
        downloader = AudioDownloader()
        filename = downloader._resolve_filename(
            "https://example.com/vr/fetchsound/?callid=xyz",
            httpx.Headers({}),
            "binary/octet-stream",
            b"\x00" * 20,
        )
        assert filename == "xyz.wav"


@pytest.mark.asyncio
async def test_download_raises_on_http_error(monkeypatch):
    class FakeResponse:
        status_code = 404
        content = b""
        headers = httpx.Headers({})

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def get(self, url):
            return FakeResponse()

    monkeypatch.setattr(
        "src.infrastructure.audio.audio_downloader.httpx.AsyncClient",
        lambda **kwargs: FakeClient(),
    )

    downloader = AudioDownloader(max_retries=1)
    with pytest.raises(AudioDownloadError, match="HTTP 404"):
        await downloader.download("https://example.com/missing")
