from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModelRouter:
    provider: str
    primary_model: str
    fallback_model: str
    nvidia_model: str
    _last_used_model: str | None = field(default=None, init=False, repr=False)

    def resolve_model(self) -> str:
        self._last_used_model = self.primary_model
        return self.primary_model

    def resolve_fallback(self) -> str:
        self._last_used_model = self.fallback_model
        return self.fallback_model

    def choose_model(self, primary_available: bool = True) -> str:
        model = self.primary_model if primary_available else self.fallback_model
        self._last_used_model = model
        return model

    @property
    def last_used_model(self) -> str | None:
        return self._last_used_model
