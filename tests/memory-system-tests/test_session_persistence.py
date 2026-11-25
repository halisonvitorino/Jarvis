"""Testes de persistência de sessões (JARVIS-A-024)."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone

import pytest

from jarvis.brain.session_manager import SessionManager


@pytest.fixture
def session_manager(tmp_path):
    """Cria um SessionManager com banco temporário."""
    db_path = tmp_path / "test_sessions.db"
    sm = SessionManager(database_path=db_path)
    yield sm
    shutil.rmtree(tmp_path, ignore_errors=True)


def test_session_persistence_across_instances(session_manager: SessionManager) -> None:
    """Sessão criada deve ser recuperável em nova instância do SessionManager."""
    session = session_manager.create_session("Sessão de teste")
    session_id = session.id

    session_manager.add_message(session_id, "user", "Mensagem 1")
    session_manager.add_message(session_id, "assistant", "Resposta 1")

    # Nova instância deve recuperar a sessão persistida
    sm2 = SessionManager(database_path=session_manager.database_path)
    recovered = sm2.get_session(session_id)

    assert recovered.id == session_id
    assert recovered.title == "Sessão de teste"
    assert len(recovered.messages) == 2
    assert recovered.messages[0].content == "Mensagem 1"
    assert recovered.messages[1].content == "Resposta 1"


def test_session_list_recover_after_restart(session_manager: SessionManager) -> None:
    """list_sessions deve recuperar sessões do banco."""
    session_manager.create_session("Sessão A")
    session_manager.create_session("Sessão B")

    sm2 = SessionManager(database_path=session_manager.database_path)
    sessions = sm2.list_sessions()
    titles = [s.title for s in sessions]
    assert "Sessão A" in titles
    assert "Sessão B" in titles


def test_session_isolation_between_sessions(session_manager: SessionManager) -> None:
    """Sessão A não deve acessar dados da sessão B."""
    s1 = session_manager.create_session("Sessão A")
    s2 = session_manager.create_session("Sessão B")

    session_manager.add_message(s1.id, "user", "Secreto da A")
    session_manager.add_message(s2.id, "user", "Público da B")

    s1_recovered = session_manager.get_session(s1.id)
    s2_recovered = session_manager.get_session(s2.id)

    assert "Secreto da A" in [m.content for m in s1_recovered.messages]
    assert "Secreto da A" not in [m.content for m in s2_recovered.messages]
    assert "Público da B" in [m.content for m in s2_recovered.messages]
    assert "Público da B" not in [m.content for m in s1_recovered.messages]


def test_session_message_order(session_manager: SessionManager) -> None:
    """Mensagens devem manter ordem cronológica."""
    session = session_manager.create_session("Ordem")
    session_id = session.id

    for i in range(5):
        session_manager.add_message(session_id, "user", f"Mensagem {i}")

    recovered = session_manager.get_session(session_id)
    contents = [m.content for m in recovered.messages]
    assert contents == [f"Mensagem {i}" for i in range(5)]


def test_session_created_at_and_updated_at(session_manager: SessionManager) -> None:
    """Sessão deve ter created_at e updated_at preenchidos."""
    session = session_manager.create_session("Timestamps")
    assert isinstance(session.created_at, datetime)
    assert isinstance(session.updated_at, datetime)
    assert session.created_at <= session.updated_at


def test_clear_all_sessions(session_manager: SessionManager) -> None:
    """clear_all_sessions deve limpar sessões da RAM e do banco."""
    session_manager.create_session("Para limpar")
    session_manager.clear_all_sessions()

    sm2 = SessionManager(database_path=session_manager.database_path)
    sessions = sm2.list_sessions()
    assert len(sessions) == 0
