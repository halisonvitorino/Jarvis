"""Configuração do JARVIS carregada de variáveis de ambiente e do arquivo .env."""
from __future__ import annotations

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

    # Omniroute Configuration
    omniroute_base_url: str = Field(default="http://127.0.0.1:20128/v1")
    omniroute_api_key: str = Field(default="")

    # Gemini Configuration
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-pro-latest")

    # NVIDIA NIM Configuration
    nvidia_base_url: str = Field(default="https://integrate.api.nvidia.com/v1")
    nvidia_api_key: str = Field(default="")
    nvidia_model: str = Field(default="nvidia/nemotron-3-ultra-550b-a55b")

    default_provider: str = Field(default="gemini")

    # Omniroute model (alternativo)
    omniroute_model: str = Field(default="omniroute/default")

    @field_validator("gemini_api_key")
    @classmethod
    def _validate_gemini_key(cls, value: str, info) -> str:
        """Valida que a chave do Gemini esteja configurada quando é o provedor padrão."""
        provider = info.data.get("default_provider", "gemini")
        if provider == "gemini" and not value.strip():
            raise ValueError(
                "JARVIS_GEMINI_API_KEY é obrigatória quando default_provider='gemini'. "
                "Configure no arquivo .env."
            )
        return value

    @field_validator("nvidia_api_key")
    @classmethod
    def _validate_nvidia_key(cls, value: str, info) -> str:
        """Valida que a chave da NVIDIA esteja configurada quando é o provedor padrão."""
        provider = info.data.get("default_provider", "gemini")
        if provider == "nvidia" and not value.strip():
            raise ValueError(
                "JARVIS_NVIDIA_API_KEY é obrigatória quando default_provider='nvidia'. "
                "Configure no arquivo .env."
            )
        return value

    @field_validator("omniroute_api_key")
    @classmethod
    def _validate_omniroute_key(cls, value: str, info) -> str:
        """Valida que a chave do Omniroute esteja configurada quando é o provedor padrão."""
        provider = info.data.get("default_provider", "gemini")
        if provider == "omniroute" and not value.strip():
            raise ValueError(
                "JARVIS_OMNIROUTE_API_KEY é obrigatória quando default_provider='omniroute'. "
                "Configure no arquivo .env."
            )
        return value

    def ensure_directories(self) -> None:
        """Cria os diretórios necessários para o funcionamento do JARVIS."""
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