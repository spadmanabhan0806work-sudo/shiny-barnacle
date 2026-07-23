from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.audio.ffmpeg_preprocessor import AudioMetadata, FFmpegPreprocessor


class TestFFmpegPreprocessor:
    def test_unsupported_format_raises(self, tmp_path):
        input_file = tmp_path / "input.flac"
        input_file.write_bytes(b"data")
        output_file = tmp_path / "output.wav"
        preprocessor = FFmpegPreprocessor()

        with pytest.raises(ValueError, match="Unsupported audio format"):
            preprocessor.normalize(input_file, output_file)

    @patch("src.infrastructure.audio.ffmpeg_preprocessor.subprocess.run")
    def test_normalize_calls_ffmpeg(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        input_file = tmp_path / "input.mp3"
        input_file.write_bytes(b"fake mp3")
        output_file = tmp_path / "output.wav"

        preprocessor = FFmpegPreprocessor(sample_rate=16000, channels=1)
        with patch.object(preprocessor, "probe") as mock_probe:
            mock_probe.return_value = AudioMetadata(
                duration_sec=12.5, sample_rate=16000, channels=1
            )
            metadata = preprocessor.normalize(input_file, output_file)

        assert metadata.duration_sec == 12.5
        ffmpeg_cmd = mock_run.call_args_list[0][0][0]
        assert ffmpeg_cmd[0] == "ffmpeg"
        assert "-ar" in ffmpeg_cmd
        assert "16000" in ffmpeg_cmd
        assert str(output_file) in ffmpeg_cmd

    @patch("src.infrastructure.audio.ffmpeg_preprocessor.subprocess.run")
    def test_normalize_ffmpeg_failure_raises(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(returncode=1, stderr="invalid data")
        input_file = tmp_path / "input.wav"
        input_file.write_bytes(b"bad")
        output_file = tmp_path / "output.wav"

        preprocessor = FFmpegPreprocessor()
        with pytest.raises(RuntimeError, match="FFmpeg failed"):
            preprocessor.normalize(input_file, output_file)

    @patch("src.infrastructure.audio.ffmpeg_preprocessor.subprocess.run")
    def test_probe_parses_ffprobe_output(self, mock_run, tmp_path):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="duration=45.123456\nsample_rate=16000\nchannels=1\n",
            stderr="",
        )
        audio = tmp_path / "test.wav"
        audio.write_bytes(b"wav")

        preprocessor = FFmpegPreprocessor()
        metadata = preprocessor.probe(audio)

        assert metadata.duration_sec == pytest.approx(45.123456)
        assert metadata.sample_rate == 16000
        assert metadata.channels == 1
