from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

_CONTENT_TYPE_EXT = {
    "audio/wav": "wav",
    "audio/x-wav": "wav",
    "audio/wave": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/mp4": "m4a",
    "audio/m4a": "m4a",
    "audio/x-m4a": "m4a",
}

_MAGIC_SIGNATURES: list[tuple[bytes, str]] = [
    (b"RIFF", "wav"),
    (b"ID3", "mp3"),
    (b"\xff\xfb", "mp3"),
    (b"\xff\xf3", "mp3"),
    (b"\xff\xf2", "mp3"),
    (b"ftyp", "m4a"),
]

_FILENAME_EXT = re.compile(r"\.(wav|mp3|m4a)(?:\?|$)", re.IGNORECASE)


@dataclass
class DownloadedAudio:
    url: str
    data: bytes
    filename: str
    content_type: str | None


class AudioDownloadError(Exception):
    """Raised when audio cannot be downloaded from a URL."""


class AudioDownloader:
    """Download call recordings from remote URLs with retries and rate limiting."""

    def __init__(
        self,
        *,
        timeout_sec: float = 60.0,
        max_retries: int = 3,
        retry_backoff_sec: float = 2.0,
        max_concurrent: int = 5,
        min_interval_sec: float = 0.2,
    ) -> None:
        self._timeout = timeout_sec
        self._max_retries = max_retries
        self._retry_backoff_sec = retry_backoff_sec
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._min_interval_sec = min_interval_sec
        self._last_request_at = 0.0
        self._rate_lock = asyncio.Lock()

    async def download(self, url: str) -> DownloadedAudio:
        async with self._semaphore:
            await self._throttle()
            last_error: Exception | None = None
            for attempt in range(self._max_retries):
                try:
                    return await self._download_once(url)
                except (httpx.HTTPError, AudioDownloadError) as exc:
                    last_error = exc
                    if attempt < self._max_retries - 1:
                        await asyncio.sleep(self._retry_backoff_sec * (attempt + 1))
            raise AudioDownloadError(f"Failed to download {url}: {last_error}") from last_error

    async def _throttle(self) -> None:
        async with self._rate_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_at
            if elapsed < self._min_interval_sec:
                await asyncio.sleep(self._min_interval_sec - elapsed)
            self._last_request_at = asyncio.get_event_loop().time()

    async def _download_once(self, url: str) -> DownloadedAudio:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
            follow_redirects=True,
        ) as client:
            response = await client.get(url)
            if response.status_code >= 400:
                raise AudioDownloadError(f"HTTP {response.status_code} for {url}")

            data = response.content
            if not data:
                raise AudioDownloadError(f"Empty response body for {url}")

            content_type = response.headers.get("content-type", "").split(";")[0].strip() or None
            filename = self._resolve_filename(url, response.headers, content_type, data)
            return DownloadedAudio(
                url=url,
                data=data,
                filename=filename,
                content_type=content_type,
            )

    def _resolve_filename(
        self,
        url: str,
        headers: httpx.Headers,
        content_type: str | None,
        data: bytes,
    ) -> str:
        disposition = headers.get("content-disposition", "")
        if "filename=" in disposition:
            match = re.search(r'filename="?([^";]+)"?', disposition)
            if match:
                name = Path(match.group(1)).name
                if self._extension(name):
                    return name

        parsed = urlparse(url)
        path_name = Path(parsed.path).name
        if path_name and self._extension(path_name):
            return path_name

        query = parse_qs(parsed.query)
        call_id = query.get("callid", [None])[0]
        ext = self._extension_from_content_type(content_type) or self._extension_from_magic(data)
        if not ext:
            ext = "wav"
        stem = call_id or Path(path_name).stem or "recording"
        return f"{stem}.{ext}"

    @staticmethod
    def _extension(filename: str) -> str | None:
        suffix = Path(filename).suffix.lstrip(".").lower()
        if suffix in ("wav", "mp3", "m4a"):
            return suffix
        match = _FILENAME_EXT.search(filename)
        return match.group(1).lower() if match else None

    @staticmethod
    def _extension_from_content_type(content_type: str | None) -> str | None:
        if not content_type:
            return None
        return _CONTENT_TYPE_EXT.get(content_type.lower())

    @staticmethod
    def _extension_from_magic(data: bytes) -> str | None:
        if len(data) >= 4 and data[:4] == b"RIFF":
            return "wav"
        if len(data) >= 3 and data[:3] == b"ID3":
            return "mp3"
        if len(data) >= 2 and data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
            return "mp3"
        if len(data) >= 8 and data[4:8] == b"ftyp":
            return "m4a"
        for signature, ext in _MAGIC_SIGNATURES:
            if data.startswith(signature):
                return ext
        return None
