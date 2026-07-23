from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class AudioMetadata:
    duration_sec: float
    sample_rate: int
    channels: int


class FFmpegPreprocessor:
    """Normalize audio to 16kHz mono WAV using FFmpeg."""

    SUPPORTED_INPUT_FORMATS = {".wav", ".mp3", ".m4a"}

    def __init__(
        self,
        *,
        sample_rate: int = 16000,
        channels: int = 1,
        ffmpeg_path: str = "ffmpeg",
        ffprobe_path: str = "ffprobe",
    ) -> None:
        self._sample_rate = sample_rate
        self._channels = channels
        self._ffmpeg_path = ffmpeg_path
        self._ffprobe_path = ffprobe_path

    def normalize(self, input_path: Path, output_path: Path) -> AudioMetadata:
        suffix = input_path.suffix.lower()
        if suffix not in self.SUPPORTED_INPUT_FORMATS:
            raise ValueError(
                f"Unsupported audio format: {suffix}. "
                f"Supported: {sorted(self.SUPPORTED_INPUT_FORMATS)}"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            self._ffmpeg_path,
            "-y",
            "-i",
            str(input_path),
            "-ar",
            str(self._sample_rate),
            "-ac",
            str(self._channels),
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {result.stderr.strip()}")

        metadata = self.probe(output_path)
        return metadata

    def probe(self, audio_path: Path) -> AudioMetadata:
        cmd = [
            self._ffprobe_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=sample_rate,channels",
            "-of",
            "default=noprint_wrappers=1",
            str(audio_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFprobe failed: {result.stderr.strip()}")

        duration_sec = 0.0
        sample_rate = self._sample_rate
        channels = self._channels
        for line in result.stdout.strip().splitlines():
            if line.startswith("duration="):
                duration_sec = float(line.split("=", 1)[1])
            elif line.startswith("sample_rate="):
                sample_rate = int(float(line.split("=", 1)[1]))
            elif line.startswith("channels="):
                channels = int(line.split("=", 1)[1])

        return AudioMetadata(
            duration_sec=duration_sec,
            sample_rate=sample_rate,
            channels=channels,
        )
