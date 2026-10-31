"""Goal -> plan endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.data import NotFoundError, get_project, get_session
from genome_studio.intent.parser import ParseError, parse_goal
from genome_studio.reasoning.mapper import map_goal
from genome_studio.reasoning.planner import build_plan
from genome_studio.warnings import warnings_from_plan

router = APIRouter(tags=["goal"])


class GoalRequest(BaseModel):
    text: str
    project_id: int | None = None


class PlanResponse(BaseModel):
    plan: dict
    warning_ids: list[int] = []


@router.post("/goal", response_model=PlanResponse)
async def create_goal(
    request: Request,
    req: GoalRequest,
    session: AsyncSession = Depends(get_session),
) -> PlanResponse:
    kg = request.app.state.kg
    try:
        goal = parse_goal(req.text)
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    iset = map_goal(goal, kg)
    try:
        plan = build_plan(goal, kg)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

    warning_ids: list[int] = []
    if req.project_id is not None:
        try:
            await get_project(session, req.project_id)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

        warning_ids = await warnings_from_plan(
            session,
            project_id=req.project_id,
            plan=plan,
            iset=iset,
        )

    return PlanResponse(plan=plan.to_dict(), warning_ids=warning_ids)
