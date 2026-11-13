from __future__ import annotations

import ipaddress
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from jarvis.brain.conversation_manager import ConversationManager
from jarvis.brain.conversation_manager import IdempotencyConflictError
from jarvis.brain.session_manager import SessionLimitError
from jarvis.core.bootstrap import bootstrap
from jarvis.integrations.gemini_client import GeminiError
from jarvis.integrations.nvidia_client import NvidiaError
from jarvis.integrations.ollama_client import OmnirouteError

STATIC_DIR = Path(__file__).with_name("static")
MAX_REQUEST_BODY_BYTES = 64 * 1024


class RequestBodyLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_bytes: int) -> None:
        self.app = app
        self.max_body_bytes = max_body_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                request_size = int(content_length)
            except ValueError:
                response = JSONResponse(
                    status_code=400,
                    content={"detail": "Cabeçalho de tamanho inválido."},
                )
                await response(scope, receive, send)
                return
            if request_size < 0 or request_size > self.max_body_bytes:
                await self._send_too_large(scope, receive, send)
                return

        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] != "http.request":
                continue

            chunk = message.get("body", b"")
            if len(chunk) > self.max_body_bytes - len(body):
                await self._send_too_large(scope, receive, send)
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        body_sent = False

        async def replay_receive() -> Message:
            nonlocal body_sent
            if body_sent:
                return await receive()
            body_sent = True
            return {"type": "http.request", "body": bytes(body), "more_body": False}

        await self.app(scope, replay_receive, send)

    async def _send_too_large(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = JSONResponse(
            status_code=413,
            content={"detail": "O corpo da solicitação excede o limite permitido."},
        )
        await response(scope, receive, send)


class LoopbackClientMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        client = scope.get("client")
        try:
            is_loopback = bool(client and ipaddress.ip_address(client[0]).is_loopback)
        except ValueError:
            is_loopback = False
        if not is_loopback:
            response = JSONResponse(
                status_code=403,
                content={"detail": "A API aceita apenas conexões locais."},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


class SessionCreateRequest(BaseModel):
    title: str = Field(default="Nova conversa", min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("O título não pode ficar vazio.")
        return title


class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=12000)
    request_id: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("A mensagem não pode ficar vazia.")
        return message


def _serialize_message(message: Any) -> dict[str, str]:
    return {
        "role": message.role,
        "content": message.content,
        "created_at": message.created_at.isoformat(),
    }


def _serialize_session(session: Any) -> dict[str, str]:
    return {
        "session_id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
    }


def create_app(manager: ConversationManager | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        bootstrap()
        yield

    app = FastAPI(title="Jarvis", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestBodyLimitMiddleware, max_body_bytes=MAX_REQUEST_BODY_BYTES)
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["127.0.0.1", "localhost", "::1"],
    )
    app.add_middleware(LoopbackClientMiddleware)
    conversation_manager = manager or ConversationManager()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next: Any) -> Any:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
            "base-uri 'self'; frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    @app.get("/", response_class=FileResponse)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/sessions")
    def list_sessions() -> dict[str, list[dict[str, str]]]:
        sessions = conversation_manager.list_sessions()
        return {"sessions": [_serialize_session(session) for session in sessions]}

    @app.get("/api/sessions/{session_id}")
    def get_session_detail(session_id: str) -> dict[str, Any]:
        try:
            session = conversation_manager.get_session(session_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        return {
            "session_id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "messages": [_serialize_message(message) for message in session.messages],
        }

    @app.post("/api/sessions")
    def create_session(payload: SessionCreateRequest) -> dict[str, str]:
        try:
            session = conversation_manager.create_session(payload.title)
        except SessionLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return {"session_id": session.id, "title": session.title}

    @app.post("/api/chat")
    def chat(payload: ChatRequest) -> dict[str, str]:
        try:
            return conversation_manager.chat(
                payload.session_id,
                payload.message,
                request_id=payload.request_id,
            )
        except IdempotencyConflictError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except (OmnirouteError, GeminiError, NvidiaError) as exc:
            raise HTTPException(
                status_code=503,
                detail=f"Provedor de IA indisponível: {exc}",
            ) from exc

    return app


app = create_app()
