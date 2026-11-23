"""Testes da opção "Falar resposta" na API de chat - Phase 3.

Valida que o campo `speak` da requisição /api/chat aciona o TTS quando
disponível e retorna o campo `spoken` na resposta, sem quebrar o fluxo
quando o TTS não está configurado ou falha.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from jarvis.ui.api_test import create_test_app


def _create_session(client: TestClient, title: str = "Sessão de teste") -> str:
    """Cria uma sessão de teste e retorna o session_id gerado."""
    response = client.post(
        "/api/sessions",
        json={"title": title},
    )
    assert response.status_code == 200, f"Falha ao criar sessão: {response.text}"
    return response.json()["session_id"]


@pytest.fixture
def app_without_tts() -> TestClient:
    return TestClient(create_test_app())


@pytest.fixture
def app_with_tts() -> tuple[TestClient, MagicMock]:
    mock_tts = MagicMock()
    return TestClient(create_test_app(tts=mock_tts)), mock_tts


# ---------------------------------------------------------------------------
# speak=false (default) — TTS não deve ser chamado
# ---------------------------------------------------------------------------


def test_chat_speak_false_returns_spoken_false(app_without_tts: TestClient) -> None:
    client = app_without_tts
    session_id = _create_session(client)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spoken"] is False
    assert data["response"]  # texto ainda entregue


def test_chat_speak_omitted_defaults_false(app_without_tts: TestClient) -> None:
    client = app_without_tts
    session_id = _create_session(client)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spoken"] is False


# ---------------------------------------------------------------------------
# speak=true com TTS disponível — TTS deve ser chamado
# ---------------------------------------------------------------------------


def test_chat_speak_true_calls_tts(app_with_tts: tuple[TestClient, MagicMock]) -> None:
    client, mock_tts = app_with_tts
    session_id = _create_session(client)
    mock_tts.synthesize_and_play.return_value = None
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spoken"] is True
    mock_tts.synthesize_and_play.assert_called_once()


# ---------------------------------------------------------------------------
# speak=true sem TTS configurado — não quebra, spoken=false
# ---------------------------------------------------------------------------


def test_chat_speak_true_without_tts(app_without_tts: TestClient) -> None:
    client = app_without_tts
    session_id = _create_session(client)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spoken"] is False
    assert data["response"]  # texto ainda entregue


# ---------------------------------------------------------------------------
# speak=true com TTS com erro — não quebra, spoken=false
# ---------------------------------------------------------------------------


def test_chat_speak_true_tts_error() -> None:
    from jarvis.voice.tts import TTSError

    mock_tts = MagicMock()
    mock_tts.synthesize_and_play.side_effect = TTSError("falha de áudio")
    client = TestClient(create_test_app(tts=mock_tts))
    session_id = _create_session(client)

    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": True},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["spoken"] is False
    assert data["response"]  # texto ainda entregue


# ---------------------------------------------------------------------------
# Validação de schema — speak aceita booleano
# ---------------------------------------------------------------------------


def test_chat_speak_invalid_type(app_without_tts: TestClient) -> None:
    client = app_without_tts
    session_id = _create_session(client)
    response = client.post(
        "/api/chat",
        json={"session_id": session_id, "message": "Olá", "speak": "não é booleano"},
    )
    assert response.status_code == 422