"""Configuração do JARVIS carregada de variáveis de ambiente e do arquivo .env."""

from enum import StrEnum
from functools import lru_cache
from pathlib import Path

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from jarvis.core.errors import ConfigurationError

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Environment(StrEnum):
    DEV = "dev"
    PROD = "prod"


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """Configurações tipadas. Caminhos relativos são resolvidos a partir da raiz do projeto."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        validate_default=True,
    )

    app_name: str = "JARVIS"
    environment: Environment = Environment.DEV

    log_level: LogLevel = LogLevel.INFO
    log_dir: Path = Path("logs")
    log_max_bytes: int = Field(default=5 * 1024 * 1024, gt=0)
    log_backup_count: int = Field(default=5, ge=0)

    data_dir: Path = Path("data")
    database_path: Path = Path("data/jarvis.db")

    @field_validator("environment", mode="before")
    @classmethod
    def _normalize_environment(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def _normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

    @field_validator("log_dir", "data_dir", "database_path")
    @classmethod
    def _resolve_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else (PROJECT_ROOT / value).resolve()

    def ensure_directories(self) -> None:
        for directory in (self.log_dir, self.data_dir, self.database_path.parent):
            directory.mkdir(parents=True, exist_ok=True)


def load_settings(**overrides: object) -> Settings:
    """Cria um Settings novo, convertendo erros de validação em ConfigurationError."""
    try:
        return Settings(**overrides)
    except ValidationError as exc:
        raise ConfigurationError(f"Configuração inválida:\n{exc}") from exc


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Settings compartilhado do processo. Use get_settings.cache_clear() para recarregar."""
    return load_settings()
