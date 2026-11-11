import logging
import sys
import threading

import pytest

from jarvis.core.errors import (
    ConfigurationError,
    DatabaseError,
    JarvisError,
    install_global_handler,
)


def test_error_hierarchy() -> None:
    assert issubclass(ConfigurationError, JarvisError)
    assert issubclass(DatabaseError, JarvisError)


def test_unhandled_exception_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    install_global_handler()

    try:
        raise JarvisError("falha simulada")
    except JarvisError:
        exc_info = sys.exc_info()

    with caplog.at_level(logging.CRITICAL, logger="jarvis.errors"):
        sys.excepthook(*exc_info)

    assert "falha simulada" in caplog.text
    assert caplog.records[-1].exc_info is not None


def test_unhandled_thread_exception_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    install_global_handler()

    def worker() -> None:
        raise RuntimeError("falha na thread")

    with caplog.at_level(logging.CRITICAL, logger="jarvis.errors"):
        thread = threading.Thread(target=worker, name="worker-teste")
        thread.start()
        thread.join()

    assert "worker-teste" in caplog.text
    assert "falha na thread" in caplog.text
