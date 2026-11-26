"""Utilitarios de retry com backoff exponencial para clientes de IA."""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorador que executa retry com backoff exponencial.

    Args:
        max_retries: Numero maximo de tentativas (além da primeira).
        base_delay: Delay inicial em segundos.
        max_delay: Delay maximo em segundos.
        backoff_factor: Fator multiplicativo para o delay.
        exceptions: Tupla de excecoes que disparam retry.

    Returns:
        Funcao decorada com retry.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = base_delay
            last_exception: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_retries:
                        logger.warning(
                            "Tentativa %d/%d falhou: %s. Retentando em %.1fs...",
                            attempt + 1,
                            max_retries + 1,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            "Todas as %d tentativas falharam para %s: %s",
                            max_retries + 1,
                            func.__name__,
                            exc,
                        )
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator