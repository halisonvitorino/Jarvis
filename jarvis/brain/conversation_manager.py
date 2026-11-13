from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from threading import Lock, RLock

from jarvis.brain.model_router import ModelRouter
from jarvis.brain.prompt_builder import PromptBuilder
from jarvis.brain.session_manager import ChatMessage, ChatSession, SessionManager
from jarvis.core.config import get_settings
from jarvis.core.logger import get_logger
from jarvis.integrations.gemini_client import GeminiClient, GeminiError
from jarvis.integrations.nvidia_client import NvidiaClient, NvidiaError
from jarvis.integrations.ollama_client import OmnirouteClient, OmnirouteError

logger = get_logger(__name__)
MAX_CONTEXT_MESSAGES = 20
MAX_COMPLETED_REQUESTS = 1000


class IdempotencyConflictError(RuntimeError):
    """Indica que uma chave de envio já pertence a outra mensagem."""

@dataclass(slots=True)
class ConversationManager:
    session_manager: SessionManager = field(default_factory=SessionManager)
    settings: object = field(default_factory=get_settings)
    model_router: ModelRouter = field(init=False)
    omniroute_client: OmnirouteClient = field(init=False)
    gemini_client: GeminiClient = field(init=False)
    nvidia_client: NvidiaClient = field(init=False)
    prompt_builder: PromptBuilder = field(default_factory=PromptBuilder)
    _session_locks: dict[str, RLock] = field(default_factory=dict, init=False, repr=False)
    _locks_guard: Lock = field(default_factory=Lock, init=False, repr=False)
    _completed_requests: dict[tuple[str, str], tuple[str, dict[str, str]]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )
    _completed_requests_lock: Lock = field(default_factory=Lock, init=False, repr=False)

    def __post_init__(self) -> None:
        self.model_router = ModelRouter(
            provider=self.settings.default_provider,
            primary_model=self.settings.gemini_model,
            fallback_model=self.settings.gemini_model,
            nvidia_model=self.settings.nvidia_model,
        )
        self.omniroute_client = OmnirouteClient(
            base_url=self.settings.omniroute_base_url,
            api_key=self.settings.omniroute_api_key,
        )
        self.gemini_client = GeminiClient(
            api_key=self.settings.gemini_api_key,
            model=self.settings.gemini_model,
        )
        self.nvidia_client = NvidiaClient(
            api_key=self.settings.nvidia_api_key,
            base_url=self.settings.nvidia_base_url,
            model=self.settings.nvidia_model,
        )

    def create_session(self, title: str = "Nova conversa") -> ChatSession:
        return self.session_manager.create_session(title)

    def add_message(self, session_id: str, role: str, content: str) -> ChatMessage:
        session_key = str(session_id)
        self.session_manager.get_session(session_key)
        with self._get_session_lock(session_key):
            return self.session_manager.add_message(session_key, role, content)

    def get_session(self, session_id: str) -> ChatSession:
        session_key = str(session_id)
        self.session_manager.get_session(session_key)
        with self._get_session_lock(session_key):
            return deepcopy(self.session_manager.get_session(session_key))

    def list_sessions(self) -> list[ChatSession]:
        sessions = [self.get_session(session.id) for session in self.session_manager.list_sessions()]
        return sorted(sessions, key=lambda session: session.updated_at, reverse=True)

    def _get_session_lock(self, session_id: str) -> RLock:
        with self._locks_guard:
            return self._session_locks.setdefault(session_id, RLock())

    def _generate_with_provider(
        self,
        model: str,
        prompt: str,
        system_prompt: str,
    ) -> str:
        provider = self.settings.default_provider
        kwargs = {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 2048,
        }
        if provider == "gemini":
            return self.gemini_client.generate(model=model, **kwargs)
        if provider == "nvidia":
            return self.nvidia_client.generate(model=model, **kwargs)
        return self.omniroute_client.generate(model=model, **kwargs)

    def chat(
        self,
        session_id: str,
        message: str,
        request_id: str | None = None,
    ) -> dict[str, str]:
        session_key = str(session_id)
        self.get_session(session_key)
        session_lock = self._get_session_lock(session_key)

        with session_lock:
            session = self.session_manager.get_session(session_key)
            request_key = (session_key, request_id) if request_id else None
            cached_request = None
            if request_key is not None:
                with self._completed_requests_lock:
                    cached_request = self._completed_requests.get(request_key)
            if cached_request is not None:
                previous_message, previous_result = cached_request
                if previous_message != message:
                    raise IdempotencyConflictError(
                        "O identificador do envio já foi usado com outra mensagem."
                    )
                return dict(previous_result)

            history = [
                f"{item.role}: {item.content}"
                for item in session.messages[-(MAX_CONTEXT_MESSAGES - 1) :]
            ]
            prompt = self.prompt_builder.build_prompt(message, history)
            system_prompt = self.prompt_builder.build_system_prompt()

            provider = self.settings.default_provider
            model = self.model_router.resolve_model()

            try:
                response = self._generate_with_provider(model, prompt, system_prompt)
            except (OmnirouteError, GeminiError, NvidiaError) as exc:
                logger.warning("Provedor primário %s indisponível: %s", provider, exc)
                if provider == "gemini":
                    # Fallback para NVIDIA, depois Omniroute
                    try:
                        response = self.nvidia_client.generate(prompt, system_prompt)
                        model = f"nvidia/{self.settings.nvidia_model}"
                    except NvidiaError:
                        try:
                            response = self.omniroute_client.generate(model, prompt, system_prompt)
                            model = f"omniroute/{model}"
                        except OmnirouteError:
                            logger.exception("Todos os provedores de fallback indisponíveis")
                            raise
                elif provider == "nvidia":
                    # Fallback para Gemini, depois Omniroute
                    try:
                        response = self.gemini_client.generate(prompt, system_prompt)
                        model = f"gemini/{self.settings.gemini_model}"
                    except GeminiError:
                        try:
                            response = self.omniroute_client.generate(model, prompt, system_prompt)
                            model = f"omniroute/{model}"
                        except OmnirouteError:
                            logger.exception("Todos os provedores de fallback indisponíveis")
                            raise
                else:
                    # Fallback para NVIDIA, depois Gemini
                    model = self.model_router.resolve_fallback()
                    try:
                        response = self.nvidia_client.generate(prompt, system_prompt)
                        model = f"nvidia/{self.settings.nvidia_model}"
                    except NvidiaError:
                        try:
                            response = self.gemini_client.generate(prompt, system_prompt)
                            model = f"gemini/{self.settings.gemini_model}"
                        except (OmnirouteError, GeminiError):
                            logger.exception("Modelo de fallback indisponível: %s", model)
                            raise

            if session.title == "Nova conversa" and not session.messages:
                session.title = message.strip().splitlines()[0][:60]
            self.add_message(session_id, "user", message)
            self.add_message(session_id, "assistant", response)
            result = {
                "session_id": session_id,
                "title": session.title,
                "response": response,
                "model": model,
            }
            if request_key is not None:
                with self._completed_requests_lock:
                    self._completed_requests[request_key] = (message, dict(result))
                    if len(self._completed_requests) > MAX_COMPLETED_REQUESTS:
                        oldest_request = next(iter(self._completed_requests))
                        del self._completed_requests[oldest_request]
            return result
