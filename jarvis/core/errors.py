"""Hierarquia de exceções do JARVIS e tratamento global de erros não capturados."""

import logging
import sys
import threading
from types import TracebackType

_logger = logging.getLogger("jarvis.errors")


class JarvisError(Exception):
    """Exceção base para todos os erros do JARVIS."""


class ConfigurationError(JarvisError):
    """Configuração ausente ou inválida."""


class DatabaseError(JarvisError):
    """Falha ao acessar ou migrar o banco de dados."""


def _handle_exception(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    _logger.critical(
        "Exceção não tratada: %s",
        exc_value,
        exc_info=(exc_type, exc_value, exc_traceback),
    )


def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    if args.exc_value is None:
        return
    thread_name = args.thread.name if args.thread else "desconhecida"
    _logger.critical(
        "Exceção não tratada na thread %s: %s",
        thread_name,
        args.exc_value,
        exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
    )


def install_global_handler() -> None:
    """Direciona exceções não tratadas (processo principal e threads) para o log."""
    sys.excepthook = _handle_exception
    threading.excepthook = _handle_thread_exception
