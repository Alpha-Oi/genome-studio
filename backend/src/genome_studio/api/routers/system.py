"""System endpoints: health, build info."""

from __future__ import annotations

from fastapi import APIRouter, Request

from genome_studio import __version__

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/build")
async def build_info(request: Request) -> dict[str, object]:
    info = request.app.state.info
    return {
        "mode": info.mode.value,
        "dev_override_available": info.dev_override_available,
        "isolated_environment": info.isolated_environment,
    }
