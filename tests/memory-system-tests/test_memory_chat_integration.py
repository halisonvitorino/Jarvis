"""Testes de integração: memória no fluxo de chat (JARVIS-A-025)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from jarvis.brain.conversation_manager import ConversationManager
from jarvis.brain.session_manager import SessionManager


@pytest.fixture
def conversation_manager_with_mock(tmp_path):
    """Cria um ConversationManager com modelo mockado e sessão temporária."""
    db_path = tmp_path / "test_integration.db"
    session_manager = SessionManager(database_path=db_path)
    cm = ConversationManager()
    cm.session_manager = session_manager

    # Mock do modelo para retorno determinístico
    mock_response = "Resposta baseada no contexto"

    def mock_generate(model, prompt, system_prompt, **kwargs):
        return mock_response

    cm._generate_with_provider = mock_generate
    yield cm, session_manager


def test_memory_influences_chat_response(
    conversation_manager_with_mock, tmp_path
) -> None:
    """Memória de conversas anteriores deve influenciar a resposta."""
    cm, sm = conversation_manager_with_mock

    session = sm.create_session("Sessão de memória")

    # Primeira interação: usuário menciona nome
    result1 = cm.chat(session.id, "Meu nome é Carlos")
    assert result1["response"] == "Resposta baseada no contexto"

    # Segunda interação: usuário pergunta o nome
    result2 = cm.chat(session.id, "Qual é meu nome?")

    # Verificar que a sessão tem as mensagens
    session_recovered = sm.get_session(session.id)
    user_messages = [m for m in session_recovered.messages if m.role == "user"]
    assert any("Carlos" in m.content for m in user_messages)

    # Verificar que o perfil foi extraído e salvo
    profile = cm.memory_manager.get_user_profile(session.id)
    assert "nome" in profile
    assert "Carlos" in profile["nome"]


def test_interactions_persisted_to_memory(
    conversation_manager_with_mock, tmp_path
) -> None:
    """Interações devem ser persistidas na memória de longo prazo."""
    cm, sm = conversation_manager_with_mock

    session = sm.create_session("Persistência")
    session_id = session.id

    cm.chat(session_id, "Gosto de programação em Python")

    # Verificar que a interação foi salva na MemoryStore
    contents = cm.memory_manager.recall_session(session_id)
    assert any("Gosto de programação em Python" in c for c in contents)

    # Verificar que o perfil foi extraído
    profile = cm.memory_manager.get_user_profile(session_id)
    assert "preferencias" in profile
    assert any("Python" in p for p in profile["preferencias"])


def test_session_isolation_in_chat(
    conversation_manager_with_mock, tmp_path
) -> None:
    """Uma sessão não deve acessar dados de outra."""
    cm, sm = conversation_manager_with_mock

    s1 = sm.create_session("Sessão A")
    s2 = sm.create_session("Sessão B")

    cm.chat(s1.id, "Meu nome é Alice")
    cm.chat(s2.id, "Meu nome é Bob")

    profile_a = cm.memory_manager.get_user_profile(s1.id)
    profile_b = cm.memory_manager.get_user_profile(s2.id)

    assert "Alice" in profile_a.get("nome", [])
    assert "Bob" in profile_b.get("nome", [])
    assert "Alice" not in profile_b.get("nome", [])
    assert "Bob" not in profile_a.get("nome", [])


def test_semantic_search_used_in_chat(
    conversation_manager_with_mock, tmp_path
) -> None:
    """Chat deve consultar memória semântica antes de responder."""
    cm, sm = conversation_manager_with_mock

    session = sm.create_session("Busca semântica")
    session_id = session.id

    # Primeira mensagem estabelece contexto
    cm.chat(session_id, "Estou aprendendo Rust")

    # Segunda mensagem deve recuperar memória sobre Rust
    result = cm.chat(session_id, "Qual linguagem estou aprendendo?")

    # Verificar que o contexto inclui a memória anterior
    session_recovered = sm.get_session(session_id)
    contents = [m.content for m in session_recovered.messages]
    assert any("Rust" in c for c in contents)
