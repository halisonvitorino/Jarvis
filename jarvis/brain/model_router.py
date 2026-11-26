from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ModelRouter:
    provider: str
    primary_model: str
    fallback_model: str
    nvidia_model: str
    omniroute_model: str
    _last_used_model: str | None = field(default=None, init=False, repr=False)
    _last_used_provider: str | None = field(default=None, init=False, repr=False)
    _provider_order: list[str] = field(default_factory=list, init=False, repr=False)

    def set_providers(self, providers: list[str]) -> None:
        """Define a ordem de prioridade dos provedores para fallback."""
        self._provider_order = list(providers)

    def resolve_model(self, provider: str | None = None) -> str:
        """Resolve o modelo para o provedor especificado ou o primário."""
        if provider is None:
            provider = self.provider
        model_map = {
            "gemini": self.primary_model,
            "nvidia": self.nvidia_model,
            "omniroute": self.omniroute_model,
        }
        model = model_map.get(provider, self.primary_model)
        self._last_used_model = model
        self._last_used_provider = provider
        return model

    def resolve_fallback(self, failed_provider: str) -> str | None:
        """Resolve o próximo provedor disponível na ordem de fallback."""
        if not self._provider_order:
            return None
        try:
            idx = self._provider_order.index(failed_provider)
        except ValueError:
            return None
        for next_provider in self._provider_order[idx + 1 :]:
            return next_provider
        return None

    def choose_model(self, primary_available: bool = True) -> str:
        model = self.primary_model if primary_available else self.fallback_model
        self._last_used_model = model
        return model

    @property
    def last_used_model(self) -> str | None:
        return self._last_used_model

    @property
    def last_used_provider(self) -> str | None:
        return self._last_used_provider
