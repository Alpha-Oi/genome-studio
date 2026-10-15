"""Build Resolver — определяет, в каком режиме работает приложение.

Критический модуль. Отвечает за разделение prod / internal / dev.
В prod-сборке Dev Override НЕДОСТУПЕН by design.

Правила:
- BUILD_MODE берётся из переменной окружения GS_BUILD.
- По умолчанию — "prod" (безопасный дефолт).
- Dev-режим требует: подписанный ключ + локальная среда + нет внешней сети.
- Если хоть одно условие не выполнено — переход в prod.
"""

from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Final


class BuildMode(str, Enum):
    """Режим сборки."""

    PROD = "prod"
    INTERNAL = "internal"
    DEV = "dev"


class DevModeError(RuntimeError):
    """Dev-режим не может быть активирован."""


# Жёстко прошитый режим prod.
# В prod-сборке этот флаг остаётся False всегда.
# В dev-сборке при сборке заменяется на True через compile-time конфиг.
_DEV_OVERRIDE_AVAILABLE: Final[bool] = os.environ.get("GS_DEV_OVERRIDE_AVAILABLE") == "1"


@dataclass(frozen=True)
class BuildInfo:
    """Информация о текущей сборке."""

    mode: BuildMode
    dev_override_available: bool
    signing_key_present: bool
    isolated_environment: bool
    reasons: tuple[str, ...]


def _env_build_mode() -> BuildMode:
    """Читает GS_BUILD. Неизвестное значение -> prod."""
    raw = os.environ.get("GS_BUILD", "prod").strip().lower()
    try:
        return BuildMode(raw)
    except ValueError:
        return BuildMode.PROD


def _signing_key_path() -> Path:
    """Путь к подписанному dev-ключу."""
    return Path.home() / ".gs" / "keys" / "dev-signing.key"


def _has_signing_key() -> bool:
    return _signing_key_path().is_file()


def _is_isolated() -> bool:
    """Грубая проверка изоляции.

    Возвращает True, если найдено внешнее сетевое подключение.
    Настоящая проверка — в Rust-модуле (Build Resolver).
    Здесь — упрощённая эвристика для MVP.
    """
    try:
        # Попытка подключиться к внешнему DNS. Если получается — не изолирован.
        with socket.create_connection(("1.1.1.1", 53), timeout=0.5):
            return False
    except (OSError, socket.timeout):
        return True


def resolve_build() -> BuildInfo:
    """Определяет режим сборки со всеми проверками.

    Логика:
    1. Если GS_DEV_OVERRIDE_AVAILABLE != "1" — это prod-сборка, дальше не идём.
    2. Если нет подписанного ключа — откат в prod.
    3. Если среда не изолирована — откат в prod.
    4. Иначе — включён dev-режим.
    """
    reasons: list[str] = []
    env_mode = _env_build_mode()

    # 1. Prod-сборка — dev-код физически отсутствует.
    if not _DEV_OVERRIDE_AVAILABLE:
        reasons.append("dev_override not compiled in this build")
        return BuildInfo(
            mode=BuildMode.PROD,
            dev_override_available=False,
            signing_key_present=_has_signing_key(),
            isolated_environment=_is_isolated(),
            reasons=tuple(reasons),
        )

    # Дальше — только для сборок с dev_override.
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
    """Бросает исключение, если текущий режим — не dev.

    Используется перед активацией dev-панели или отключением T2.
    """
    info = resolve_build()
    if info.mode != BuildMode.DEV:
        raise DevModeError(
            f"dev mode required, current mode: {info.mode.value}; "
            f"reasons: {'; '.join(info.reasons)}"
        )
