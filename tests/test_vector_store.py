"""Testes unitários para o VectorStore (JARVIS-A-022)."""

from __future__ import annotations

import shutil
from typing import List

import pytest

from jarvis.memory.vector_store import VectorStore


@pytest.fixture
def vector_store(tmp_path):
    """Cria um VectorStore com diretório temporário."""
    store_dir = tmp_path / "chroma_test"
    vs = VectorStore(storage_dir=str(store_dir))
    yield vs
    shutil.rmtree(store_dir, ignore_errors=True)


def test_vector_store_initializes(vector_store: VectorStore) -> None:
    """VectorStore deve inicializar sem erro."""
    assert vector_store.client is not None
    assert vector_store.collection.name == "jarvis_memory"


def test_vector_store_add_and_search(vector_store: VectorStore) -> None:
    """Deve adicionar itens e buscá-los por similaridade."""
    vector_store.add_items(
        ids=["id1", "id2"],
        embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
        metadatas=[{"session_id": "s1"}, {"session_id": "s1"}],
        documents=["texto sobre Python", "texto sobre culinária"],
    )
    results = vector_store.search(query_embedding=[0.1, 0.2, 0.3], n_results=5)
    ids = results.get("ids", [[]])[0]
    documents = results.get("documents", [[]])[0]
    assert "id1" in ids
    assert len(documents) > 0
    assert all(d is not None for d in documents if d)


def test_vector_store_session_isolation(vector_store: VectorStore) -> None:
    """Busca com session_id deve retornar apenas itens daquela sessão."""
    vector_store.add_items(
        ids=["s1_item1", "s1_item2", "s2_item1"],
        embeddings=[[0.1, 0.2, 0.3]] * 3,
        metadatas=[
            {"session_id": "s1"},
            {"session_id": "s1"},
            {"session_id": "s2"},
        ],
        documents=["conteúdo sessão 1 A", "conteúdo sessão 1 B", "conteúdo sessão 2"],
    )
    results = vector_store.search(
        query_embedding=[0.1, 0.2, 0.3], n_results=5, session_id="s1"
    )
    ids = results.get("ids", [[]])[0]
    assert "s1_item1" in ids
    assert "s1_item2" in ids
    assert "s2_item1" not in ids


def test_vector_store_returns_documents(vector_store: VectorStore) -> None:
    """Busca deve retornar documentos (conteúdo), não apenas IDs."""
    vector_store.add_items(
        ids=["doc1"],
        embeddings=[[0.5, 0.5, 0.5]],
        metadatas=[{"session_id": "s1"}],
        documents=["conteúdo real do documento"],
    )
    results = vector_store.search(query_embedding=[0.5, 0.5, 0.5], n_results=5)
    documents = results.get("documents", [[]])[0]
    assert "conteúdo real do documento" in documents


def test_vector_store_persistence(vector_store: VectorStore, tmp_path) -> None:
    """Dados devem persistir após recriar o VectorStore no mesmo diretório."""
    store_dir = tmp_path / "chroma_persist"
    vs1 = VectorStore(storage_dir=str(store_dir))
    vs1.add_items(
        ids=["persist1"],
        embeddings=[[0.1, 0.2, 0.3]],
        metadatas=[{"session_id": "s1"}],
        documents=["dado que deve persistir"],
    )

    # Recriar instância no mesmo diretório
    vs2 = VectorStore(storage_dir=str(store_dir))
    results = vs2.search(query_embedding=[0.1, 0.2, 0.3], n_results=5)
    ids = results.get("ids", [[]])[0]
    assert "persist1" in ids
    shutil.rmtree(store_dir, ignore_errors=True)
