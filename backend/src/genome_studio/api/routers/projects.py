"""Projects and experiments CRUD."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.data import (
    NotFoundError,
    create_experiment,
    create_project,
    delete_experiment,
    delete_project,
    get_project,
    get_session,
    list_experiments,
    list_projects,
)
from genome_studio.data.payload import (
    PayloadNotJsonError,
    PayloadTooDeepError,
    PayloadTooLargeError,
    validate_payload,
)

router = APIRouter(tags=["projects"])


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field("", max_length=5000)
    organism: str = Field("", max_length=64)


class ProjectResponse(BaseModel):
    project: dict


class ProjectListResponse(BaseModel):
    projects: list[dict]


class ExperimentCreate(BaseModel):
    kind: str = Field(..., min_length=1, max_length=64)
    title: str = Field("", max_length=300)
    payload: dict = Field(default_factory=dict)

    @field_validator("payload")
    @classmethod
    def _validate_payload(cls, v: dict) -> dict:
        try:
            return validate_payload(v)
        except (PayloadTooLargeError, PayloadTooDeepError, PayloadNotJsonError) as e:
            raise ValueError(str(e)) from e


class ExperimentResponse(BaseModel):
    experiment: dict


class ExperimentListResponse(BaseModel):
    experiments: list[dict]


@router.get("/projects", response_model=ProjectListResponse)
async def projects_list(
    session: AsyncSession = Depends(get_session),
) -> ProjectListResponse:
    items = await list_projects(session)
    return ProjectListResponse(projects=[p.to_dict() for p in items])


@router.post("/projects", response_model=ProjectResponse)
async def projects_create(
    req: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    p = await create_project(
        session, name=req.name, description=req.description, organism=req.organism
    )
    return ProjectResponse(project=p.to_dict())


@router.get("/projects/{project_id}", response_model=ProjectResponse)
async def projects_get(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> ProjectResponse:
    try:
        p = await get_project(session, project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return ProjectResponse(project=p.to_dict(include_experiments=True))


@router.delete("/projects/{project_id}")
async def projects_delete(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        await delete_project(session, project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"status": "deleted", "id": project_id}


@router.get(
    "/projects/{project_id}/experiments",
    response_model=ExperimentListResponse,
)
async def experiments_list(
    project_id: int,
    session: AsyncSession = Depends(get_session),
) -> ExperimentListResponse:
    try:
        await get_project(session, project_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    items = await list_experiments(session, project_id)
    return ExperimentListResponse(experiments=[e.to_dict() for e in items])


@router.post(
    "/projects/{project_id}/experiments",
    response_model=ExperimentResponse,
)
async def experiments_create(
    project_id: int,
    req: ExperimentCreate,
    session: AsyncSession = Depends(get_session),
) -> ExperimentResponse:
    try:
        e = await create_experiment(
            session,
            project_id=project_id,
            kind=req.kind,
            title=req.title,
            payload=req.payload,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ExperimentResponse(experiment=e.to_dict())


@router.delete("/experiments/{experiment_id}")
async def experiments_delete(
    experiment_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    try:
        await delete_experiment(session, experiment_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {"status": "deleted", "id": experiment_id}
