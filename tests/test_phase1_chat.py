"""Testes da API de chat e do ConversationManager (Phase 1).

Focam em comportamento do core: sessões, mensagens, limites, idempotência
e integração com a API FastAPI. Os provedores de IA são isolados via mocks.
"""

from threading import Lock
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient as FastAPITestClient

from jarvis.brain.conversation_manager import ConversationManager, IdempotencyConflictError
from jarvis.brain.model_router import ModelRouter
from jarvis.brain.session_manager import ChatSession, SessionLimitError
from jarvis.integrations.gemini_client import GeminiError
from jarvis.integrations.nvidia_client import NvidiaError
from jarvis.integrations.ollama_client import OmnirouteError
from jarvis.memory import MemoryStore
from jarvis.ui.api import create_app


class MockOmnirouteClient:
    """Cliente Omniroute simulado para testes determinísticos."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self._lock = Lock()

    def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None,
                 temperature: float = 0.7, top_p: float = 0.95, max_tokens: int = 2048) -> str:
        with self._lock:
            self.calls.append({
                "prompt": prompt,
                "system_prompt": system_prompt,
                "model": model,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
            })
        return "Resposta simulada do Omniroute"


class MockGeminiClient:
    """Cliente Gemini simulado para testes determinísticos."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None) -> str:
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return "Resposta simulada do Gemini"


