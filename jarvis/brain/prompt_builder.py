from __future__ import annotations

from typing import Iterable


class PromptBuilder:
    """Constrói prompts simples para a conversa atual do assistente."""

    system_prompt = (
        "Você é J.A.R.V.I.S., um assistente pessoal local útil, direto e prestativo. "
        "Responda de forma clara, curta e objetiva."
    )

    @classmethod
    def build_prompt(cls, user_message: str, history: Iterable[str] = ()) -> str:
        messages = list(history)
        if user_message:
            messages.append(f"user: {user_message}")
        return "\n".join(messages)

    @classmethod
    def build_system_prompt(cls) -> str:
        return cls.system_prompt
