"""Mode-related endpoints.

Сейчас: GET /mode — текущий режим и пользователь.
Позже: POST /mode — переключение (Фаза A0).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from genome_studio.auth import User, get_current_user, resolve_mode


router = APIRouter(tags=["mode"])


@router.get("/mode")
async def get_mode(user: User = Depends(get_current_user)) -> dict:
    """Текущий режим работы и пользователь.

    Local mode: mode=local, user.id=0, user.is_admin=True.
    Multi mode (после Фазы A1): реальный пользователь из JWT.
    """
    return {
        "mode": resolve_mode().value,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_admin": user.is_admin,
            "is_local": user.is_local,
        },
        "available_modes": ["local", "multi"],
        "switchable": False,  # станет True в Фазе A0
    }