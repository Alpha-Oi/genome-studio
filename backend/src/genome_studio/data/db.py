"""Database engine and session management.

Uses SQLite via aiosqlite. For production switch to Postgres by
setting GS_DB_URL.

Env vars:
    GS_DB_URL: full SQLAlchemy URL (overrides path-based)
    GS_DB_PATH: path to sqlite file
    GS_HOME: base directory (default: user home)
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Declarative base for all models."""


_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


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


def get_engine() -> AsyncEngine:
    """Singleton engine."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=False,
            future=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Singleton session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
        )
    return _session_factory


async def init_db() -> None:
    """Initialize the database.

    Two modes:
    1. GS_SKIP_MIGRATIONS=1 (tests): create_all for speed and isolation.
    2. Default (prod/dev): alembic upgrade head for proper versioned migrations.
    """
    import os

    # Register all models on Base.metadata (needed for create_all fallback)
    from genome_studio.data import models as _data_models  # noqa: F401
    from genome_studio.warnings import models as _warning_models  # noqa: F401

    if os.environ.get("GS_SKIP_MIGRATIONS") == "1":
        # Fast path for tests: create_all, no alembic
        engine = get_engine()
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
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        return

    cfg = Config(str(ini_path))
    # alembic command.upgrade is sync, run in thread
    await asyncio.to_thread(command.upgrade, cfg, "head")


async def dispose_engine() -> None:
    """Dispose engine (for tests / shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an async session."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
