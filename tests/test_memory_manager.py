"""Testes unitários para o MemoryManager (JARVIS-A-023)."""

from __future__ import annotations

import shutil

import pytest

from jarvis.memory.memory_manager import MemoryManager


@pytest.fixture
def memory_manager() -> MemoryManager:
    """Cria um MemoryManager para testes."""
    mm = MemoryManager()
    yield mm


def test_memory_manager_update_and_recall(memory_manager: MemoryManager) -> None:
    """Deve armazenar e recuperar mensagens de sessão."""
    entry = memory_manager.update_session_memory("sess1", "user", "Olá")
    assert entry["role"] == "user"
    assert entry["content"] == "Olá"

    contents = memory_manager.recall_session("sess1")
    assert "Olá" in contents


def test_memory_manager_save_and_get_profile(memory_manager: MemoryManager) -> None:
    """Deve salvar e recuperar perfil de usuário."""
    profile = memory_manager.save_user_profile(
        "sess1", {"nome": "João", "preferencias": ["Python"]}
    )
    assert profile["nome"] == "João"
    assert "Python" in profile["preferencias"]

    retrieved = memory_manager.get_user_profile("sess1")
    assert retrieved["nome"] == "João"


def test_memory_manager_search_history(memory_manager: MemoryManager) -> None:
    """Deve buscar no histórico da sessão por texto."""
    memory_manager.update_session_memory("sess1", "user", "Gosto de programação em Python")
    memory_manager.update_session_memory("sess1", "user", "Gosto de cozinhar massa")

    results = memory_manager.search_history("sess1", "Python")
    assert len(results) >= 1  # Pelo menos a mensagem "Python" deve ser encontrada
    assert "Python" in results[0]


def test_memory_manager_get_context_summary(memory_manager: MemoryManager) -> None:
    """Deve gerar resumo de contexto da sessão."""
    memory_manager.update_session_memory("sess1", "user", "Olá")
    memory_manager.update_session_memory("sess1", "assistant", "Oi!")

    summary = memory_manager.get_all_context("sess1")
    assert "user: Olá" in summary
    assert "assistant: Oi!" in summary


def test_memory_manager_semantic_search_returns_content(memory_manager: MemoryManager) -> None:
    """semantic_search deve retornar uma lista (pode estar vazia se não houver dados)."""
    resultados = memory_manager.semantic_search(query="Python", n_results=5)
    assert isinstance(resultados, list)


def test_memory_manager_semantic_session_isolation(memory_manager: MemoryManager) -> None:
    """semantic_search com session_id deve retornar uma lista (isolamento básico)."""
    resultados_s1 = memory_manager.semantic_search(query="teste", n_results=5, session_id="s1")
    resultados_s2 = memory_manager.semantic_search(query="teste", n_results=5, session_id="s2")
    assert isinstance(resultados_s1, list)
    assert isinstance(resultados_s2, list)
