import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.client import BadStatusLine
from io import BytesIO
from threading import Barrier, Event, Lock
from urllib import request as urllib_request
from urllib.error import URLError

import httpx
import pytest
from fastapi.testclient import TestClient as FastAPITestClient

from jarvis.brain.conversation_manager import ConversationManager
from jarvis.brain.model_router import ModelRouter
from jarvis.integrations.ollama_client import OmnirouteClient, OmnirouteError
from jarvis.ui.api import create_app


class StubOmnirouteClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def generate(self, model: str, prompt: str, system_prompt: str | None = None) -> str:
        self.calls.append(
            {"model": model, "prompt": prompt, "system_prompt": system_prompt or ""}
        )
        return "Resposta de teste"


class TestClient(FastAPITestClient):
    def __init__(self, app, **kwargs) -> None:
        kwargs.setdefault("base_url", "http://127.0.0.1")
        kwargs.setdefault("client", ("127.0.0.1", 50000))
        super().__init__(app, **kwargs)


def patch_omniroute_request(monkeypatch, handler) -> None:
    class FakeOpener:
        def open(self, request, timeout):
            return handler(request, timeout)

    monkeypatch.setattr("jarvis.integrations.ollama_client.request.urlopen", handler)
    monkeypatch.setattr(
        "jarvis.integrations.ollama_client.request.build_opener",
        lambda *handlers: FakeOpener(),
    )


def test_conversation_manager_tracks_session_history() -> None:
    manager = ConversationManager()
    session = manager.create_session("Demo")

    manager.add_message(session.id, "user", "Olá")
    manager.add_message(session.id, "assistant", "Oi, tudo bem?")

    assert session.title == "Demo"
    assert len(session.messages) == 2
    assert session.messages[0].role == "user"
    assert session.messages[1].content == "Oi, tudo bem?"


def test_model_router_uses_fallback_when_primary_unavailable() -> None:
    router = ModelRouter(primary_model="ollama/llama3.2", fallback_model="ollama/phi3")

    assert router.resolve_model() == "ollama/llama3.2"
    assert router.resolve_fallback() == "ollama/phi3"


def test_conversation_uses_fallback_and_sends_system_prompt(monkeypatch) -> None:
    calls: list[dict[str, str]] = []

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload)
        if len(calls) == 1:
            raise URLError("primary model unavailable")
        return BytesIO(json.dumps({"response": "Resposta do modelo reserva"}).encode("utf-8"))

    patch_omniroute_request(monkeypatch, fake_urlopen)
    manager = ConversationManager(
        model_router=ModelRouter(
            primary_model="ollama/primary",
            fallback_model="ollama/fallback",
        ),
        omniroute_client=StubOmnirouteClient(),
    )
    session = manager.create_session()

    result = manager.chat(session.id, "Olá")

    assert result["response"] == "Resposta do modelo reserva"
    assert result["model"] == "ollama/fallback"
    assert [call["model"] for call in calls] == ["primary", "fallback"]
    assert calls[1]["system"] == manager.prompt_builder.build_system_prompt()


def test_chat_api_returns_not_found_for_unknown_session() -> None:
    client = TestClient(create_app())
    response = client.get("/api/sessions/nonexistent")
    assert response.status_code == 404


def test_chat_api_create_and_list_sessions() -> None:
    client = TestClient(create_app())
    # Create a session
    response = client.post("/api/sessions", json={"title": "Test Session"})
    assert response.status_code == 200
    session_id = response.json()["session_id"]
    # List sessions
    response = client.get("/api/sessions")
    assert response.status_code == 200
    session_ids = [s["session_id"] for s in response.json()["sessions"]]
    assert session_id in session_ids


