import sys

import pytest

from jarvis.__main__ import main
from jarvis.core.bootstrap import bootstrap
from jarvis.core.config import Settings
from jarvis.core.logger import LOG_FILE_NAME
from jarvis.database.connection import connect
from jarvis.database.events import recent_events


def test_bootstrap_prepares_infrastructure(settings: Settings) -> None:
    bootstrap(settings)

    assert (settings.log_dir / LOG_FILE_NAME).is_file()
    assert settings.database_path.is_file()
    assert sys.excepthook.__module__ == "jarvis.core.errors"
    with connect(settings.database_path) as connection:
        events = recent_events(connection)
    assert events[0]["source"] == "bootstrap"


def test_bootstrap_can_run_twice(settings: Settings) -> None:
    bootstrap(settings)
    bootstrap(settings)

    with connect(settings.database_path) as connection:
        assert len(recent_events(connection)) == 2


def test_main_returns_error_on_invalid_configuration(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("JARVIS_LOG_MAX_BYTES", "0")

    assert main() == 1
    assert "Configuração inválida" in capsys.readouterr().err
