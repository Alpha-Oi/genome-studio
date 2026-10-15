"""CRUD operations for projects and experiments."""

from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from genome_studio.data.models import Experiment, Project


class NotFoundError(LookupError):
    """Entity not found."""


# --- Projects ------------------------------------------------------------

async def create_project(
    session: AsyncSession,
    name: str,
    description: str = "",
    organism: str = "",
) -> Project:
    p = Project(name=name, description=description, organism=organism)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return p


async def list_projects(session: AsyncSession) -> list[Project]:
    stmt = select(Project).order_by(Project.updated_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_project(session: AsyncSession, project_id: int) -> Project:
    stmt = (
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.experiments))
    )
    result = await session.execute(stmt)
    p = result.scalar_one_or_none()
    if p is None:
        raise NotFoundError(f"project {project_id} not found")
    return p


async def delete_project(session: AsyncSession, project_id: int) -> None:
    p = await get_project(session, project_id)
    await session.delete(p)
    await session.commit()


async def update_project(
    session: AsyncSession,
    project_id: int,
    *,
    name: str | None = None,
    description: str | None = None,
    organism: str | None = None,
) -> Project:
    p = await get_project(session, project_id)
    if name is not None:
        p.name = name
    if description is not None:
        p.description = description
    if organism is not None:
        p.organism = organism
    await session.commit()
    await session.refresh(p)
    return p


# --- Experiments ---------------------------------------------------------

async def create_experiment(
    session: AsyncSession,
    project_id: int,
    kind: str,
    title: str,
    payload: dict | None = None,
) -> Experiment:
    # ensure project exists
    await get_project(session, project_id)
    e = Experiment(
        project_id=project_id,
        kind=kind,
        title=title,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
    )
    session.add(e)
    await session.commit()
    await session.refresh(e)
    return e


async def list_experiments(
    session: AsyncSession, project_id: int
) -> list[Experiment]:
    stmt = (
        select(Experiment)
        .where(Experiment.project_id == project_id)
        .order_by(Experiment.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_experiment(session: AsyncSession, experiment_id: int) -> None:
    stmt = select(Experiment).where(Experiment.id == experiment_id)
    result = await session.execute(stmt)
    e = result.scalar_one_or_none()
    if e is None:
        raise NotFoundError(f"experiment {experiment_id} not found")
    await session.delete(e)
    await session.commit()