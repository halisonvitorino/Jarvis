"""Testes dos utilitários de áudio (audio_utils) - Phase 3.

Todos os testes usam mocks; não dependem de microfone, áudio real nem pydub.
"""

from __future__ import annotations
import sys

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.audio_utils import AudioUtilsError


# ---------------------------------------------------------------------------
# Helpers para simular ImportError de módulos instalados
# ---------------------------------------------------------------------------


def _block_module(name: str):
    saved = sys.modules.get(name)
    sys.modules[name] = None
    return saved


def _restore_module(name: str, saved) -> None:
    if saved is not None:
        sys.modules[name] = saved
    else:
        sys.modules.pop(name, None)


# ---------------------------------------------------------------------------
# record_audio
# ---------------------------------------------------------------------------


def test_record_audio_success(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import record_audio

    output = tmp_path / "gravacao.wav"
    fake_sd = MagicMock()
    fake_sd.rec.return_value = [[0.0] * 16000]
    fake_sf = MagicMock()

    with patch.dict("sys.modules", {"sounddevice": fake_sd, "soundfile": fake_sf}):
        resultado = record_audio(str(output), duration=2.0, sample_rate=16000)

    assert resultado == str(output)
    fake_sd.rec.assert_called_once()
    fake_sd.wait.assert_called_once()
    fake_sf.write.assert_called_once()


def test_record_audio_import_error(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import record_audio

    saved = _block_module("sounddevice")
    try:
        with pytest.raises(AudioUtilsError, match="sounddevice ou soundfile nao disponivel"):
            record_audio(str(tmp_path / "x.wav"))
    finally:
        _restore_module("sounddevice", saved)


def test_record_audio_generic_error(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import record_audio

    fake_sd = MagicMock()
    fake_sd.rec.side_effect = RuntimeError("boom")
    fake_sf = MagicMock()

    with patch.dict("sys.modules", {"sounddevice": fake_sd, "soundfile": fake_sf}):
        with pytest.raises(AudioUtilsError, match="Falha ao gravar audio"):
            record_audio(str(tmp_path / "x.wav"))


# ---------------------------------------------------------------------------
# convert_audio_format
# ---------------------------------------------------------------------------


def test_convert_audio_format_success(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import convert_audio_format

    inp = tmp_path / "entrada.mp3"
    outp = tmp_path / "saida.wav"
    inp.write_bytes(b"fake audio")

    fake_segment = MagicMock()
    fake_pydub = MagicMock()
    fake_pydub.AudioSegment = fake_segment
    with patch.dict("sys.modules", {"pydub": fake_pydub}):
        fake_segment.from_file.return_value = fake_segment
        resultado = convert_audio_format(str(inp), str(outp), target_format="wav")

    assert resultado == str(outp)
    fake_segment.export.assert_called_once_with(str(outp), format="wav")


def test_convert_audio_format_import_error(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import convert_audio_format

    inp = tmp_path / "entrada.mp3"
    inp.write_bytes(b"fake audio")

    saved = _block_module("pydub")
    try:
        with pytest.raises(AudioUtilsError, match="pydub nao disponivel"):
            convert_audio_format(str(inp), str(tmp_path / "saida.wav"))
    finally:
        _restore_module("pydub", saved)


# ---------------------------------------------------------------------------
# validate_audio_file
# ---------------------------------------------------------------------------


def test_validate_audio_file_valid(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import validate_audio_file

    arquivo = tmp_path / "som.wav"
    arquivo.write_bytes(b"data")
    assert validate_audio_file(str(arquivo)) is True


def test_validate_audio_file_not_exists() -> None:
    from jarvis.voice.audio_utils import validate_audio_file

    assert validate_audio_file("nao_existe.wav") is False


def test_validate_audio_file_unsupported_extension(tmp_path: Path) -> None:
    from jarvis.voice.audio_utils import validate_audio_file

    arquivo = tmp_path / "som.xyz"
    arquivo.write_bytes(b"data")
    assert validate_audio_file(str(arquivo)) is False


# ---------------------------------------------------------------------------
# list_audio_devices
# ---------------------------------------------------------------------------


def test_list_audio_devices_success() -> None:
    from jarvis.voice.audio_utils import list_audio_devices

    fake_sd = MagicMock()
    fake_sd.query_devices.return_value = [
        {"name": "Mic", "max_input_channels": 1, "max_output_channels": 0, "default_samplerate": 16000},
        {"name": "Speakers", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 44100},
    ]

    with patch.dict("sys.modules", {"sounddevice": fake_sd}):
        resultado = list_audio_devices()

    assert "input" in resultado
    assert "output" in resultado
    assert len(resultado["input"]) == 1
    assert len(resultado["output"]) == 1
    assert resultado["input"][0]["name"] == "Mic"


def test_list_audio_devices_import_error() -> None:
    from jarvis.voice.audio_utils import list_audio_devices

    saved = _block_module("sounddevice")
    try:
        with pytest.raises(AudioUtilsError, match="sounddevice nao disponivel"):
            list_audio_devices()
    finally:
        _restore_module("sounddevice", saved)


# ---------------------------------------------------------------------------
# AudioUtilsError
# ---------------------------------------------------------------------------


def test_audio_utils_error_is_exception() -> None:
    err = AudioUtilsError("falha")
    assert isinstance(err, Exception)
    assert str(err) == "falha"