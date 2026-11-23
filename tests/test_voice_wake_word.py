"""Testes do módulo Wake Word detection - Phase 3.

Todos os testes usam mocks; não dependem de áudio real nem STT verdadeiro.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from jarvis.voice.stt import STTError
from jarvis.voice.wake_word import WakeWordDetector, WakeWordError


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------


def test_wake_word_default_values() -> None:
    wwd = WakeWordDetector()
    assert wwd.wake_words == ["jarvis"]
    assert wwd.sensitivity == 0.8
    assert wwd._is_listening is False
    assert wwd._callback is None
    assert isinstance(wwd.stt, MagicMock) is False  # SpeechToText real (não carregado)


def test_wake_word_custom_values() -> None:
    stt = MagicMock()
    wwd = WakeWordDetector(wake_words=["hermes", "jarvis"], stt=stt, sensitivity=0.5)
    assert wwd.wake_words == ["hermes", "jarvis"]
    assert wwd.sensitivity == 0.5
    assert wwd.stt is stt


# ---------------------------------------------------------------------------
# callback / escuta
# ---------------------------------------------------------------------------


def test_set_callback() -> None:
    wwd = WakeWordDetector()
    chamado = []

    def cb(text: str) -> None:
        chamado.append(text)

    wwd.set_callback(cb)
    assert wwd._callback is cb


def test_start_listening_without_callback_raises() -> None:
    wwd = WakeWordDetector()
    with pytest.raises(WakeWordError, match="Callback nao definido"):
        wwd.start_listening()


def test_start_listening_success() -> None:
    wwd = WakeWordDetector()
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    assert wwd._is_listening is True


def test_stop_listening() -> None:
    wwd = WakeWordDetector()
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    wwd.stop_listening()
    assert wwd._is_listening is False


# ---------------------------------------------------------------------------
# check_wake_word
# ---------------------------------------------------------------------------


def test_check_wake_word_detects() -> None:
    wwd = WakeWordDetector(wake_words=["jarvis"])
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    assert wwd.check_wake_word("E ai, jarvis") is True


def test_check_wake_word_case_insensitive() -> None:
    wwd = WakeWordDetector(wake_words=["JARVIS"])
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    assert wwd.check_wake_word("jarvis, você aí?") is True


def test_check_wake_word_not_detected() -> None:
    wwd = WakeWordDetector(wake_words=["jarvis"])
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    assert wwd.check_wake_word("Olá mundo") is False


def test_check_wake_word_not_listening() -> None:
    wwd = WakeWordDetector(wake_words=["jarvis"])
    wwd.set_callback(lambda t: None)
    # não chama start_listening
    assert wwd.check_wake_word("jarvis") is False


def test_check_wake_word_empty_text() -> None:
    wwd = WakeWordDetector(wake_words=["jarvis"])
    wwd.set_callback(lambda t: None)
    wwd.start_listening()
    assert wwd.check_wake_word("") is False
    assert wwd.check_wake_word("   ") is False


def test_check_wake_word_invokes_callback() -> None:
    wwd = WakeWordDetector(wake_words=["jarvis"])
    eventos = []
    wwd.set_callback(lambda t: eventos.append(t))
    wwd.start_listening()
    wwd.check_wake_word("jarvis ligue a luz")
    assert eventos == ["jarvis ligue a luz"]


# ---------------------------------------------------------------------------
# process_audio
# ---------------------------------------------------------------------------


def test_process_audio_wake_word_detected() -> None:
    stt = MagicMock()
    stt.transcribe.return_value = "jarvis, acorde"
    wwd = WakeWordDetector(wake_words=["jarvis"], stt=stt)
    wwd.set_callback(lambda t: None)
    wwd.start_listening()

    resultado = wwd.process_audio("qualquer.wav")
    assert resultado == "jarvis, acorde"
    stt.transcribe.assert_called_once_with("qualquer.wav")


def test_process_audio_no_wake_word() -> None:
    stt = MagicMock()
    stt.transcribe.return_value = "olá mundo"
    wwd = WakeWordDetector(wake_words=["jarvis"], stt=stt)
    wwd.set_callback(lambda t: None)
    wwd.start_listening()

    resultado = wwd.process_audio("qualquer.wav")
    assert resultado is None


def test_process_audio_stt_error() -> None:
    stt = MagicMock()
    stt.transcribe.side_effect = STTError("falha na transcricao")
    wwd = WakeWordDetector(wake_words=["jarvis"], stt=stt)
    wwd.set_callback(lambda t: None)
    wwd.start_listening()

    with pytest.raises(WakeWordError, match="Falha ao processar audio para wake word"):
        wwd.process_audio("qualquer.wav")


# ---------------------------------------------------------------------------
# WakeWordError
# ---------------------------------------------------------------------------


def test_wake_word_error_is_exception() -> None:
    err = WakeWordError("falha")
    assert isinstance(err, Exception)
    assert str(err) == "falha"