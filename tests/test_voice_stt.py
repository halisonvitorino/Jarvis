"""Testes do módulo Speech-to-Text (STT) - Phase 3.

Todos os testes usam mocks; não dependem de microfone, modelo Whisper real
nem hardware de áudio.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import SpeechToText, STTError


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------


def test_stt_default_values() -> None:
    stt = SpeechToText()
    assert stt.model_size == "base"
    assert stt.language is None
    assert stt.compute_type == "int8"
    assert stt._is_loaded is False
    assert stt._model is None


def test_stt_custom_values() -> None:
    stt = SpeechToText(model_size="small", language="pt", compute_type="float16")
    assert stt.model_size == "small"
    assert stt.language == "pt"
    assert stt.compute_type == "float16"


# ---------------------------------------------------------------------------
# load_model
# ---------------------------------------------------------------------------


def test_stt_load_model_success() -> None:
    fake_model = MagicMock()
    stt = SpeechToText()
    with patch("faster_whisper.WhisperModel", return_value=fake_model):
        stt.load_model()
    assert stt._is_loaded is True
    assert stt._model is fake_model


def test_stt_load_model_idempotent() -> None:
    fake_model = MagicMock()
    stt = SpeechToText()
    with patch("faster_whisper.WhisperModel", return_value=fake_model) as whisp:
        stt.load_model()
        stt.load_model()
    whisp.assert_called_once()


def test_stt_load_model_import_error() -> None:
    stt = SpeechToText()
    with patch("faster_whisper.WhisperModel", side_effect=ImportError("no module")):
        with pytest.raises(STTError, match="faster-whisper nao disponivel"):
            stt.load_model()


def test_stt_load_model_generic_error() -> None:
    stt = SpeechToText()
    with patch("faster_whisper.WhisperModel", side_effect=RuntimeError("boom")):
        with pytest.raises(STTError, match="Nao foi possivel carregar o modelo STT"):
            stt.load_model()


# ---------------------------------------------------------------------------
# transcribe
# ---------------------------------------------------------------------------


def test_stt_transcribe_success() -> None:
    fake_model = MagicMock()
    seg1 = SimpleNamespace(text="Olá")
    seg2 = SimpleNamespace(text="mundo")
    fake_model.transcribe.return_value = ([seg1, seg2], None)

    stt = SpeechToText()
    stt._model = fake_model
    stt._is_loaded = True

    texto = stt.transcribe("qualquer.wav")
    assert texto == "Olá mundo"
    fake_model.transcribe.assert_called_once()


def test_stt_transcribe_model_not_loaded() -> None:
    stt = SpeechToText()
    stt._is_loaded = False
    stt._model = None
    with patch.object(stt, "load_model"):
        with pytest.raises(STTError, match="Modelo STT nao carregado"):
            stt.transcribe("qualquer.wav")


def test_stt_transcribe_from_bytes_success() -> None:
    fake_model = MagicMock()
    seg1 = SimpleNamespace(text="texto")
    fake_model.transcribe.return_value = ([seg1], None)

    stt = SpeechToText()
    stt._model = fake_model
    stt._is_loaded = True

    fake_sf = MagicMock()
    fake_sf.read.return_value = ([0.0] * 100, 16000)

    with patch.dict("sys.modules", {"soundfile": fake_sf}):
        texto = stt.transcribe_from_bytes(b"fake-wav-bytes")

    assert texto == "texto"
    fake_model.transcribe.assert_called_once()


def test_stt_transcribe_from_bytes_sample_rate_warning() -> None:
    fake_model = MagicMock()
    seg1 = SimpleNamespace(text="texto")
    fake_model.transcribe.return_value = ([seg1], None)

    stt = SpeechToText()
    stt._model = fake_model
    stt._is_loaded = True

    fake_sf = MagicMock()
    fake_sf.read.return_value = ([0.0] * 100, 8000)

    with patch.dict("sys.modules", {"soundfile": fake_sf}):
        texto = stt.transcribe_from_bytes(b"bytes", sample_rate=16000)

    assert texto == "texto"


# ---------------------------------------------------------------------------
# STTError
# ---------------------------------------------------------------------------


def test_stt_error_is_exception() -> None:
    err = STTError("falha")
    assert isinstance(err, Exception)
    assert str(err) == "falha"