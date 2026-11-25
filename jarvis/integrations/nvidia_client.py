"""Cliente para integração com a API da NVIDIA NIM (formato compatível com OpenAI)."""
from __future__ import annotations

import json
import os
from typing import Any

import urllib.error
import urllib.request

from jarvis.integrations.ai_client import AIClient, AIClientError

MAX_RESPONSE_BYTES = 1024 * 1024  # 1 MiB máximo
MAX_GENERATED_TOKENS = 16384


class NvidiaError(AIClientError):
    """Indica falha ao solicitar uma resposta à API da NVIDIA NIM."""


class NvidiaClient(AIClient):
    """Cliente para interagir com a API da NVIDIA NIM (compatível com OpenAI)."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("JARVIS_NVIDIA_API_KEY", "") or os.getenv("NVIDIA_API_KEY", "")
        self.base_url = (base_url or "https://integrate.api.nvidia.com/v1").rstrip("/")
        self.model = model or "nvidia/nemotron-3-ultra-550b-a55b"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = MAX_GENERATED_TOKENS,
    ) -> str:
        """Gera uma resposta usando a API da NVIDIA NIM.

        Args:
            prompt: Mensagem do usuário
            system_prompt: Prompt do sistema (personalidade do assistente)
            temperature: Criatividade da resposta (0.0 a 2.0)
            top_p: Amostragem de núcleo (0.0 a 1.0)
            max_tokens: Número máximo de tokens gerados

        Returns:
            Resposta do modelo como texto

        Raises:
            NvidiaError: Se a solicitação falhar
        """
        if not self.api_key:
            raise NvidiaError(
                "Chave API da NVIDIA não configurada. "
                "Defina a variável de ambiente NVIDIA_API_KEY ou "
                "configure JARVIS_NVIDIA_API_KEY no .env"
            )

        # Construir mensagens no formato OpenAI
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # Construir o payload
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
        }

        # Construir a URL da API
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=60) as response:
                response_bytes = response.read(MAX_RESPONSE_BYTES + 1)
                if len(response_bytes) > MAX_RESPONSE_BYTES:
                    raise NvidiaError(
                        "A resposta da NVIDIA excede o limite permitido."
                    )

                body = json.loads(response_bytes.decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")[:200]
            raise NvidiaError(
                f"A solicitação à NVIDIA falhou (HTTP {e.code}): {error_body}"
            ) from e
        except urllib.error.URLError as e:
            raise NvidiaError(f"Erro de conexão à NVIDIA: {e}") from e
        except Exception as e:
            raise NvidiaError(f"Erro inesperado ao chamar NVIDIA: {e}") from e

        # Extrair a resposta do formato OpenAI-compatível
        if not isinstance(body, dict):
            raise NvidiaError("A NVIDIA retornou uma resposta inválida.")

        try:
            text = body.get("choices", [{}])[0].get("message", {}).get("content", "")
        except (AttributeError, IndexError, KeyError):
            raise NvidiaError("A NVIDIA retornou uma resposta inválida.")

        if not isinstance(text, str) or not text.strip():
            raise NvidiaError("A NVIDIA retornou uma resposta vazia.")

        return text.strip()

    def is_available(self) -> bool:
        """Verifica se a chave API da NVIDIA está configurada."""
        return bool(self.api_key)

    def health_check(self) -> dict:
        """Realiza uma verificação de saúde simples da NVIDIA."""
        if not self.is_available():
            return {"available": False, "reason": "API key not configured"}
        return {"available": True, "model": self.model, "api_key_configured": True}