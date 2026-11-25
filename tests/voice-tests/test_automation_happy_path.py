"""
Automated Tests: PHASE 3 - VOICE ASSISTANT
Happy Path Scenarios

Test Plan Reference: test_plans/PHASE_3_VOICE_ASSISTANT.md
- TP-01: Basic voice interaction
- TP-02: Multi-turn conversation
- TP-03: Command recognition
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.voice.stt import SpeechToText, STTError
from jarvis.voice.tts import TextToSpeech, TTSError
from jarvis.voice.voice_conversation import VoiceConversation, VoiceConversationError


# ── TP-01: Basic voice interaction ───────────────────────────────────────
def test_tp01_basic_voice_interaction() -> None:
    """TP-01: Basic voice interaction - Wake word → simple command → TTS response."""
    # Mock the STT, TTS, and wake word components
    cm = MagicMock()
    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()

    # STT returns a simple command
    stt.transcribe.return_value = "Que horas são"

    # TTS synthesize_and_play is mocked
    vc = VoiceConversation(
        conversation_manager=cm,
        stt=stt,
        tts=tts,
        wake_word=ww,
        auto_wake=False,
    )

    # Activate conversation and process voice input
    vc._is_active = True
    resultado = vc.process_voice_input("comando.wav")

    # Assert: TTS should be called with the response
    tts.synthesize_and_play.assert_called_once()
    # Verify the result is not None (TTS was called)
    assert resultado is not None


# ── TP-03: Command recognition ────────────────────────────────────────────
def test_tp03_command_recognition() -> None:
    """TP-03: Command recognition - Say 'What time is it' → system responds."""
    cm = MagicMock()
    cm.chat.return_value = {"response": "São 15h30min", "model": "gemini"}

    stt = MagicMock()
    stt.transcribe.return_value = "Que horas são"

    tts = MagicMock()

    ww = MagicMock()

    vc = VoiceConversation(
        conversation_manager=cm,
        stt=stt,
        tts=tts,
        wake_word=ww,
        auto_wake=False,
    )

    vc._is_active = True
    resposta = vc.process_voice_input("comando.wav")

    # Assert: Correct time information provided
    cm.chat.assert_called_once()
    tts.synthesize_and_play.assert_called_once_with("São 15h30min")
    assert "15" in str(resposta) or "horas" in str(resposta).lower()


# ── TP-02: Multi-turn conversation ────────────────────────────────────────
def test_tp02_multi_turn_conversation() -> None:
    """TP-02: Multi-turn conversation - Natural flow without repeated wake word."""
    cm = MagicMock()

    stt = MagicMock()
    tts = MagicMock()
    ww = MagicMock()

    # First interaction
    stt.transcribe.return_value = "Ligar luz"
    cm.chat.return_value = {"response": "Luz ligada", "model": "gemini"}

    vc = VoiceConversation(
        conversation_manager=cm,
        stt=stt,
        tts=tts,
        wake_word=ww,
        auto_wake=True,
    )

    vc._is_active = True

    # First command (wake word already activated)
    vc.process_voice_input("ligar luz.wav")

    # Second command (no need to repeat wake word)
    stt.transcribe.return_value = "Desligar luz"
    cm.chat.return_value = {"response": "Luz desligada", "model": "gemini"}

    vc.process_voice_input("desligar luz.wav")

    # Assert: Two commands processed in sequence without repeating wake word
    assert stt.transcribe.call_count == 2
    assert cm.chat.call_count == 2
    assert tts.synthesize_and_play.call_count == 2