"""Inicialização do JARVIS: config -> logs -> tratamento de erros -> banco de dados."""

from jarvis import __version__
from jarvis.core.config import Settings, get_settings
from jarvis.core.errors import install_global_handler
from jarvis.core.logger import get_logger, setup_logging
from jarvis.database.connection import connect
from jarvis.database.events import record_event
from jarvis.database.migrator import run_migrations


def bootstrap(settings: Settings | None = None) -> Settings:
    """Prepara a infraestrutura base e retorna as configurações em uso."""
    settings = settings or get_settings()
    settings.ensure_directories()

    setup_logging(settings)
    install_global_handler()
    logger = get_logger("bootstrap")
    logger.info("Iniciando %s v%s (ambiente=%s)", settings.app_name, __version__, settings.environment)

    applied = run_migrations(settings.database_path)
    if applied:
        logger.info("Migrações aplicadas: %s", applied)

    with connect(settings.database_path) as connection:
        record_event(connection, "INFO", "bootstrap", f"startup v{__version__}")

    logger.info("%s pronto. Banco: %s", settings.app_name, settings.database_path)
    return settings
