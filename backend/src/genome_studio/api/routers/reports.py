"""Project PDF report."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.data import (
    NotFoundError,
    get_project,
    get_session,
    list_experiments,
)
from genome_studio.report import build_project_pdf
from genome_studio.warnings import list_warnings

router = APIRouter(tags=["reports"])


@router.get("/projects/{project_id}/report.pdf")
async def project_report_pdf(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> Response:
    try:
        project = await get_project(session, project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    experiments = await list_experiments(session, project_id)
    warnings = await list_warnings(session, project_id)

    pdf_bytes = build_project_pdf(
        project=project.to_dict(),
        experiments=[e.to_dict() for e in experiments],
        warnings=[w.to_dict() for w in warnings],
    )

    safe_name = (
        "".join(c if c.isalnum() or c in "-_" else "_" for c in project.name)[:60] or "project"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'},
    )
