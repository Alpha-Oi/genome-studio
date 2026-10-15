"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI

from genome_studio import __version__
from genome_studio.build_resolver import resolve_build


def create_app() -> FastAPI:
    """Создаёт FastAPI-приложение."""
    info = resolve_build()

    app = FastAPI(
        title="Genome Studio",
        version=__version__,
        docs_url="/docs" if info.mode.value != "prod" else None,
        redoc_url=None,
    )

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/build")
    async def build_info() -> dict[str, object]:
        return {
            "mode": info.mode.value,
            "dev_override_available": info.dev_override_available,
            "isolated_environment": info.isolated_environment,
        }

    return app
