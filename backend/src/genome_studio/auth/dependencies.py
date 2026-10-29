"""FastAPI dependencies для авторизации.

Сейчас get_current_user() всегда возвращает LOCAL_USER.
После Фазы A1 начнёт читать JWT из Authorization: Bearer
и возвращать реального пользователя.

ВАЖНО: сигнатура не меняется. Эндпоинты уже сейчас пишутся как

    from genome_studio.auth import get_current_user
    from fastapi import Depends

    @app.get("/projects")
    async def list_projects(user = Depends(get_current_user)):
        ...

И при переходе в multi mode им не нужно ничего менять.
"""

from __future__ import annotations

from genome_studio.auth.modes import LOCAL_USER, User, resolve_mode


async def get_current_user() -> User:
    """Вернуть текущего пользователя.

    Local mode: LOCAL_USER (без проверки).
    Multi mode: (TODO Фаза A1) JWT из Authorization header.

    Пока реализован только local mode. При GS_MODE=multi и
    отсутствии реализации — возвращаем LOCAL_USER с предупреждением,
    чтобы не сломать существующий код.
    """
    mode = resolve_mode()
    if mode.value == "local":
        return LOCAL_USER

    # TODO (Фаза A1): читать JWT, валидировать, загружать User из БД.
    # Пока — fallback на local, чтобы multi-эндпоинты не падали
    # в нереализованном режиме.
    return LOCAL_USER
