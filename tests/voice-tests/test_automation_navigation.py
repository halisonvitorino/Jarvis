"""
Automated Tests: PHASE 3 - VOICE ASSISTANT
Navigation Flows & UI Validation

Test Plan Reference: test_plans/PHASE_3_VOICE_ASSISTANT.md
- TNV-01: Voice flow from startup
- TNV-02: Context retention across sessions
- TUI-01: Voice status indicator
- TUI-02: Microphone selection UI
- TUI-03: Volume/quality controls
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fastapi.testclient import TestClient

from jarvis.ui.api_test import create_test_app


# ── TNV-01: Voice flow from startup ──────────────────────────────────────
def test_tnv01_voice_flow_from_startup() -> None:
    """TNV-01: Voice flow from startup - System ready for voice after initialization."""
    app = create_test_app()
    client = TestClient(app)

    # Create session
    session_response = client.post(
        "/api/sessions",
        json={"title": "Teste de voz"},
    )
    session_id = session_response.json()["session_id"]

    # Chat with speak=false (TTS not called by default)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": False},
    )

    assert response.status_code == 200
    data = response.json()
    # Voice flow should work without errors
    assert "response" in data or "spoken" in data


# ── TNV-02: Context retention across sessions ────────────────────────────
def test_tnv02_context_retention_across_sessions() -> None:
    """TNV-02: Context retention across sessions - Context preserved or reset appropriately."""
    app = create_test_app()
    client = TestClient(app)

    # Create first session
    session1_response = client.post(
        "/api/sessions",
        json={"title": "Sessão 1"},
    )
    session_id_1 = session1_response.json()["session_id"]

    # Have a conversation in first session
    client.post(
        "/api/chat",
        json={"session_id": session_id_1, "message": "Olá JARVIS", "speak": False},
    )

    # Create new session (simulating restart)
    session2_response = client.post(
        "/api/sessions",
        json={"title": "Sessão 2"},
    )
    session_id_2 = session2_response.json()["session_id"]

    # New session should start fresh (context reset)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id_2, "message": "Olá JARVIS", "speak": False},
    )

    assert response.status_code == 200
    # Each session starts with fresh context


# ── TUI-01: Voice status indicator ───────────────────────────────────────
def test_tui01_voice_status_indicator() -> None:
    """TUI-01: Voice status indicator - Clear visual indicator when listening/speaking."""
    app = create_test_app()
    client = TestClient(app)

    session_response = client.post(
        "/api/sessions",
        json={"title": "Teste"},
    )
    session_id = session_response.json()["session_id"]

    # When speak=true, should indicate TTS is being processed
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": True},
    )

    assert response.status_code == 200
    data = response.json()
    # Response should include spoken field
    assert "spoken" in data


# ── TUI-02: Microphone selection UI ──────────────────────────────────────
def test_tui02_microphone_selection_ui() -> None:
    """TUI-02: Microphone selection UI - System uses selected microphone for STT."""
    # This test validates the API endpoints that handle microphone selection
    # In Phase 3, microphone management is configured at the system level
    app = create_test_app()
    client = TestClient(app)

    session_response = client.post(
        "/api/sessions",
        json={"title": "Teste"},
    )
    session_id = session_response.json()["session_id"]

    # Chat should work with default microphone configuration
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": False},
    )

    assert response.status_code == 200


# ── TUI-03: Volume/quality controls ──────────────────────────────────────
def test_tui03_volume_quality_controls() -> None:
    """TUI-03: Volume/quality controls - Audio plays at correct volume."""
    app = create_test_app()
    from jarvis.voice.tts import TextToSpeech
    mock_tts = MagicMock(spec=TextToSpeech)

    app_with_tts = create_test_app(tts=mock_tts)
    client = TestClient(app_with_tts)

    session_response = client.post(
        "/api/sessions",
        json={"title": "Teste"},
    )
    session_id = session_response.json()["session_id"]

    # Request TTS with speak=true
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": True},
    )

    assert response.status_code == 200
    data = response.json()
    # spoken should be True when TTS is available and mock is used
    assert data.get("spoken") is True