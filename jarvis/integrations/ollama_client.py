from __future__ import annotations

import json
import urllib.error as error
import urllib.request as request
from typing import Any

from jarvis.integrations.ai_client import AIClient, AIClientError

MAX_RESPONSE_BYTES = 1024 * 1024
MAX_GENERATED_TOKENS = 2048


class OmnirouteError(AIClientError):
    """Indica falha ao solicitar uma resposta ao serviço Omniroute."""


class OmnirouteClient(AIClient):
    """Cliente para interagir com o serviço Omniroute."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or "http://127.0.0.1:20128/v1").rstrip("/")
        self.api_key = api_key or os.getenv("OMNIROUTE_API_KEY", "")

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = MAX_GENERATED_TOKENS,
    ) -> str:
        """Gera uma resposta usando o serviço Omniroute.

        Args:
            prompt: Mensagem do usuário.
            system_prompt: Prompt do sistema (personalidade do assistente).
            model: Nome do modelo a ser usado.
            temperature: Criatividade da resposta (0.0 a 2.0).
            top_p: Amostragem de núcleo (0.0 a 1.0).
            max_tokens: Número máximo de tokens gerados.

        Returns:
            Texto da resposta gerada.

        Raises:
            OmnirouteError: Se a solicitação falhar.
        """
        if model is None:
            model = "default"

        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "system": system_prompt,
            "max_tokens": max_tokens,
        }

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            req = request.Request(
                f"{self.base_url}/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with request.urlopen(req, timeout=60) as response:
                response_bytes = response.read(MAX_RESPONSE_BYTES + 1)
                if len(response_bytes) > MAX_RESPONSE_BYTES:
                    raise OmnirouteError("A resposta do Omniroute excede o limite permitido.")
                body = json.loads(response_bytes.decode("utf-8"))
        except (
            error.URLError,
            OSError,
        ) as exc:
            raise OmnirouteError("A solicitação ao Omniroute falhou.") from exc

        if not isinstance(body, dict):
            raise OmnirouteError("O Omniroute retornou uma resposta inválida.")

        text = body.get("choices", [{}])[0].get("message", {}).get("content")
        if not isinstance(text, str) or not text.strip():
            raise OmnirouteError("O Omniroute retornou uma resposta vazia.")
        return text.strip()
