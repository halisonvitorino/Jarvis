from __future__ import annotations

import re
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
from jarvis.voice.tts import TextToSpeech, TTSError
import os
from pathlib import Path

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
    speak: bool = Field(default=False)

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


def create_app(
    manager: ConversationManager | None = None,
    tts: TextToSpeech | None = None,
) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        nonlocal tts  # 1. Usa a variável 'tts' externa em vez de criar uma local
        bootstrap()

        if tts is None:
            # 2. Aponta para a pasta 'data' na raiz do projeto (3 níveis acima de api.py)
            project_root = Path(__file__).resolve().parent.parent.parent
            models_dir = project_root / "data" / "voice" / "models"
            onnx_path = models_dir / "pt_BR-jeff-medium.onnx"
            json_path = models_dir / "pt_BR-jeff-medium.onnx.json"

            if onnx_path.exists() and json_path.exists():
                try:
                    tts = TextToSpeech(
                        model_path=str(onnx_path), config_path=str(json_path)
                    )
                    tts.load_model()
                    print("✅ TTS automático carregado dos modelos do projeto")
                except Exception as e:
                    print(f"❌ Não foi possível carregar TTS automático: {e}")
            else:
                print(f"⚠️ Modelos TTS não encontrados em: {models_dir}")

        yield

    app = FastAPI(title="Jarvis", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        RequestBodyLimitMiddleware, max_body_bytes=MAX_REQUEST_BODY_BYTES
    )
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
            "messages": [
                _serialize_message(message) for message in session.messages
            ],
        }

    @app.post("/api/sessions")
    def create_session(payload: SessionCreateRequest) -> dict[str, str]:
        try:
            session = conversation_manager.create_session(payload.title)
        except SessionLimitError as exc:
            raise HTTPException(status_code=429, detail=str(exc)) from exc
        return {"session_id": session.id, "title": session.title}

    @app.post("/api/chat")
    def chat(payload: ChatRequest) -> dict[str, Any]:
        try:
            result = conversation_manager.chat(
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

        # 3. Indentação corrigida dentro da função chat
        spoken = False
        if payload.speak:
            if tts is not None:
                try:
                    raw_text = result.get("response", "")
                    clean_text = re.sub(r"```[\s\(\S\)]*?```", "Veja o código na tela.", raw_text)
                    clean_text = re.sub(r"[`*_~#•-]+", " ", clean_text)
                    clean_text = re.sub(r"\s+", " ", clean_text).strip()
                    tts.synthesize_and_play(clean_text)
                    spoken = True
                except TTSError as exc:
                    print(f"Erro TTS: {exc}")
                    spoken = False
            else:
                print("TTS não disponível - resposta será apenas texto")

        return {
            "session_id": result["session_id"],
            "title": result["title"],
            "response": result["response"],
            "model": result["model"],
            "spoken": spoken,
        }

    @app.delete("/api/test/sessions")
    def clear_all_sessions() -> dict[str, str]:
        """Limpa todas as sessões (apenas para testes)."""
        conversation_manager.session_manager.clear_all_sessions()
        return {"status": "cleared"}

    @app.websocket("/ws/voice")
    async def websocket_voice(websocket: WebSocket):
        await websocket.accept()
        import json
        import asyncio
        import numpy as np
        
        # Voice state
        voice_state = {
            "volume": 0.0,
            "bands": [0.0] * 16,
            "speaking": False,
            "thinking": False
        }
        
        # Audio buffer for analysis
        audio_buffer = []
        buffer_size = 1024
        
        try:
            while True:
                # Receive audio data from client
                data = await websocket.receive_text()
                try:
                    audio_chunk = json.loads(data)
                    if "audio" in audio_chunk:
                        # Process audio for volume and frequencies
                        samples = np.array(audio_chunk["audio"], dtype=np.float32)
                        if len(samples) > 0:
                            # Calculate RMS volume
                            rms = np.sqrt(np.mean(samples ** 2))
                            voice_state["volume"] = min(1.0, float(rms) * 10)
                            
                            # Calculate FFT frequency bands
                            if len(samples) >= 256:
                                # Apply windowing
                                windowed = samples * np.hanning(len(samples))
                                fft = np.fft.rfft(windowed, n=256)
                                magnitudes = np.abs(fft[:129])
                                
                                # Create 8-16 bands (mel-scale approximation)
                                band_size = 128 // 8  # 16 bands from 128 frequency bins
                                bands = []
                                for i in range(8):
                                    start = i * band_size
                                    end = min((i + 1) * band_size, 128)
                                    if start < end:
                                        band_val = np.mean(magnitudes[start:end])
                                    else:
                                        band_val = 0.0
                                    # Normalize to 0-1
                                    band_val = min(1.0, float(band_val) * 5)
                                    bands.append(band_val)
                                    
                                # Pad to 16 bands if needed
                                while len(bands) < 16:
                                    bands.append(0.0)
                                voice_state["bands"] = bands[:16]
                            
                            # Detect speaking state
                            if voice_state["volume"] > 0.3:
                                voice_state["speaking"] = True
                            else:
                                voice_state["speaking"] = False
                        
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass
                
                # Send current voice state
                await websocket.send_text(json.dumps(voice_state))
                await asyncio.sleep(0.03)  # ~30fps
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            await websocket.close()
    return app


def _clean_text_for_tts(text: str) -> str:
    """Remove formatação Markdown e símbolos para uma leitura fluida no TTS."""
    # Remove blocos de código completos (```...```) para o Jarvis não ler código linha por linha
    text = re.sub(
        r"```[\s\(\S\)]*?```",
        "Veja o código na tela.",
        text,
    )
    # Remove crases de código inline (`codigo`) mantendo a palavra
    text = re.sub(r"`([^`]+)`", r"\1", text)
    # Remove links [texto](url) deixando apenas o texto
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Remove hashtags de títulos (#, ##, ###)
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)
    # Remove negrito, itálico e tachado (*, _, ~)
    text = re.sub(r"[*_~]+", "", text)
    # Remove marcadores de lista no início das linhas (- ou •)
    text = re.sub(r"^\s*[-•]\s+", "", text, flags=re.MULTILINE)
    # Limpa múltiplos espaços ou quebras de linha seguidas
    text = re.sub(r"\n{2,}", ". ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


app = create_app()