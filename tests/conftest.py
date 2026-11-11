import logging
import os
import sys
import threading
from collections.abc import Iterator
from pathlib import Path

import pytest

from jarvis.core.config import Settings, get_settings, load_settings


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Remove variáveis JARVIS_* reais e restaura estado global alterado pelos testes."""
    for key in list(os.environ):
        if key.startswith("JARVIS_"):
            monkeypatch.delenv(key)
    get_settings.cache_clear()
    original_excepthook = sys.excepthook
    original_thread_excepthook = threading.excepthook

    yield

    get_settings.cache_clear()
    sys.excepthook = original_excepthook
    threading.excepthook = original_thread_excepthook
    jarvis_logger = logging.getLogger("jarvis")
    for handler in list(jarvis_logger.handlers):
        jarvis_logger.removeHandler(handler)
        handler.close()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Settings apontando logs e banco para um diretório temporário, sem ler o .env."""
    return load_settings(
        _env_file=None,
        log_dir=tmp_path / "logs",
        data_dir=tmp_path / "data",
        database_path=tmp_path / "data" / "jarvis.db",
    )
