"""Vector store for semantic memory search using ChromaDB.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Cada responsabilidade isolada em função exclusiva
- nomes de funções e variáveis descritivos em inglês
- Log de todas as operações críticas
"""
from __future__ import annotations

import logging
from typing import List, Optional

import chromadb
from pathlib import Path

from jarvis.core.config import PROJECT_ROOT

logger = logging.getLogger(__name__)


class VectorStore:
    """Manages semantic search and storage using ChromaDB.

    Responsibilities:
    - Create/initialize ChromaDB client and collection
    - Store embeddings with metadata
    - Search for similar items by query embedding
    - List and manage stored items
    """

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        self.storage_dir = (
            Path(storage_dir).resolve() if storage_dir else None
        )
        # Garantir coleção nova: remover diretório anterior se existir
        import shutil
        if self.storage_dir:
            if self.storage_dir.exists():
                shutil.rmtree(self.storage_dir, ignore_errors=True)
        self.client = chromadb.PersistentClient(path=str(self.storage_dir) if self.storage_dir else None)
        self.collection = self.client.get_or_create_collection(name="jarvis_memory")
        logger.info("VectorStore initialized with collection 'jarvis_memory'")

    def add_items(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict],
        documents: Optional[List[str]] = None,
    ) -> None:
        """Add items with embeddings to the vector store.

        Args:
            ids: Unique identifiers for each item
            embeddings: List of embedding vectors (same order as ids)
            metadatas: Dictionary metadata for each item (same order as ids)
            documents: Optional text content for each item (same order as ids).
                       Required for search results to return actual content.
        """
        try:
            add_kwargs = {
                "ids": ids,
                "embeddings": embeddings,
                "metadatas": metadatas,
            }
            if documents is not None:
                add_kwargs["documents"] = documents
            self.collection.add(**add_kwargs)
            logger.debug("Added %d items to vector store", len(ids))
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to add items to vector store: %s", exc)
            raise

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        session_id: Optional[str] = None,
    ) -> dict:
        """Search for items similar to the query embedding.

        Args:
            query_embedding: The embedding vector to search against
            n_results: Number of results to return (default: 5)
            session_id: Optional session ID to filter results (isolates memory per session)

        Returns:
            Dictionary with search results containing ids, distances, metadatas, and documents
        """
        try:
            where_filter = {"session_id": session_id} if session_id else None
            query_kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            if where_filter:
                query_kwargs["where"] = where_filter
            results = self.collection.query(**query_kwargs)
            logger.debug(
                "Search returned %d results",
                len(results.get("ids", [[]])[0] or []),
            )
            return results
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Vector store search failed: %s", exc)
            raise

    def get_all_items(self) -> dict:
        """Retrieve all items from the vector store.

        Returns:
            Dictionary with all stored items
        """
        try:
            return self.collection.get()
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get all items from vector store: %s", exc)
            raise


vector_store = VectorStore(storage_dir=str(PROJECT_ROOT / "data" / "chroma"))  # Singleton instance for reuse across the module