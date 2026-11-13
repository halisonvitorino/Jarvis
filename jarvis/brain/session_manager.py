from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

MAX_SESSIONS = 50
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
    """Armazena sessões de conversa em memória com histórico por sessão."""

    def __init__(self) -> None:
        self._sessions: dict[str, ChatSession] = {}
        self._sessions_lock = Lock()

    def create_session(self, title: str = "Nova conversa") -> ChatSession:
        with self._sessions_lock:
            if len(self._sessions) >= MAX_SESSIONS:
                raise SessionLimitError("Limite de conversas atingido. Reinicie o serviço local.")
            session = ChatSession(id=str(uuid4()), title=title)
            self._sessions[session.id] = session
            return session

    def get_session(self, session_id: str) -> ChatSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise KeyError(f"Sessão '{session_id}' não encontrada")
        return session

    def list_sessions(self) -> list[ChatSession]:
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
        return message

    def get_messages(self, session_id: str) -> list[ChatMessage]:
        return list(self.get_session(session_id).messages)
