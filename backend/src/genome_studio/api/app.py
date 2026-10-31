"""FastAPI app factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from genome_studio import __version__
from genome_studio.api.batch import router as batch_router
from genome_studio.api.mode import router as mode_router
from genome_studio.api.parse import router as parse_router
from genome_studio.api.rate_limit import setup_rate_limiting
from genome_studio.api.related import router as related_router
from genome_studio.api.routers import (
    crispr as crispr_router,
)
from genome_studio.api.routers import (
    export as export_router,
)
from genome_studio.api.routers import (
    goal as goal_router,
)
from genome_studio.api.routers import (
    projects as projects_router,
)
from genome_studio.api.routers import (
    reports as reports_router,
)
from genome_studio.api.routers import (
    simulate as simulate_router,
)
from genome_studio.api.routers import (
    system as system_router,
)
from genome_studio.api.routers import (
    warnings as warnings_router,
)
from genome_studio.build_resolver import resolve_build
from genome_studio.data import (
    create_engine,
    create_session_factory,
    init_db,
)
from genome_studio.knowledge.seed import build_default_kg


def create_app() -> FastAPI:
    info = resolve_build()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine()
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        await init_db(engine)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Genome Studio",
        version=__version__,
        docs_url="/docs" if info.mode.value != "prod" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    setup_rate_limiting(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.info = info
    app.state.kg = build_default_kg()

    app.include_router(mode_router)
    app.include_router(related_router)
    app.include_router(batch_router)
    app.include_router(parse_router)

    app.include_router(system_router.router)
    app.include_router(goal_router.router)
    app.include_router(crispr_router.router)
    app.include_router(simulate_router.router)
    app.include_router(export_router.router)
    app.include_router(projects_router.router)
    app.include_router(warnings_router.router)
    app.include_router(reports_router.router)

    return app
