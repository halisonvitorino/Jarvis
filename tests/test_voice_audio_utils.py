"""Testes do modulo de utilitarios de audio.

Valida gravacao, conversao de formato, validacao de arquivo
e listagem de dispositivos com mocks.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.audio_utils import AudioUtilsError, list_audio_devices, record_audio, validate_audio_file


class TestRecordAudio:
    """Testes de gravacao de microfone."""

    def test_record_audio_success(self, tmp_path: Path) -> None:
        output = str(tmp_path / "rec.wav")
        with patch("jarvis.voice.audio_utils.sd") as mock_sd, patch(
            "jarvis.voice.audio_utils.sf"
        ) as mock_sf:
            mock_sf.write = MagicMock()
            result = record_audio(output, duration=1.0)
        assert result == output
        mock_sd.rec.assert_called_once()
        mock_sd.wait.assert_called_once()
        mock_sf.write.assert_called_once()

    def test_record_audio_missing_deps(self, tmp_path: Path) -> None:
        output = str(tmp_path / "rec.wav")
        with patch("jarvis.voice.audio_utils.sd", side_effect=ImportError("missing")):
            with pytest.raises(AudioUtilsError, match="sounddevice ou soundfile nao disponivel"):
                record_audio(output)

    def test_record_audio_failure_wraps_error(self, tmp_path: Path) -> None:
        output = str(tmp_path / "rec.wav")
        with patch("jarvis.voice.audio_utils.sd") as mock_sd, patch(
            "jarvis.voice.audio_utils.sf"
        ) as mock_sf:
            mock_sd.wait.side_effect = RuntimeError("fail")
            with pytest.raises(AudioUtilsError, match="Falha ao gravar audio"):
                record_audio(output)

    def test_record_audio_logs(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        output = str(tmp_path / "rec.wav")
        with patch("jarvis.voice.audio_utils.sd"), patch("jarvis.voice.audio_utils.sf"):
            with caplog.at_level(logging.INFO, logger="jarvis.voice.audio_utils"):
                record_audio(output, duration=2.0)
        assert "Gravando audio" in caplog.text


class TestConvertAudioFormat:
    """Testes de conversao de formato de audio."""

    def test_convert_audio_success(self, tmp_path: Path) -> None:
        input_path = str(tmp_path / "input.mp3")
        output_path = str(tmp_path / "output.wav")
        with patch("pydub.AudioSegment") as mock_segment:
            result = convert_audio_format(input_path, output_path, "wav")
        assert result == output_path
        mock_segment.from_file.assert_called_once_with(input_path)
        mock_segment.from_file.return_value.export.assert_called_once_with(
            output_path, format="wav"
        )

    def test_convert_audio_missing_deps(self, tmp_path: Path) -> None:
        with patch("pydub.AudioSegment", side_effect=ImportError("missing")):
            with pytest.raises(AudioUtilsError, match="pydub nao disponivel"):
                convert_audio_format("in.mp3", "out.wav")

    def test_convert_audio_failure_wraps_error(self, tmp_path: Path) -> None:
        with patch("pydub.AudioSegment") as mock_segment:
            mock_segment.from_file.return_value.export.side_effect = RuntimeError("fail")
            with pytest.raises(AudioUtilsError, match="Falha ao converter audio"):
                convert_audio_format("in.mp3", "out.wav")


class TestValidateAudioFile:
    """Testes de validacao de arquivo de audio."""

    def test_existing_valid_file(self, tmp_path: Path) -> None:
        path = tmp_path / "audio.wav"
        path.write_bytes(b"data")
        assert validate_audio_file(str(path)) is True

    def test_nonexistent_file(self, tmp_path: Path) -> None:
        assert validate_audio_file(str(tmp_path / "missing.wav")) is False

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        path = tmp_path / "audio.txt"
        path.write_bytes(b"data")
        assert validate_audio_file(str(path)) is False

    def test_supported_extensions(self, tmp_path: Path) -> None:
        for ext in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
            path = tmp_path / f"audio{ext}"
            path.write_bytes(b"data")
            assert validate_audio_file(str(path)) is True, f"Failed for {ext}"

    def test_validate_logs_warning_on_missing(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.WARNING, logger="jarvis.voice.audio_utils"):
            validate_audio_file(str(tmp_path / "missing.wav"))
        assert "Arquivo de audio nao encontrado" in caplog.text


class TestListAudioDevices:
    """Testes de listagem de dispositivos de audio."""

    def test_list_audio_devices_success(self) -> None:
        devices = [
            {"name": "mic", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 16000},
            {"name": "speaker", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
        ]
        with patch("jarvis.voice.audio_utils.sd") as mock_sd:
            mock_sd.query_devices.return_value = devices
            result = list_audio_devices()
        assert len(result["input"]) == 1
        assert len(result["output"]) == 1
        assert result["input"][0]["name"] == "mic"
        assert result["output"][0]["name"] == "speaker"

    def test_list_audio_devices_missing_deps(self) -> None:
        with patch("jarvis.voice.audio_utils.sd", side_effect=ImportError("missing")):
            with pytest.raises(AudioUtilsError, match="sounddevice nao disponivel"):
                list_audio_devices()

    def test_list_audio_devices_failure_wraps_error(self) -> None:
        with patch("jarvis.voice.audio_utils.sd") as mock_sd:
            mock_sd.query_devices.side_effect = RuntimeError("fail")
            with pytest.raises(AudioUtilsError, match="Falha ao listar dispositivos"):
                list_audio_devices()