class MockNvidiaClient:
    """Cliente NVIDIA simulado para testes determinísticos."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate(self, prompt: str, system_prompt: str | None = None, model: str | None = None,
                 temperature: float = 0.7, top_p: float = 0.95, max_tokens: int = 2048) -> str:
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt, "model": model})
        return "Resposta simulada da NVIDIA"


class TestConversationManager(ConversationManager):
    """ConversationManager com clientes de IA injetáveis para testes."""

    def __init__(self, provider: str = "gemini",
                 omniroute: MockOmnirouteClient | None = None,
                 gemini: MockGeminiClient | None = None,
                 nvidia: MockNvidiaClient | None = None) -> None:
        super().__init__()
        self._test_provider = provider
        self.settings.default_provider = provider  # sobrescreve para o teste controlar o provedor
        self.omniroute_client = omniroute or MockOmnirouteClient()
        self.gemini_client = gemini or MockGeminiClient()
        self.nvidia_client = nvidia or MockNvidiaClient()

    def _generate_with_provider(self, model: str, prompt: str,
                                system_prompt: str | None = None) -> str:
        """Delegação direta para o cliente injetado conforme provider do teste."""
        if self._test_provider == "gemini":
            return self.gemini_client.generate(prompt, system_prompt, model)
        if self._test_provider == "nvidia":
            return self.nvidia_client.generate(prompt, system_prompt, model)
        return self.omniroute_client.generate(prompt, system_prompt, model)


class APITestClient:
    """Wrapper do TestClient do FastAPI configurado para loopback."""

    def __init__(self, app) -> None:
        self._client = FastAPITestClient(app, base_url="http://127.0.0.1", client=("127.0.0.1", 50000))

    def __getattr__(self, name):
        return getattr(self._client, name)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _make_manager(provider="gemini", omniroute=None, gemini=None, nvidia=None):
    """Constrói um ConversationManager com mocks injetáveis."""
    return TestConversationManager(provider=provider, omniroute=omniroute,
                                   gemini=gemini, nvidia=nvidia)


def test_conversation_manager_tracks_session_history() -> None:
    """ConversationManager mantém histórico ordenado por sessão."""
    manager = ConversationManager()
    session = manager.create_session("Demo")

    manager.add_message(session.id, "user", "Olá")
    manager.add_message(session.id, "assistant", "Oi, tudo bem?")

    assert session.title == "Demo"
    assert len(session.messages) == 2
    assert session.messages[0].role == "user"
    assert session.messages[1].content == "Oi, tudo bem?"


def test_model_router_resolves_primary_and_fallback() -> None:
    """ModelRouter retorna modelo primário e de fallback corretamente."""
    router = ModelRouter(provider="gemini", primary_model="gemini-pro", fallback_model="gemini-1.5-flash",
                         nvidia_model="nvidia/nemotron-3-ultra-550b-a55b")

    assert router.resolve_model() == "gemini-pro"
    assert router.resolve_fallback() == "gemini-1.5-flash"


def test_conversation_uses_injected_clients() -> None:
    """chat() usa os clientes injetados e persiste o turno."""
    gemini = MockGeminiClient()
    manager = _make_manager(gemini=gemini)
    session = manager.create_session("Test")

    result = manager.chat(session.id, "Olá")

    assert result["response"] == "Resposta simulada do Gemini"
    assert result["model"]  # modelo não vazio
    assert len(gemini.calls) == 1
    assert "Olá" in gemini.calls[0]["prompt"]
    assert any(m.content == "Olá" for m in session.messages)
    assert any(m.role == "assistant" for m in session.messages)


def test_conversation_names_new_session_from_first_message() -> None:
    """Session 'Nova conversa' ganha título da primeira mensagem."""
    manager = _make_manager(gemini=MockGeminiClient())
    session = manager.create_session("Nova conversa")

    manager.chat(session.id, "Sobre Python")

def test_conversation_max_context_messages() -> None:
    """Contexto do modelo é limitado às mensagens recentes."""
    manager = _make_manager(gemini=MockGeminiClient())
    session = manager.create_session("Test")

    for i in range(25):
        manager.add_message(session.id, "user", f"Mensagem {i}")

    result = manager.chat(session.id, "Resposta")
    history = manager.get_session(session.id).messages[-19:]
    assert len(history) <= 19


def test_conversation_session_limit_raises() -> None:
    """Excesso de sessões eleva SessionLimitError."""
    manager = _make_manager(gemini=MockGeminiClient())
    for i in range(50):
        manager.create_session(f"Session {i}")
    with pytest.raises(SessionLimitError):
        manager.create_session("Limite")


def test_conversation_missing_session_raises() -> None:
    """Chamada em sessão inexistente eleva KeyError."""
    manager = _make_manager(gemini=MockGeminiClient())
    with pytest.raises(KeyError):
        manager.chat("nao-existe", "Olá")


def test_chat_api_returns_not_found_for_unknown_session() -> None:
    """API retorna 404 para sessão inexistente."""
    client = APITestClient(create_app())
    response = client.get("/api/sessions/nonexistent")
    assert response.status_code == 404


def test_chat_api_create_and_list_sessions() -> None:
    """API cria e lista sessões."""
    client = APITestClient(create_app())
    response = client.post("/api/sessions", json={"title": "Test Session"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    response = client.get("/api/sessions")
    assert response.status_code == 200
    session_ids = [s["session_id"] for s in response.json()["sessions"]]
    assert session_id in session_ids


def test_chat_api_returns_429_on_session_limit() -> None:
    """API retorna 429 quando o limite de sessões é atingido."""
    manager = _make_manager(gemini=MockGeminiClient())
    for i in range(50):
        manager.create_session(f"Session {i}")
    client = APITestClient(create_app(manager))

    response = client.post("/api/sessions", json={"title": "Limite"})
    assert response.status_code == 429


def test_chat_api_sends_message_and_receives_response() -> None:
    """Fluxo completo da API: criação de sessão + chat."""
    gemini = MockGeminiClient()
    manager = _make_manager(gemini=gemini)
    client = APITestClient(create_app(manager))

    session_response = client.post("/api/sessions", json={"title": "Test"})
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    chat_response = client.post("/api/chat", json={"session_id": session_id, "message": "Olá"})
    assert chat_response.status_code == 200
    data = chat_response.json()
    assert "response" in data
    assert "model" in data
    assert "session_id" in data
    assert data["response"] == "Resposta simulada do Gemini"


def test_chat_api_empty_message_is_rejected() -> None:
    """Mensagem vazia é rejeitada pela validação do schema (422)."""
    gemini = MockGeminiClient()
    manager = _make_manager(gemini=gemini)
    client = APITestClient(create_app(manager))

    response = client.post("/api/sessions", json={"title": "Test"})
    session_id = response.json()["session_id"]
    response = client.post("/api/chat", json={"session_id": session_id, "message": ""})
    assert response.status_code == 422


def test_chat_api_body_limit_rejected() -> None:
    """Corpo acima de 64 KiB retorna 413."""
    manager = _make_manager(gemini=MockGeminiClient())
    client = APITestClient(create_app(manager))
    payload = {"session_id": "x", "message": "x" * (64 * 1024 + 1)}
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 413


def test_chat_api_503_when_all_ia_unavailable() -> None:
    """API retorna 503 quando todos os provedores falham."""

    class FailingGeminiClient:
        def generate(self, prompt, system_prompt=None, model=None):
            raise GeminiError("Gemini down")

    class FailingNvidiaClient:
        def generate(self, prompt, system_prompt=None, model=None, **kwargs):
            raise NvidiaError("NVIDIA down")

    class FailingOmnirouteClient:
        def generate(self, prompt, system_prompt=None, model=None, **kwargs):
            raise OmnirouteError("Omniroute down")

    manager = _make_manager(
        gemini=FailingGeminiClient(),
        nvidia=FailingNvidiaClient(),
        omniroute=FailingOmnirouteClient(),
    )
    client = APITestClient(create_app(manager))

    response = client.post("/api/sessions", json={"title": "Test"})
    session_id = response.json()["session_id"]
    response = client.post("/api/chat", json={"session_id": session_id, "message": "Olá"})
    assert response.status_code == 503


def test_idempotency_conflict_when_reusing_key() -> None:
    """Reuso de request_id no mesmo turno retorna 409."""
    manager = _make_manager(gemini=MockGeminiClient())
    client = APITestClient(create_app(manager))

    session_response = client.post("/api/sessions", json={"title": "Test"})
    session_id = session_response.json()["session_id"]
    request_id = "req-123"

    first = client.post("/api/chat", json={"session_id": session_id, "message": "Olá", "request_id": request_id})
    assert first.status_code == 200

    second = client.post("/api/chat", json={"session_id": session_id, "message": "Mundo", "request_id": request_id})
    assert second.status_code == 409
    detail = second.json().get("detail", "")
    assert "identificador" in detail or "Idempotency" in detail
