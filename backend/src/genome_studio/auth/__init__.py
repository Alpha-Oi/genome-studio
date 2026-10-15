"""Auth layer — заглушка.

Здесь будет авторизация для multi-user режима:
- User, Organization, Membership модели (Фаза A1/B)
- Хеш пароля (bcrypt), JWT (access + refresh)
- Эндпоинты /auth/register, /auth/login, /auth/refresh, /auth/logout
- Защита API через get_current_user

Сейчас модуль содержит только:
- AppMode (local | multi)
- User (dataclass)
- LOCAL_USER (виртуальный пользователь для local mode)
- get_current_user (FastAPI dependency, всегда возвращает LOCAL_USER)

См. docs/15-multiuser-architecture.md и ADR 0007/0008.
"""

from genome_studio.auth.dependencies import get_current_user
from genome_studio.auth.modes import (
    LOCAL_USER,
    AppMode,
    User,
    resolve_mode,
)

__all__ = [
    "AppMode",
    "User",
    "LOCAL_USER",
    "resolve_mode",
    "get_current_user",
]