"""Memória de curto e longo prazo. Implementação da Phase 2 (Memory System)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jarvis.core.config import PROJECT_ROOT


class MemoryStore:
    """Armazena contexto recente por sessão e perfil persistente do usuário."""

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        base_dir = Path(storage_dir) if storage_dir is not None else PROJECT_ROOT / "data" / "memory"
        self.storage_dir = base_dir.resolve()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self._session_file = self.storage_dir / "short_term.json"
        self._profile_file = self.storage_dir / "long_term.json"

        self._sessions = self._load_json(self._session_file, default={})
        self._profiles = self._load_json(self._profile_file, default={})

    @staticmethod
    def _load_json(path: Path, *, default: Any) -> Any:
        if not path.exists():
            return default

        try:
            with path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, OSError):
            return default

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)

    def remember(self, session_id: str, role: str, content: str) -> dict[str, str]:
        session_memory = self._sessions.setdefault(str(session_id), [])
        entry = {"role": role, "content": content}
        session_memory.append(entry)
        self._write_json(self._session_file, self._sessions)
        return entry

    def recall(self, session_id: str) -> list[str]:
        session_memory = self._sessions.get(str(session_id), [])
        return [entry["content"] for entry in session_memory]

    def save_profile(self, profile_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        profile_key = str(profile_name)
        existing = self._profiles.get(profile_key, {})
        merged: dict[str, Any] = dict(existing)

        for key, value in payload.items():
            current = merged.get(key)
            if isinstance(current, list) and isinstance(value, list):
                merged[key] = list(dict.fromkeys([*current, *value]))
            elif isinstance(current, dict) and isinstance(value, dict):
                merged[key] = {**current, **value}
            else:
                merged[key] = value

        self._profiles[profile_key] = merged
        self._write_json(self._profile_file, self._profiles)
        return dict(merged)

    def get_profile(self, profile_name: str) -> dict[str, Any]:
        return dict(self._profiles.get(str(profile_name), {}))

    def search_history(self, session_id: str, query: str) -> list[str]:
        session_memory = self._sessions.get(str(session_id), [])
        query_lower = str(query).strip().lower()
        if not query_lower:
            return []

        return [
            str(entry["content"])
            for entry in session_memory
            if query_lower in str(entry.get("content", "")).lower()
        ]

    def remember_fact(self, session_id: str, fact: str) -> str:
        return self.remember(session_id, "fact", fact)["content"]

    def get_context_summary(self, session_id: str) -> str:
        session_memory = self._sessions.get(str(session_id), [])
        return "\n".join(f"{entry['role']}: {entry['content']}" for entry in session_memory)


__all__ = ["MemoryStore"]
