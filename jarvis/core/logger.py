"""Sistema de logs: console + arquivo rotativo sob o logger raiz "jarvis"."""

import logging
import sys
from logging.handlers import RotatingFileHandler

from jarvis.core.config import Settings

ROOT_LOGGER_NAME = "jarvis"
LOG_FILE_NAME = "jarvis.log"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_HANDLER_MARKER = "_jarvis_handler"


def setup_logging(settings: Settings) -> logging.Logger:
    """Configura o logger "jarvis". Pode ser chamado várias vezes sem duplicar handlers."""
    logger = logging.getLogger(ROOT_LOGGER_NAME)
    logger.setLevel(settings.log_level.value)

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_MARKER, False):
            logger.removeHandler(handler)
            handler.close()

    settings.log_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    console_handler = logging.StreamHandler(sys.stderr)
    file_handler = RotatingFileHandler(
        settings.log_dir / LOG_FILE_NAME,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    for handler in (console_handler, file_handler):
        handler.setFormatter(formatter)
        setattr(handler, _HANDLER_MARKER, True)
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger filho de "jarvis" (ex.: get_logger("database") -> "jarvis.database")."""
    if name == ROOT_LOGGER_NAME or name.startswith(f"{ROOT_LOGGER_NAME}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{ROOT_LOGGER_NAME}.{name}")
