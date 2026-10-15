"""Режимы работы и модель пользователя.

Сейчас:
- AppMode — enum (local / multi)
- User — dataclass (id, email, name, is_admin)
- LOCAL_USER — виртуальный пользователь для local mode
- resolve_mode() — читает режим из env GS_MODE (default: local)

В будущем (Фаза A0):
- resolve_mode() начнёт читать из таблицы app_settings
- Появится переключатель режима через UI

ВАЖНО: без изменения сигнатур. Код, который сейчас вызывает
resolve_mode(), продолжит работать.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum


class AppMode(str, Enum):
    """Режим работы программы."""

    LOCAL = "local"
    MULTI = "multi"


@dataclass(frozen=True)
class User:
    """Пользователь.

    В local mode — виртуальный LOCAL_USER.
    В multi mode (Фаза A1) — реальный пользователь из БД.
    """

    id: int
    email: str
    name: str
    is_admin: bool = False

    @property
    def is_local(self) -> bool:
        return self.id == 0


# Виртуальный пользователь для local mode.
# Не существует в БД. Все проекты в local mode принадлежат ему.
LOCAL_USER = User(
    id=0,
    email="local@localhost",
    name="Local user",
    is_admin=True,
)


def resolve_mode() -> AppMode:
    """Определить текущий режим работы.

    Сейчас — из env GS_MODE.
    Позже (Фаза A0) — из таблицы app_settings с fallback на env.
    """
    raw = os.environ.get("GS_MODE", "local").strip().lower()
    try:
        return AppMode(raw)
    except ValueError:
        return AppMode.LOCAL