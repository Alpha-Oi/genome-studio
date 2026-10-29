"""Related history: find similar past experiments."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.data import get_session
from genome_studio.data.models import Experiment, Project

router = APIRouter(tags=["related"])


@router.get("/related")
async def find_related(
    gene: str = Query(..., min_length=1, max_length=64),
    organism: str = Query(..., min_length=1, max_length=64),
    intent: str = Query(..., min_length=1, max_length=64),
    limit: int = Query(5, ge=1, le=50),
    exclude_project_id: int | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Find past plan experiments with same gene + organism + intent.

    Returns a list of matches (newest first). Requires exact match on all
    three fields. This is intentionally simple — Phase C1 from
    docs/15-multiuser-architecture.md.
    """
    stmt = (
        select(Experiment).where(Experiment.kind == "plan").order_by(Experiment.created_at.desc())
    )
    result = await session.execute(stmt)
    experiments = result.scalars().all()

    matches: list[dict] = []
    for exp in experiments:
        try:
            payload = json.loads(exp.payload_json)
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        goal = payload.get("goal") or {}
        target = goal.get("target") or {}
        if (
            target.get("gene") == gene
            and target.get("organism") == organism
            and goal.get("intent") == intent
        ):
            intervention = payload.get("intervention") or {}
            matches.append(
                {
                    "experiment_id": exp.id,
                    "project_id": exp.project_id,
                    "title": exp.title,
                    "created_at": exp.created_at.isoformat(),
                    "intervention_kind": intervention.get("kind"),
                    "predicted_effect": intervention.get("predicted_effect"),
                    "off_target_risk": intervention.get("off_target_risk"),
                    "essentiality_risk": intervention.get("essentiality_risk"),
                }
            )
            if len(matches) >= limit:
                break

    # attach project names
    if matches:
        pids = list({m["project_id"] for m in matches})
        pstmt = select(Project).where(Project.id.in_(pids))
        presult = await session.execute(pstmt)
        projects = {p.id: p.name for p in presult.scalars().all()}
        for m in matches:
            m["project_name"] = projects.get(m["project_id"], "?")

    return {
        "related": matches,
        "criteria": {
            "gene": gene,
            "organism": organism,
            "intent": intent,
        },
    }
