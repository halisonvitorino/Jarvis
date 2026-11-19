"""Testes do modulo Wake Word detection.

Valida deteccao de palavras-chave, configuracao de sensibilidade
e integracao com o motor STT.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import STTError, SpeechToText
from jarvis.voice.wake_word import WakeWordDetector, WakeWordError


class TestWakeWordDetectorInit:
    """Testes de inicializacao do detector."""

    def test_init_defaults(self) -> None:
        detector = WakeWordDetector()
        assert detector.wake_words == ["jarvis"]
        assert detector.sensitivity == 0.8
        assert isinstance(detector.stt, SpeechToText)
        assert detector._is_listening is False
        assert detector._callback is None

    def test_init_custom_params(self) -> None:
        stt = SpeechToText()
        detector = WakeWordDetector(
            wake_words=["jarvis", "hermes"], stt=stt, sensitivity=0.9
        )
        assert detector.wake_words == ["jarvis", "hermes"]
        assert detector.stt is stt
        assert detector.sensitivity == 0.9

    def test_init_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        with caplog.at_level(logging.INFO, logger="jarvis.voice.wake_word"):
            WakeWordDetector(wake_words=["jarvis"])
        assert "WakeWordDetector inicializado" in caplog.text


class TestWakeWordDetectorCallback:
    """Testes de configuracao de callback."""

    def test_set_callback(self) -> None:
        detector = WakeWordDetector()
        callback = MagicMock()
        detector.set_callback(callback)
        assert detector._callback is callback

    def test_set_callback_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        detector = WakeWordDetector()
        with caplog.at_level(logging.DEBUG, logger="jarvis.voice.wake_word"):
            detector.set_callback(MagicMock())
        assert "Callback de wake word definido" in caplog.text


class TestWakeWordDetectorListening:
    """Testes de controle de escuta."""

    def test_start_listening_without_callback_raises(self) -> None:
        detector = WakeWordDetector()
        with pytest.raises(WakeWordError, match="Callback nao definido"):
            detector.start_listening()
        assert detector._is_listening is False

    def test_start_listening_success(self) -> None:
        detector = WakeWordDetector()
        detector.set_callback(MagicMock())
        detector.start_listening()
        assert detector._is_listening is True

    def test_start_listening_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        detector = WakeWordDetector()
        detector.set_callback(MagicMock())
        with caplog.at_level(logging.INFO, logger="jarvis.voice.wake_word"):
            detector.start_listening()
        assert "Escuta de wake word iniciada" in caplog.text

    def test_stop_listening(self) -> None:
        detector = WakeWordDetector()
        detector._is_listening = True
        detector.stop_listening()
        assert detector._is_listening is False

    def test_stop_listening_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        detector = WakeWordDetector()
        with caplog.at_level(logging.DEBUG, logger="jarvis.voice.wake_word"):
            detector.stop_listening()
        assert "Escuta de wake word parada" in caplog.text


class TestCheckWakeWord:
    """Testes de deteccao de palavra-chave."""

    def test_detects_default_word(self) -> None:
        detector = WakeWordDetector()
        detector._is_listening = True
        callback = MagicMock()
        detector.set_callback(callback)
        assert detector.check_wake_word("Jarvis, que horas sao?") is True
        callback.assert_called_once()

    def test_detects_custom_word(self) -> None:
        detector = WakeWordDetector(wake_words=["hermes"])
        detector._is_listening = True
        callback = MagicMock()
        detector.set_callback(callback)
        assert detector.check_wake_word("Hermes, me ajude") is True
        callback.assert_called_once()

    def test_no_match_returns_false(self) -> None:
        detector = WakeWordDetector()
        detector._is_listening = True
        callback = MagicMock()
        detector.set_callback(callback)
        assert detector.check_wake_word("Hoje o tempo esta bom") is False
        callback.assert_not_called()

    def test_empty_text_returns_false(self) -> None:
        detector = WakeWordDetector()
        detector._is_listening = True
        assert detector.check_wake_word("") is False

    def test_not_listening_returns_false(self) -> None:
        detector = WakeWordDetector()
        callback = MagicMock()
        detector.set_callback(callback)
        assert detector.check_wake_word("Jarvis") is False
        callback.assert_not_called()

    def test_case_insensitive(self) -> None:
        detector = WakeWordDetector(wake_words=["jarvis"])
        detector._is_listening = True
        assert detector.check_wake_word("JARVIS aqui") is True


class TestProcessAudio:
    """Testes de processamento de audio para wake word."""

    def test_process_audio_success(self) -> None:
        stt = MagicMock(spec=SpeechToText)
        stt.transcribe.return_value = "Jarvis, me diga oi"
        detector = WakeWordDetector(stt=stt)
        detector._is_listening = True
        callback = MagicMock()
        detector.set_callback(callback)
        result = detector.process_audio("audio.wav")
        assert result == "Jarvis, me diga oi"
        stt.transcribe.assert_called_once_with("audio.wav")

    def test_process_audio_no_wake_word(self) -> None:
        stt = MagicMock(spec=SpeechToText)
        stt.transcribe.return_value = "So um commentario"
        detector = WakeWordDetector(stt=stt)
        detector._is_listening = True
        result = detector.process_audio("audio.wav")
        assert result is None

    def test_process_audio_no_stt_raises(self) -> None:
        detector = WakeWordDetector()
        detector.stt = None
        with pytest.raises(WakeWordError, match="Motor STT nao disponivel"):
            detector.process_audio("audio.wav")

    def test_process_audio_stt_failure_wraps_error(self) -> None:
        stt = MagicMock(spec=SpeechToText)
        stt.transcribe.side_effect = STTError("fail")
        detector = WakeWordDetector(stt=stt)
        detector._is_listening = True
        with pytest.raises(WakeWordError, match="Falha ao processar audio"):
            detector.process_audio("audio.wav")

    def test_process_audio_logs_detection(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        stt = MagicMock(spec=SpeechToText)
        stt.transcribe.return_value = "Jarvis aqui"
        detector = WakeWordDetector(stt=stt)
        detector._is_listening = True
        with caplog.at_level(logging.INFO, logger="jarvis.voice.wake_word"):
            detector.process_audio("audio.wav")
        assert "Wake word detectada" in caplog.text