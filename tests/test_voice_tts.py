"""Testes do módulo Text-to-Speech (TTS) - Phase 3.

Todos os testes usam mocks; não dependem do Piper TTS real nem de áudio.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.tts import TextToSpeech, TTSError


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------


def test_tts_default_values(tmp_path: Path) -> None:
    out = tmp_path / "voice_output"
    tts = TextToSpeech(output_dir=str(out))
    assert tts.model_path is None
    assert tts.config_path is None
    assert tts.output_dir == out
    assert tts._is_loaded is False
    assert tts._engine is None
    assert out.exists()


def test_tts_custom_values(tmp_path: Path) -> None:
    out = tmp_path / "custom_out"
    tts = TextToSpeech(
        model_path="model.onnx",
        config_path="config.json",
        output_dir=str(out),
    )
    assert tts.model_path == "model.onnx"
    assert tts.config_path == "config.json"
    assert tts.output_dir == out


# ---------------------------------------------------------------------------
# load_model
# ---------------------------------------------------------------------------


def test_tts_load_model_success() -> None:
    fake_engine = MagicMock()
    mock_piper = MagicMock()
    mock_piper.load.return_value = fake_engine
    tts = TextToSpeech()
    with patch("piper.PiperVoice", mock_piper):
        tts.load_model()
    assert tts._is_loaded is True
    assert tts._engine is fake_engine


def test_tts_load_model_idempotent() -> None:
    fake_engine = MagicMock()
    mock_piper = MagicMock()
    mock_piper.load.return_value = fake_engine
    tts = TextToSpeech()
    with patch("piper.PiperVoice", mock_piper) as piper:
        tts.load_model()
        tts.load_model()
    piper.load.assert_called_once()


def test_tts_load_model_import_error() -> None:
    mock_piper = MagicMock()
    mock_piper.load.side_effect = ImportError("no module")
    tts = TextToSpeech()
    with patch("piper.PiperVoice", mock_piper):
        with pytest.raises(TTSError, match="piper-tts nao disponivel"):
            tts.load_model()


def test_tts_load_model_generic_error() -> None:
    mock_piper = MagicMock()
    mock_piper.load.side_effect = RuntimeError("boom")
    tts = TextToSpeech()
    with patch("piper.PiperVoice", mock_piper):
        with pytest.raises(TTSError, match="Nao foi possivel carregar o modelo TTS"):
            tts.load_model()


# ---------------------------------------------------------------------------
# synthesize
# ---------------------------------------------------------------------------


def test_tts_synthesize_success(tmp_path: Path) -> None:
    fake_engine = MagicMock()
    tts = TextToSpeech(output_dir=str(tmp_path / "out"))
    tts._engine = fake_engine
    tts._is_loaded = True

    fake_wave = MagicMock()
    fake_wave_file = MagicMock()
    fake_wave.open.return_value.__enter__.return_value = fake_wave_file

    output_file = tmp_path / "out" / "tts_test.wav"
    with patch.dict("sys.modules", {"wave": fake_wave}):
        resultado = tts.synthesize("Olá mundo", output_file=str(output_file))

    assert resultado == str(output_file)
    fake_engine.synthesize_wav.assert_called_once()


def test_tts_synthesize_auto_filename(tmp_path: Path) -> None:
    fake_engine = MagicMock()
    tts = TextToSpeech(output_dir=str(tmp_path / "out"))
    tts._engine = fake_engine
    tts._is_loaded = True

    fake_wave = MagicMock()
    fake_wave_file = MagicMock()
    fake_wave.open.return_value.__enter__.return_value = fake_wave_file

    with patch.dict("sys.modules", {"wave": fake_wave}):
        resultado = tts.synthesize("texto qualquer")

    assert resultado.endswith(".wav")
    fake_engine.synthesize_wav.assert_called_once()


def test_tts_synthesize_empty_text() -> None:
    tts = TextToSpeech()
    fake_engine = MagicMock()
    tts._engine = fake_engine
    tts._is_loaded = True

    with pytest.raises(TTSError, match="Texto vazio nao pode ser sintetizado"):
        tts.synthesize("")
    with pytest.raises(TTSError, match="Texto vazio nao pode ser sintetizado"):
        tts.synthesize("   ")


def test_tts_synthesize_model_not_loaded() -> None:
    tts = TextToSpeech()
    with patch.object(tts, "load_model"):
        with pytest.raises(TTSError, match="Modelo TTS nao carregado"):
            tts.synthesize("qualquer coisa")


# ---------------------------------------------------------------------------
# synthesize_and_play
# ---------------------------------------------------------------------------


def test_tts_synthesize_and_play_success(tmp_path: Path) -> None:
    fake_engine = MagicMock()
    tts = TextToSpeech(output_dir=str(tmp_path / "out"))
    tts._engine = fake_engine
    tts._is_loaded = True

    fake_sd = MagicMock()
    fake_sf = MagicMock()
    fake_sf.read.return_value = ([0.0] * 100, 16000)
    fake_wave = MagicMock()
    fake_wave_file = MagicMock()
    fake_wave.open.return_value.__enter__.return_value = fake_wave_file

    with patch.dict(
        "sys.modules",
        {"sounddevice": fake_sd, "soundfile": fake_sf, "wave": fake_wave},
    ):
        tts.synthesize_and_play("Ola")
    fake_sd.play.assert_called_once()
    fake_sd.wait.assert_called_once()


def test_tts_synthesize_and_play_error() -> None:
    tts = TextToSpeech()
    fake_engine = MagicMock()
    tts._engine = fake_engine
    tts._is_loaded = True

    fake_sd = MagicMock()
    fake_sd.play.side_effect = RuntimeError("boom")
    fake_sf = MagicMock()
    fake_sf.read.return_value = ([0.0] * 100, 16000)

    with patch.dict("sys.modules", {"sounddevice": fake_sd, "soundfile": fake_sf}):
        with pytest.raises(TTSError, match="Falha ao reproduzir fala"):
            tts.synthesize_and_play("qualquer")


# ---------------------------------------------------------------------------
# TTSError
# ---------------------------------------------------------------------------


def test_tts_error_is_exception() -> None:
    err = TTSError("falha")
    assert isinstance(err, Exception)
    assert str(err) == "falha"