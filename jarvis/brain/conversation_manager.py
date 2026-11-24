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
from jarvis.memory import MemoryManager

logger = get_logger(__name__)
MAX_CONTEXT_MESSAGES = 20
MAX_COMPLETED_REQUESTS = 1000


class IdempotencyConflictError(RuntimeError):
    """Indica que uma chave de envio já pertence a outra mensagem."""

@dataclass(slots=True)
class ConversationManager:
    session_manager: SessionManager = field(default_factory=SessionManager)
    settings: object = field(default_factory=get_settings)
    memory_manager: MemoryManager = field(default_factory=MemoryManager)
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
        self.memory_manager = MemoryManager()

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
            # Recuperar memórias relevantes da memória de longo prazo
            relevant_memories = self.memory_manager.semantic_search(
                query=message, n_results=5, session_id=session_key
            )
            if relevant_memories:
                history.append(
                    "memórias relevantes: " + " | ".join(relevant_memories)
                )
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
            # Persistir interações na memória de longo prazo
            try:
                self.memory_manager.update_session_memory(session_key, "user", message)
                self.memory_manager.update_session_memory(
                    session_key, "assistant", response
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(
                    "Falha ao persistir interação na memória: %s", exc
                )
            # Extrair e armazenar informações de perfil quando apropriado (JARVIS-A-012)
            try:
                self._extract_and_save_profile(message, session_key)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug(
                    "Falha ao extrair perfil da mensagem: %s", exc
                )
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

    def _extract_and_save_profile(self, message: str, session_key: str) -> None:
        """Extrai informações de perfil (nome, preferências) da mensagem do usuário.

        Usa padrões simples para detectar declarações de nome e preferências,
        salvando-as como perfil de longo prazo do usuário.

        Args:
            message: Mensagem do usuário
            session_key: Identificador da sessão
        """
        import re

        message_lower = message.lower().strip()
        profile_updates: dict[str, list[str]] = {}

        # Detectar declaração de nome: "meu nome é X", "me chamo X", "sou o/a X"
        name_patterns = [
            r"meu nome é\s+([a-zA-ZÀ-ÿ\s]+)",
            r"me chamo\s+([a-zA-ZÀ-ÿ\s]+)",
            r"sou o\s+([a-zA-ZÀ-ÿ\s]+)",
            r"sou a\s+([a-zA-ZÀ-ÿ\s]+)",
        ]
        for pattern in name_patterns:
            match = re.search(pattern, message_lower)
            if match:
                nome = match.group(1).strip().title()
                if len(nome) > 1:
                    profile_updates.setdefault("nome", []).append(nome)
                break

        # Detectar preferências: "gosto de X", "prefiro X"
        pref_patterns = [
            r"gosto de\s+([a-zA-ZÀ-ÿ\s]+)",
            r"prefiro\s+([a-zA-ZÀ-ÿ\s]+)",
            r"gosto muito de\s+([a-zA-ZÀ-ÿ\s]+)",
        ]
        for pattern in pref_patterns:
            match = re.search(pattern, message_lower)
            if match:
                pref = match.group(1).strip()
                if len(pref) > 2:
                    profile_updates.setdefault("preferencias", []).append(pref)
                break

        if profile_updates:
            try:
                existing = self.memory_manager.get_user_profile(session_key)
                merged: dict[str, Any] = dict(existing)
                for key, values in profile_updates.items():
                    current = merged.get(key, [])
                    if isinstance(current, list):
                        merged[key] = list(dict.fromkeys([*current, *values]))
                    else:
                        merged[key] = values
                self.memory_manager.save_user_profile(session_key, merged)
                logger.debug(
                    "Perfil atualizado para sessão %s: %s", session_key, profile_updates
                )
            except Exception as exc:
                logger.debug("Falha ao salvar perfil: %s", exc)
