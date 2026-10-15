"""Warning Registry: create / list / acknowledge."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.warnings.models import (
    Warning,
    WarningLevel,
    WarningSeverity,
    WarningStatus,
)


class WarningError(ValueError):
    """Invalid warning operation."""


# --- Create --------------------------------------------------------------

async def create_warning(
    session: AsyncSession,
    *,
    project_id: int,
    level: WarningLevel,
    severity: WarningSeverity,
    type: str,
    message: str,
    evidence: list[str] | None = None,
    experiment_id: int | None = None,
    dedupe: bool = True,
) -> Warning:
    """Create a new warning attached to a project.

    If dedupe is True and there is already an open warning with the same
    (project_id, type, message) - returns the existing one instead of
    creating a duplicate.
    """
    if dedupe:
        stmt = (
            select(Warning)
            .where(
                Warning.project_id == project_id,
                Warning.type == type,
                Warning.message == message,
                Warning.status == WarningStatus.OPEN.value,
            )
            .limit(1)
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing

    w = Warning(
        project_id=project_id,
        experiment_id=experiment_id,
        level=level.value,
        severity=severity.value,
        type=type,
        message=message,
        evidence_json=json.dumps(evidence or [], ensure_ascii=False),
    )
    session.add(w)
    await session.commit()
    await session.refresh(w)
    return w


# --- Read ----------------------------------------------------------------

async def list_warnings(
    session: AsyncSession,
    project_id: int,
    status: WarningStatus | None = None,
) -> list[Warning]:
    stmt = select(Warning).where(Warning.project_id == project_id)
    if status is not None:
        stmt = stmt.where(Warning.status == status.value)
    stmt = stmt.order_by(Warning.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_warning(session: AsyncSession, warning_id: int) -> Warning:
    stmt = select(Warning).where(Warning.id == warning_id)
    result = await session.execute(stmt)
    w = result.scalar_one_or_none()
    if w is None:
        raise WarningError(f"warning {warning_id} not found")
    return w


# --- Acknowledge ---------------------------------------------------------

async def acknowledge_warning(
    session: AsyncSession,
    warning_id: int,
    *,
    by: str,
    note: str,
) -> Warning:
    """Acknowledge a warning. Deleting is not allowed by design."""
    w = await get_warning(session, warning_id)
    if w.status == WarningStatus.ACKNOWLEDGED.value:
        raise WarningError(f"warning {warning_id} already acknowledged")
    if not note.strip():
        raise WarningError("acknowledgment note is required")

    w.status = WarningStatus.ACKNOWLEDGED.value
    w.acknowledged_by = by
    w.acknowledged_at = datetime.now(timezone.utc)
    w.acknowledgment_note = note.strip()
    await session.commit()
    await session.refresh(w)
    return w