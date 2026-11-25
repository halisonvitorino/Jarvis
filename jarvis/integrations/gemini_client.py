"""Cliente para integração com Google Gemini API."""
from __future__ import annotations

import json
import os
from typing import Any

import urllib.error
import urllib.request

from jarvis.integrations.ai_client import AIClient, AIClientError

MAX_RESPONSE_BYTES = 1024 * 1024  # 1 MiB máximo
MAX_GENERATED_TOKENS = 2048


class GeminiError(AIClientError):
    """Indica falha ao solicitar uma resposta ao Google Gemini."""


class GeminiClient(AIClient):
    """Cliente para interagir com o Google Generative AI API."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        # Modelos compatíveis com a API v1beta
        self.model = model or "gemini-pro"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = MAX_GENERATED_TOKENS,
    ) -> str:
        """Gera uma resposta usando o Google Gemini API.

        Args:
            prompt: Mensagem do usuário.
            system_prompt: Prompt do sistema (personalidade do assistente).
            model: Nome do modelo (ignorado pelo Gemini, usa self.model).
            temperature: Criatividade da resposta (0.0 a 2.0).
            top_p: Amostragem de núcleo (0.0 a 1.0).
            max_tokens: Número máximo de tokens gerados.

        Returns:
            Texto da resposta gerada.

        Raises:
            GeminiError: Se a solicitação falhar.
        """
        if not self.api_key:
            raise GeminiError(
                "Chave API do Gemini não configurada. "
                "Defina a variável de ambiente GEMINI_API_KEY ou "
                "configure JARVIS_GEMINI_API_KEY no .env"
            )

        # Construir o conteúdo da mensagem
        contents = []

        # Adicionar prompt do sistema se fornecido
        if system_prompt:
            contents.append(
                {
                    "role": "user",
                    "parts": [{"text": system_prompt}],
                }
            )

        # Adicionar mensagem do usuário
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        # Construir o payload
        payload = {
            "contents": contents,
        }

        # Construir a URL da API
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"

        headers = {"Content-Type": "application/json"}

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
                    raise GeminiError(
                        "A resposta do Gemini excede o limite permitido."
                    )

                body = json.loads(response_bytes.decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")[:200]
            raise GeminiError(
                f"A solicitação ao Gemini falhou (HTTP {e.code}): {error_body}"
            ) from e
        except urllib.error.URLError as e:
            raise GeminiError(f"Erro de conexão ao Gemini: {e}") from e
        except Exception as e:
            raise GeminiError(f"Erro inesperado ao chamar Gemini: {e}") from e

        # Extrair a resposta do formato Gemini
        if not isinstance(body, dict):
            raise GeminiError("O Gemini retornou uma resposta inválida.")

        # Navegar pela estrutura de resposta
        try:
            text = (
                body.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
        except (AttributeError, IndexError, KeyError):
            # Tentar estrutura alternativa
            try:
                text = body.get("text", "")
            except Exception:
                raise GeminiError("O Gemini retornou uma resposta inválida.")

        if not isinstance(text, str) or not text.strip():
            raise GeminiError("O Gemini retornou uma resposta vazia.")

        return text.strip()

    def is_available(self) -> bool:
        """Verifica se a chave API do Gemini está configurada."""
        return bool(self.api_key)

    def health_check(self) -> dict:
        """Realiza uma verificação de saúde simples do Gemini."""
        if not self.is_available():
            return {"available": False, "reason": "API key not configured"}
        return {"available": True, "model": self.model, "api_key_configured": True}