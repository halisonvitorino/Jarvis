"""Testes do modulo de conversa por voz.

Valida integracao entre STT, TTS, Wake Word e ConversationManager,
com mocks para todos os motores de voz.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import STTError
from jarvis.voice.tts import TTSError
from jarvis.voice.voice_conversation import VoiceConversation, VoiceConversationError


class _MockConversationManager:
    """Mock do ConversationManager com injectavel behavior."""

    def __init__(self, response: str = "resposta", raise_exc: Exception | None = None) -> None:
        self._response = response
        self._raise_exc = raise_exc
        self.chat = MagicMock(return_value={"response": self._response, "session_id": "voice_session"})
        if raise_exc is not None:
            self.chat.side_effect = raise_exc


class TestVoiceConversationInit:
    """Testes de inicializacao do VoiceConversation."""

    def test_init_defaults(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        assert vc.conversation_manager is manager
        assert vc.auto_wake is False
        assert vc._is_active is False

    def test_init_custom(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(
            conversation_manager=manager,
            auto_wake=True,
        )
        assert vc.auto_wake is True

    def test_init_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        manager = _MockConversationManager()
        with caplog.at_level(logging.INFO, logger="jarvis.voice.voice_conversation"):
            VoiceConversation(conversation_manager=manager, auto_wake=True)
        assert "VoiceConversation inicializado" in caplog.text


class TestVoiceConversationStartStop:
    """Testes de controle de inicio e parada."""

    def test_start_loads_models(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        with patch.object(vc.stt, "load_model") as mock_stt_load, patch.object(
            vc.tts, "load_model"
        ) as mock_tts_load:
            vc.start()
        mock_stt_load.assert_called_once()
        mock_tts_load.assert_called_once()
        assert vc._is_active is True

    def test_start_failure_wraps_error(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        with patch.object(vc.stt, "load_model", side_effect=STTError("fail")):
            with pytest.raises(VoiceConversationError, match="Nao foi iniciar conversa"):
                vc.start()
        assert vc._is_active is False

    def test_start_tts_failure_wraps_error(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        with patch.object(vc.stt, "load_model"), patch.object(
            vc.tts, "load_model", side_effect=TTSError("fail")
        ):
            with pytest.raises(VoiceConversationError, match="Nao foi iniciar conversa"):
                vc.start()

    def test_stop(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        vc.wake_word._is_listening = True
        vc.stop()
        assert vc._is_active is False
        assert vc.wake_word._is_listening is False

    def test_stop_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with caplog.at_level(logging.INFO, logger="jarvis.voice.voice_conversation"):
            vc.stop()
        assert "Conversa por voz parada" in caplog.text

    def test_start_auto_wake_configures_callback(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager, auto_wake=True)
        with patch.object(vc.stt, "load_model"), patch.object(vc.tts, "load_model"):
            vc.start()
        assert vc.wake_word._callback is vc._on_wake_word
        assert vc.wake_word._is_listening is True


class TestProcessVoiceInput:
    """Testes de processamento de entrada de voz."""

    def test_process_voice_input_success(self) -> None:
        manager = _MockConversationManager(response="Olá, tudo bem?")
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with patch.object(vc.stt, "transcribe", return_value="Oi, fala comigo"), patch.object(
            vc.tts, "synthesize_and_play"
        ) as mock_play:
            result = vc.process_voice_input("audio.wav")
        assert result == "Olá, tudo bem?"
        vc.stt.transcribe.assert_called_once_with("audio.wav")
        manager.chat.assert_called_once_with(
            session_id="voice_session", message="Oi, fala comigo"
        )
        mock_play.assert_called_once_with("Olá, tudo bem?")

    def test_process_voice_input_not_active_raises(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        with pytest.raises(VoiceConversationError, match="nao esta ativa"):
            vc.process_voice_input("audio.wav")

    def test_process_voice_input_stt_failure_wraps_error(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with patch.object(vc.stt, "transcribe", side_effect=STTError("fail")):
            with pytest.raises(VoiceConversationError, match="Falha no processamento de voz"):
                vc.process_voice_input("audio.wav")

    def test_process_voice_input_tts_failure_wraps_error(self) -> None:
        manager = _MockConversationManager()
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with patch.object(vc.stt, "transcribe", return_value="oi"), patch.object(
            vc.tts, "synthesize_and_play", side_effect=TTSError("fail")
        ):
            with pytest.raises(VoiceConversationError, match="Falha no processamento de voz"):
                vc.process_voice_input("audio.wav")

    def test_process_voice_input_empty_response(self) -> None:
        manager = _MockConversationManager(response="")
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with patch.object(vc.stt, "transcribe", return_value="oi"), patch.object(
            vc.tts, "synthesize_and_play"
        ) as mock_play:
            result = vc.process_voice_input("audio.wav")
        assert result == ""
        mock_play.assert_called_once_with("")

    def test_process_voice_input_logs_user_text(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        manager = _MockConversationManager(response="ok")
        vc = VoiceConversation(conversation_manager=manager)
        vc._is_active = True
        with patch.object(vc.stt, "transcribe", return_value="oi"), patch.object(
            vc.tts, "synthesize_and_play"
        ), caplog.at_level(logging.DEBUG, logger="jarvis.voice.voice_conversation"):
            vc.process_voice_input("audio.wav")
        assert "Usuario disse: oi" in caplog.text