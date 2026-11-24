from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import uuid4

from jarvis.core.config import PROJECT_ROOT
from jarvis.database.connection import open_connection

MAX_SESSIONS = 500
MAX_MESSAGES_PER_SESSION = 200


class SessionLimitError(RuntimeError):
    """Indica que o limite de sessões em memória foi atingido."""


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(slots=True)
class ChatSession:
    id: str
    title: str
    messages: list[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionManager:
    """Armazena sessões de conversa em memória com persistência SQLite."""

    def __init__(self, database_path: Path | None = None) -> None:
        self.database_path = database_path or PROJECT_ROOT / "data" / "jarvis.db"
        self._sessions: dict[str, ChatSession] = {}
        self._sessions_lock = Lock()
        self._init_database()

    def _init_database(self) -> None:
        """Garante que as tabelas de sessão e mensagem existam."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        with open_connection(self.database_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id          TEXT PRIMARY KEY,
                    title       TEXT NOT NULL DEFAULT 'Nova conversa',
                    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    updated_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_sessions_updated_at
                ON sessions (updated_at)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id  TEXT NOT NULL,
                    role        TEXT NOT NULL,
                    content     TEXT NOT NULL,
                    created_at  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_session_id
                ON messages (session_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_messages_created_at
                ON messages (created_at)
                """
            )
            conn.commit()

    def _load_sessions_from_db(self) -> None:
        """Carrega todas as sessões do banco para a memória RAM."""
        with open_connection(self.database_path) as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
            ).fetchall()
            for row in rows:
                session_id = row[0]
                session = ChatSession(
                    id=session_id,
                    title=row[1],
                    created_at=datetime.fromisoformat(row[2]),
                    updated_at=datetime.fromisoformat(row[3]),
                )
                msg_rows = conn.execute(
                    "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                    (session_id,),
                ).fetchall()
                session.messages = [
                    ChatMessage(role=m[0], content=m[1], created_at=datetime.fromisoformat(m[2]))
                    for m in msg_rows
                ]
                self._sessions[session_id] = session

    def _save_session(self, session: ChatSession) -> None:
        """Persiste uma sessão no banco de dados."""
        with open_connection(self.database_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions (id, title, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session.id,
                    session.title,
                    session.created_at.isoformat(),
                    session.updated_at.isoformat(),
                ),
            )
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))
            for msg in session.messages:
                conn.execute(
                    """
                    INSERT INTO messages (session_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        session.id,
                        msg.role,
                        msg.content,
                        msg.created_at.isoformat(),
                    ),
                )
            conn.commit()

    def create_session(self, title: str = "Nova conversa") -> ChatSession:
        with self._sessions_lock:
            if len(self._sessions) >= MAX_SESSIONS:
                raise SessionLimitError("Limite de conversas atingido. Reinicie o serviço local.")
            session = ChatSession(id=str(uuid4()), title=title)
            self._sessions[session.id] = session
            self._save_session(session)
            return session

    def get_session(self, session_id: str) -> ChatSession:
        session = self._sessions.get(session_id)
        if session is not None:
            return session
        # Tenta carregar do banco
        with open_connection(self.database_path) as conn:
            row = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?",
                (session_id,),
            ).fetchone()
            if row is None:
                raise KeyError(f"Sessão '{session_id}' não encontrada")
            session = ChatSession(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2]),
                updated_at=datetime.fromisoformat(row[3]),
            )
            msg_rows = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            ).fetchall()
            session.messages = [
                ChatMessage(role=m[0], content=m[1], created_at=datetime.fromisoformat(m[2]))
                for m in msg_rows
            ]
            self._sessions[session_id] = session
            return session

    def list_sessions(self) -> list[ChatSession]:
        with self._sessions_lock:
            if not self._sessions:
                self._load_sessions_from_db()
            return sorted(
                self._sessions.values(),
                key=lambda session: session.updated_at,
                reverse=True,
            )

    def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        session = self.get_session(session_id)
        message = ChatMessage(role=role, content=content)
        session.messages.append(message)
        if len(session.messages) > MAX_MESSAGES_PER_SESSION:
            session.messages = session.messages[-MAX_MESSAGES_PER_SESSION:]
        session.updated_at = datetime.now(timezone.utc)
        self._save_session(session)
        return message

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        return list(self.get_session(session_id).messages)

    def clear_all_sessions(self) -> None:
        """Remove todas as sessões (útil para testes)."""
        with self._sessions_lock:
            self._sessions.clear()
            with open_connection(self.database_path) as conn:
                conn.execute("DELETE FROM messages")
                conn.execute("DELETE FROM sessions")
                conn.commit()