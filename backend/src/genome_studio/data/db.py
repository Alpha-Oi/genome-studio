"""Database engine and session management.

Uses SQLAlchemy async. SQLite via aiosqlite, Postgres via asyncpg.
Engine is created per-app (stored in app.state), not as a module-level singleton.

Env vars:
    GS_DB_URL: full SQLAlchemy URL (overrides path-based)
    GS_DB_PATH: path to sqlite file
    GS_HOME: base directory (default: user home)
    GS_SKIP_MIGRATIONS: "1" to use create_all instead of alembic (tests)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all models."""


def _default_db_path() -> Path:
    home = os.environ.get("GS_HOME")
    base = Path(home) if home else Path.home()
    return base / ".gs" / "data" / "gs.db"


def get_database_url() -> str:
    """Resolve SQLAlchemy URL from env."""
    explicit = os.environ.get("GS_DB_URL")
    if explicit:
        return explicit

    path = os.environ.get("GS_DB_PATH")
    db_path = Path(path) if path else _default_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def create_engine(url: str | None = None) -> AsyncEngine:
    """Create a new async engine. Each call returns a fresh instance."""
    return create_async_engine(
        url or get_database_url(),
        echo=False,
        future=True,
    )


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    """Initialize the database.

    Two modes:
    1. GS_SKIP_MIGRATIONS=1 (tests): create_all for speed and isolation.
    2. Default (prod/dev): alembic upgrade head for proper versioned migrations.
    """
    # Register all models on Base.metadata (needed for create_all fallback)
    from genome_studio.data import models as _data_models  # noqa: F401
    from genome_studio.warnings import models as _warning_models  # noqa: F401

    if os.environ.get("GS_SKIP_MIGRATIONS") == "1":
        # Fast path for tests: create_all, no alembic
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    # Production path: run alembic migrations
    import asyncio

    from alembic import command
    from alembic.config import Config

    ini_path = Path(__file__).parent.parent.parent.parent.parent / "alembic.ini"
    if not ini_path.is_file():
        # Fallback: if alembic.ini not found (e.g. packaged), use create_all
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    cfg = Config(str(ini_path))
    # alembic command.upgrade is sync, run in thread
    await asyncio.to_thread(command.upgrade, cfg, "head")


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an async session from app.state."""
    factory = request.app.state.session_factory
    async with factory() as session:
        yield session
