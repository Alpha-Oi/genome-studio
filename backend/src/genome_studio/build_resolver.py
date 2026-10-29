"""Build Resolver - определяет режим работы приложения.

Критический модуль. Отвечает за разделение prod / internal / dev.
В prod-сборке Dev Override НЕДОСТУПЕН by design.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class BuildMode(str, Enum):
    """Режим сборки."""

    PROD = "prod"
    INTERNAL = "internal"
    DEV = "dev"


class DevModeError(RuntimeError):
    """Dev-режим не может быть активирован."""


@dataclass(frozen=True)
class BuildInfo:
    """Информация о текущей сборке."""

    mode: BuildMode
    dev_override_available: bool
    signing_key_present: bool
    isolated_environment: bool
    reasons: tuple[str, ...]


def _dev_override_available() -> bool:
    """Проверяет, разрешён ли dev-override в этой сборке.

    Читается динамически, чтобы тесты могли менять env.
    В prod-контейнере GS_DEV_OVERRIDE_AVAILABLE жёстко "0".
    """
    return os.environ.get("GS_DEV_OVERRIDE_AVAILABLE") == "1"


def _env_build_mode() -> BuildMode:
    """Читает GS_BUILD. Неизвестное значение -> prod."""
    raw = os.environ.get("GS_BUILD", "prod").strip().lower()
    try:
        return BuildMode(raw)
    except ValueError:
        return BuildMode.PROD


def _gs_home() -> Path:
    """Домашняя директория Genome Studio.

    Приоритет:
    1. GS_HOME env var - для тестов и изоляции.
    2. Path.home() - системный (USERPROFILE на Windows, HOME на Unix).
    """
    gs_home = os.environ.get("GS_HOME")
    if gs_home:
        return Path(gs_home)
    return Path.home()


def _signing_key_path() -> Path:
    """Путь к подписанному dev-ключу."""
    return _gs_home() / ".gs" / "keys" / "dev-signing.key"


def _has_signing_key() -> bool:
    """Проверяет наличие dev-ключа."""
    return _signing_key_path().is_file()


def _is_isolated() -> bool:
    """Грубая проверка изоляции.

    Возвращает True, если внешняя сеть недоступна.
    Настоящая проверка - в Rust-модуле (Build Resolver).
    """
    try:
        with socket.create_connection(("1.1.1.1", 53), timeout=0.5):
            return False
    except (TimeoutError, OSError):
        return True


def resolve_build() -> BuildInfo:
    """Определяет режим сборки со всеми проверками."""
    reasons: list[str] = []
    env_mode = _env_build_mode()

    # 1. Prod-сборка - dev-код физически отсутствует.
    if not _dev_override_available():
        reasons.append("dev_override not compiled in this build")
        return BuildInfo(
            mode=BuildMode.PROD,
            dev_override_available=False,
            signing_key_present=_has_signing_key(),
            isolated_environment=_is_isolated(),
            reasons=tuple(reasons),
        )

    if env_mode != BuildMode.DEV:
        reasons.append(f"GS_BUILD={env_mode.value}, dev not requested")
        return BuildInfo(
            mode=env_mode,
            dev_override_available=True,
            signing_key_present=_has_signing_key(),
            isolated_environment=_is_isolated(),
            reasons=tuple(reasons),
        )

    # 2. Проверка ключа.
    if not _has_signing_key():
        reasons.append("no signing key, falling back to prod")
        return BuildInfo(
            mode=BuildMode.PROD,
            dev_override_available=True,
            signing_key_present=False,
            isolated_environment=_is_isolated(),
            reasons=tuple(reasons),
        )

    # 3. Проверка изоляции.
    if not _is_isolated():
        reasons.append("external network detected, falling back to prod")
        return BuildInfo(
            mode=BuildMode.PROD,
            dev_override_available=True,
            signing_key_present=True,
            isolated_environment=False,
            reasons=tuple(reasons),
        )

    # Все проверки пройдены.
    reasons.append("all dev conditions satisfied")
    return BuildInfo(
        mode=BuildMode.DEV,
        dev_override_available=True,
        signing_key_present=True,
        isolated_environment=True,
        reasons=tuple(reasons),
    )


def is_dev() -> bool:
    """True, если активен dev-режим."""
    return resolve_build().mode == BuildMode.DEV


def is_prod() -> bool:
    """True, если активен prod-режим."""
    return resolve_build().mode == BuildMode.PROD


def require_dev() -> None:
    """Бросает исключение, если текущий режим - не dev."""
    info = resolve_build()
    if info.mode != BuildMode.DEV:
        raise DevModeError(
            f"dev mode required, current mode: {info.mode.value}; "
            f"reasons: {'; '.join(info.reasons)}"
        )
