"""
J.A.R.V.I.S Memory Manager

Gerencia a integração entre o sistema de memória e o ConversationManager.
Coordena memória de curto/longo prazo, perfis de usuário e busca de histórico.

Princípios ASD-STE100:
- Código direto e claro, sem ambiguidade
- Modular: cada responsabilidade tem sua classe/exceção
- Testável: métodos puros com entradas/saídas explícitas
- Logado: todas as operações críticas têm logging
- Substituível: pode ser trocado por implementação mais avançada sem alterar ConversationManager
"""

from __future__ import annotations

import logging
from typing import Any, Optional, List

from jarvis.memory import MemoryStore
from jarvis.core.config import get_settings

logger = logging.getLogger(__name__)


class MemoryManager:
    """Facade for MemoryStore integration with ConversationManager."""

    def __init__(self, storage_dir: Optional[str] = None) -> None:
        self.memory = MemoryStore(storage_dir)
        logger.info("MemoryManager initialized with storage at %s", self.memory.storage_dir)

    def update_session_memory(self, session_id: str, role: str, content: str) -> dict[str, str]:
        """Register a new message in session memory.

        Args:
            session_id: Unique session identifier
            role: Message role ('user', 'assistant', 'system')
            content: Message content

        Returns:
            dict with role and content that was stored
        """
        try:
            entry = self.memory.remember(session_id, role, content)
            logger.debug("Memory updated for session %s", session_id)
            return entry
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to update memory for session %s: %s", session_id, exc)
            raise

    def recall_session(self, session_id: str) -> list[str]:
        """Retrieve all message contents for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            List of message contents in chronological order
        """
        try:
            contents = self.memory.recall(session_id)
            logger.debug("Recalled %d messages for session %s", len(contents), session_id)
            return contents
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to recall memory for session %s: %s", session_id, exc)
            raise

    def save_user_profile(self, profile_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist user profile data.

        Args:
            profile_name: Identifier for the profile
            payload: Dictionary of profile attributes

        Returns:
            Merged profile dictionary
        """
        try:
            profile = self.memory.save_profile(profile_name, payload)
            logger.info("User profile '%s' saved with %d keys", profile_name, len(payload))
            return profile
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to save user profile '%s': %s", profile_name, exc)
            raise

    def get_user_profile(self, profile_name: str) -> dict[str, Any]:
        """Retrieve a user profile.

        Args:
            profile_name: Identifier for the profile

        Returns:
            Profile dictionary (empty if not found)
        """
        try:
            profile = self.memory.get_profile(profile_name)
            logger.debug("Retrieved profile '%s' with %d keys", profile_name, len(profile))
            return profile
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to retrieve user profile '%s': %s", profile_name, exc)
            raise

    def search_history(self, session_id: str, query: str) -> list[str]:
        """Search session history for a query string.

        Args:
            session_id: Unique session identifier
            query: Search query (plain text)

        Returns:
            List of matching message contents
        """
        try:
            results = self.memory.search_history(session_id, query)
            logger.debug("Found %d matches for query '%s' in session %s", len(results), query, session_id)
            return results
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to search history for session %s: %s", session_id, exc)
            raise

    def get_all_context(self, session_id: str) -> str:
        """Get full context summary for a session.

        Args:
            session_id: Unique session identifier

        Returns:
            Newline-joined string of "role: content" entries
        """
        try:
            summary = self.memory.get_context_summary(session_id)
            logger.debug("Generated context summary for session %s (length %d chars)", session_id, len(summary))
            return summary
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Failed to get context for session %s: %s", session_id, exc)
            raise

    def semantic_search(self, query: str, n_results: int = 5) -> List[str]:
        """Search memory for semantically similar items.

        Uses ChromaDB vector store to find items matching the query concept.

        Args:
            query: Search query text
            n_results: Number of results to return (default: 5)

        Returns:
            List of matching message contents sorted by relevance
        """
        from jarvis.memory.vector_store import vector_store as vs

        try:
            # Generate a simple embedding from the query text
            # In production, this would use a proper embedding model
            embedding = self._create_embedding(query)
            results = vs.search(embedding, n_results=n_results)
            matches: List[str] = results.get("ids", []) or []
            logger.info("Semantic search for '%s' returned %d results", query, len(matches))
            return matches
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Semantic search failed for query '%s': %s", query, exc)
            raise

    @staticmethod
    def _create_embedding(text: str) -> List[float]:
        """Create a simple embedding from text.

        Uses a hash-based approach for deterministic embedding generation.
        In production, this would be replaced by a sentence-transformers model.

        Args:
            text: Input text to embed

        Returns:
            List of floating point values representing the embedding
        """
        import hashlib

        hash_object = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Convert hex to float list in range [-1, 1]
        embedding: List[float] = []
        for i in range(0, 64, 2):
            hex_val = hash_object[i:i+2]
            float_val = (int(hex_val, 16) / 255.0) * 2.0 - 1.0
            embedding.append(float_val)
        # Pad or truncate to 384 dimensions ( typical embedding size )
        while len(embedding) < 384:
            embedding.append(0.0)
        embedding = embedding[:384]
        return embedding