"""Warnings endpoints: list, acknowledge."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.data import NotFoundError, get_project, get_session
from genome_studio.warnings import (
    WarningError,
    WarningStatus,
    acknowledge_warning,
    list_warnings,
)

router = APIRouter(tags=["warnings"])


class WarningListResponse(BaseModel):
    warnings: list[dict]


class WarningResponse(BaseModel):
    warning: dict


class AcknowledgeRequest(BaseModel):
    by: str = Field(..., min_length=1, max_length=64)
    note: str = Field(..., min_length=1, max_length=2000)


@router.get("/projects/{project_id}/warnings", response_model=WarningListResponse)
async def warnings_list(
    project_id: int,
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> WarningListResponse:
    try:
        await get_project(session, project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    status_enum: WarningStatus | None = None
    if status:
        try:
            status_enum = WarningStatus(status)
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=f"status must be open|acknowledged, got {status!r}",
            ) from e

    items = await list_warnings(session, project_id, status=status_enum)
    return WarningListResponse(warnings=[w.to_dict() for w in items])


@router.post(
    "/warnings/{warning_id}/acknowledge",
    response_model=WarningResponse,
)
async def warnings_acknowledge(
    warning_id: int,
    req: AcknowledgeRequest,
    session: AsyncSession = Depends(get_session),
) -> WarningResponse:
    try:
        w = await acknowledge_warning(session, warning_id, by=req.by, note=req.note)
    except WarningError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return WarningResponse(warning=w.to_dict())
