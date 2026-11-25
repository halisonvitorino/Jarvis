"""Classe base e tipos para clientes de provedores de IA."""
from __future__ import annotations

from abc import ABC, abstractmethod


class AIClientError(RuntimeError):
    """Exceção base para erros de clientes de provedores de IA."""


class AIClient(ABC):
    """Interface abstrata para clientes de provedores de IA.

    Todo cliente de provedor (Gemini, NVIDIA, Omniroute, etc.) deve
    implementar esta interface para garantir consistência no sistema.
    """

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        top_p: float = 0.95,
        max_tokens: int = 2048,
    ) -> str:
        """Gera uma resposta de IA para o prompt fornecido.

        Args:
            prompt: Mensagem do usuário.
            system_prompt: Instrução do sistema (personalidade do assistente).
            model: Nome do modelo a ser usado (opcional, depende do provedor).
            temperature: Criatividade da resposta (0.0 a 2.0).
            top_p: Amostragem de núcleo (0.0 a 1.0).
            max_tokens: Número máximo de tokens gerados.

        Returns:
            Texto da resposta gerada.

        Raises:
            AIClientError: Se a solicitação falhar.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o provedor de IA está disponível para conexão."""

    @abstractmethod
    def health_check(self) -> dict:
        """Realiza uma verificação de saúde do provedor, retornando status e metadados.

        Returns:
            Dicionário com informações de saúde do provedor.
        """