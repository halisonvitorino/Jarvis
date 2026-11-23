"""Testes do módulo VoiceConversation (integração voz + chat) - Phase 3.

Todos os testes usam mocks; não dependem de modelos de voz, microfone nem IA real.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import STTError
from jarvis.voice.tts import TTSError
from jarvis.voice.voice_conversation import VoiceConversation, VoiceConversationError


# ---------------------------------------------------------------------------
# Inicialização
# ---------------------------------------------------------------------------


def test_voice_conversation_defaults() -> None:
    cm = MagicMock()
    vc = VoiceConversation(conversation_manager=cm)
    assert vc.conversation_manager is cm
    assert vc.auto_wake is False
    assert vc._is_active is False
    assert isinstance(vc.stt, MagicMock) is False  # SpeechToText real
    assert isinstance(vc.tts, MagicMock) is False  # TextToSpeech real
    assert isinstance(vc.wake_word, MagicMock) is False  # WakeWordDetector real


def test_voice_conversation_custom() -> None:
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(
        conversation_manager=cm,
        stt=stt,
        tts=tts,
        wake_word=ww,
        auto_wake=True,
    )
    assert vc.stt is stt
    assert vc.tts is tts
    assert vc.wake_word is ww
    assert vc.auto_wake is True


# ---------------------------------------------------------------------------
# start / stop
# ---------------------------------------------------------------------------


def test_start_loads_models() -> None:
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    vc.start()
    stt.load_model.assert_called_once()
    tts.load_model.assert_called_once()
    assert vc._is_active is True


def test_start_auto_wake_registers_callback_and_listens() -> None:
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(
        conversation_manager=cm, stt=stt, tts=tts, wake_word=ww, auto_wake=True
    )
    vc.start()
    ww.set_callback.assert_called_once()
    ww.start_listening.assert_called_once()


def test_start_stt_failure_raises() -> None:
    cm = MagicMock()
    stt = MagicMock()
    stt.load_model.side_effect = STTError("falha stt")
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    with pytest.raises(VoiceConversationError, match="Nao foi possível iniciar conversa por voz"):
        vc.start()


def test_start_tts_failure_raises() -> None:
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    tts.load_model.side_effect = TTSError("falha tts")
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    with pytest.raises(VoiceConversationError, match="Nao foi possível iniciar conversa por voz"):
        vc.start()


def test_stop() -> None:
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    vc._is_active = True
    vc.stop()
    assert vc._is_active is False
    ww.stop_listening.assert_called_once()


# ---------------------------------------------------------------------------
# process_voice_input
# ---------------------------------------------------------------------------


def test_process_voice_input_full_flow() -> None:
    cm = MagicMock()
    cm.chat.return_value = {"response": "Resposta do JARVIS", "model": "gemini"}

    stt = MagicMock()
    stt.transcribe.return_value = "Olá, JARVIS"

    tts = MagicMock()
    tts.synthesize_and_play.return_value = None

    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    vc._is_active = True

    resposta = vc.process_voice_input("comando.wav")

    assert resposta == "Resposta do JARVIS"
    stt.transcribe.assert_called_once_with("comando.wav")
    cm.chat.assert_called_once_with(session_id="voice_session", message="Olá, JARVIS")
    tts.synthesize_and_play.assert_called_once_with("Resposta do JARVIS")


def test_process_voice_input_not_active_raises() -> None:
    cm = MagicMock()
    vc = VoiceConversation(conversation_manager=cm)
    with pytest.raises(VoiceConversationError, match="Conversa por voz nao esta ativa"):
        vc.process_voice_input("comando.wav")


def test_process_voice_input_stt_error() -> None:
    cm = MagicMock()
    stt = MagicMock()
    stt.transcribe.side_effect = STTError("falha stt")
    tts = MagicMock()
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    vc._is_active = True
    with pytest.raises(VoiceConversationError, match="Falha no processamento de voz"):
        vc.process_voice_input("comando.wav")


def test_process_voice_input_tts_error() -> None:
    cm = MagicMock()
    cm.chat.return_value = {"response": "oi"}
    stt = MagicMock()
    stt.transcribe.return_value = "ola"
    tts = MagicMock()
    tts.synthesize_and_play.side_effect = TTSError("falha tts")
    ww = MagicMock()
    vc = VoiceConversation(conversation_manager=cm, stt=stt, tts=tts, wake_word=ww)
    vc._is_active = True
    with pytest.raises(VoiceConversationError, match="Falha no processamento de voz"):
        vc.process_voice_input("comando.wav")


# ---------------------------------------------------------------------------
# VoiceConversationError
# ---------------------------------------------------------------------------


def test_voice_conversation_error_is_exception() -> None:
    err = VoiceConversationError("falha")
    assert isinstance(err, Exception)
    assert str(err) == "falha"