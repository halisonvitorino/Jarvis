import logging
from pathlib import Path

from jarvis.core.config import Settings, load_settings
from jarvis.core.logger import LOG_FILE_NAME, get_logger, setup_logging


def _flush(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.flush()


def test_setup_logging_writes_to_file(settings: Settings) -> None:
    logger = setup_logging(settings)

    get_logger("test").info("mensagem de teste")
    _flush(logger)

    content = (settings.log_dir / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "mensagem de teste" in content
    assert "| INFO     | jarvis.test |" in content


def test_setup_logging_is_idempotent(settings: Settings) -> None:
    setup_logging(settings)
    logger = setup_logging(settings)

    assert len(logger.handlers) == 2


def test_log_level_is_applied(tmp_path: Path) -> None:
    settings = load_settings(_env_file=None, log_dir=tmp_path, log_level="WARNING")
    logger = setup_logging(settings)

    get_logger("test").info("não deve aparecer")
    get_logger("test").warning("deve aparecer")
    _flush(logger)

    content = (tmp_path / LOG_FILE_NAME).read_text(encoding="utf-8")
    assert "não deve aparecer" not in content
    assert "deve aparecer" in content


def test_get_logger_namespacing() -> None:
    assert get_logger("database").name == "jarvis.database"
    assert get_logger("jarvis.core").name == "jarvis.core"
    assert get_logger("jarvis").name == "jarvis"
