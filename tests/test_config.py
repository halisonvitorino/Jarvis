from pathlib import Path

import pytest

from jarvis.core.config import (
    PROJECT_ROOT,
    Environment,
    LogLevel,
    Settings,
    get_settings,
    load_settings,
)
from jarvis.core.errors import ConfigurationError


def test_defaults() -> None:
    settings = load_settings(_env_file=None)

    assert settings.app_name == "JARVIS"
    assert settings.environment is Environment.DEV
    assert settings.log_level is LogLevel.INFO
    assert settings.log_dir == Path("logs")
    assert settings.database_path == Path("data/jarvis.db")


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_ENVIRONMENT", "prod")
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("JARVIS_LOG_BACKUP_COUNT", "2")

    settings = load_settings(_env_file=None)

    assert settings.environment is Environment.PROD
    assert settings.log_level is LogLevel.DEBUG
    assert settings.log_backup_count == 2


def test_env_file_is_loaded(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("JARVIS_APP_NAME=Hermes\n", encoding="utf-8")

    settings = load_settings(_env_file=env_file)

    assert settings.app_name == "Hermes"


def test_absolute_paths_are_kept(tmp_path: Path) -> None:
    settings = load_settings(_env_file=None, database_path=tmp_path / "custom.db")

    assert settings.database_path == tmp_path / "custom.db"


def test_invalid_value_raises_configuration_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JARVIS_LOG_LEVEL", "VERBOSE")

    with pytest.raises(ConfigurationError):
        load_settings(_env_file=None)


def test_ensure_directories_creates_missing_dirs(settings: Settings) -> None:
    """Certifica que ensure_directories cria os diretórios necessários."""
    settings.ensure_directories()
    assert settings.log_dir.is_dir()
    assert settings.data_dir.is_dir()
    assert settings.database_path.parent.is_dir()


def test_get_settings_is_cached() -> None:
    assert get_settings() is get_settings()
