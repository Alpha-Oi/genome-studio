"""Конфигурация приложения.

Все настройки читаются из переменных окружения с префиксом GS_.
Использует pydantic-settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from genome_studio.build_resolver import BuildMode, resolve_build


class Settings(BaseSettings):
    """Настройки Genome Studio."""

    model_config = SettingsConfigDict(
        env_prefix="GS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Основное
    app_name: str = "Genome Studio"
    debug: bool = False

    # База данных
    database_url: str = Field(
        default="postgresql+asyncpg://gs:gs@localhost:5432/gs",
        description="PostgreSQL DSN",
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Файлы
    data_dir: Path = Field(default=Path.home() / ".gs" / "data")

    # Логи
    log_level: str = "INFO"
    log_json: bool = False

    @property
    def build_mode(self) -> BuildMode:
        """Текущий режим сборки."""
        return resolve_build().mode

    @property
    def log_dir(self) -> Path:
        """Каталог логов, зависит от режима сборки."""
        base = Path.home() / ".gs"
        mode = self.build_mode.value
        return base / mode / "logs"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Возвращает singleton настроек."""
    return Settings()