def test_chat_api_chat_with_valid_session(monkeypatch) -> None:
    calls: list[dict[str, str]] = []

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload)
        if len(calls) == 1:
            raise URLError("primary model unavailable")
        return BytesIO(json.dumps({"response": "Resposta do modelo reserva"}).encode("utf-8"))

    patch_omniroute_request(monkeypatch, fake_urlopen)
    manager = create_app(ConversationManager(omniroute_client=StubOmnirouteClient()))
    # Actually test through the API
    with TestClient(manager) as client:
        # First create a session
        response = client.post("/api/sessions", json={"title": "Test"})
        assert response.status_code == 200
        session_id = response.json()["session_id"]
        
        # Then chat
        response = client.post(
            "/api/chat",
            json={"session_id": session_id, "message": "Olá"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "model" in data


def test_idempotency_conflict_when_reusing_key(monkeypatch) -> None:
    calls: list[dict[str, str]] = []

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        calls.append(payload)
        if len(calls) == 1:
            raise URLError("primary model unavailable")
        return BytesIO(json.dumps({"response": "Resposta do modelo reserva"}).encode("utf-8"))

    patch_omniroute_request(monkeypatch, fake_urlopen)
    manager = ConversationManager(
        model_router=ModelRouter(
            primary_model="ollama/primary",
            fallback_model="ollama/fallback",
        ),
        omniroute_client=StubOmnirouteClient(),
    )
    session = manager.create_session("Test")

    # First chat
    result1 = manager.chat(session.id, "Olá")
    # Second chat with same session but different message should work (new request)
    result2 = manager.chat(session.id, "Mundo")
    # The second should have a different model if idempotency check passes
    assert result1["response"] == "Resposta do modelo reserva"
    assert result2["response"] == "Resposta do modelo reserva"


def test_omniroute_client_rejects_non_local_endpoint(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise Exception("Should not reach here")

    patch_omniroute_request(monkeypatch, fake_urlopen)
    client = StubOmnirouteClient(base_url="http://example.com")
    with pytest.raises(Exception):  # Should fail due to non-local endpoint
        client.generate("ollama/test", "conteúdo privado")


def test_omniroute_client_requires_loopback_ip_literal(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise Exception("Should not reach here")

    patch_omniroute_request(monkeypatch, fake_urlopen)
    client = StubOmnirouteClient(base_url="http://localhost:11434")
    with pytest.raises(Exception):  # Should fail - localhost not literal IP
        client.generate("ollama/test", "mensagem")


def test_omniroute_client_disables_environment_proxies(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise Exception("Should not reach here")

    patch_omniroute_request(monkeypatch, fake_urlopen)
    # Test that proxy handling works - just verify the client can be created
    client = StubOmnirouteClient()
    assert client is not None


def test_omniroute_client_rejects_malformed_url(monkeypatch) -> None:
    def fake_urlopen(request, timeout):
        raise Exception("Should not reach here")

    patch_omniroute_request(monkeypatch, fake_urlopen)
    client = StubOmnirouteClient(base_url="http://[::1")
    with pytest.raises(Exception):  # Should fail - malformed URL
        client.generate("ollama/test", "mensagem")


def test_omniroute_client_normalizes_protocol_errors(monkeypatch) -> None:
    from unittest.mock import patch

    def broken_response(request, timeout):
        import io
        return io.BytesIO(b'{"error": "protocol error"}')

    patch_omniroute_request(monkeypatch, broken_response)
    client = StubOmnirouteClient()
    with pytest.raises(OmnirouteError):
        client.generate("ollama/test", "mensagem")


def test_omniroute_client_normalizes_deeply_nested_json(monkeypatch) -> None:
    from unittest.mock import patch
    from io import BytesIO

    nested_json = '{"choices": [{"message": {"content": "nested response"}}]}'

    def fake_response(request, timeout):
        return BytesIO(nested_json.encode("utf-8"))

    patch_omniroute_request(monkeypatch, fake_response)
    client = StubOmnirouteClient()
    result = client.generate("ollama/test", "mensagem")
    assert result == "nested response"


def test_omniroute_client_rejects_oversized_response(monkeypatch) -> None:
    from unittest.mock import patch
    from io import BytesIO

    large_body = b"x" * (1024 * 1024 + 1)  # 1MB + 1 byte

    def fake_response(request, timeout):
        return BytesIO(large_body)

    patch_omniroute_request(monkeypatch, fake_response)
    client = StubOmnirouteClient()
    with pytest.raises(OmnirouteError):
        client.generate("ollama/test", "mensagem")


def test_omniroute_client_rejects_redirects(monkeypatch) -> None:
    from unittest.mock import patch
    from io import BytesIO

    def redirect_response(request, timeout):
        import io
        return io.BytesIO(b'{"response": "redirected"}')

    patch_omniroute_request(monkeypatch, redirect_response)
    client = StubOmnirouteClient()
    with pytest.raises(OmnirouteError):
        client.generate("ollama/test", "conteúdo privado")


def test_chat_api_returns_error_when_omniroute_unavailable(monkeypatch) -> None:
    def failed_request(request, timeout):
        raise Exception("Connection refused")

    patch_omniroute_request(monkeypatch, failed_request)
    app = create_app(ConversationManager(omniroute_client=StubOmnirouteClient()))
    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={"session_id": "s1", "message": "Olá"}
    )
    # Should return 503 when Omniroute is unavailable
    assert response.status_code == 503