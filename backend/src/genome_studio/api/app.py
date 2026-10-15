"""FastAPI app factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio import __version__
from genome_studio.build_resolver import resolve_build
from genome_studio.crispr.designer import design_guides
from genome_studio.crispr.offtarget import find_offtargets, off_target_risk
from genome_studio.data import (
    NotFoundError,
    create_experiment,
    create_project,
    delete_project,
    dispose_engine,
    get_project,
    get_session,
    init_db,
    list_experiments,
    list_projects,
)
from genome_studio.intent.parser import ParseError, parse_goal
from genome_studio.knowledge.seed import build_default_kg
from genome_studio.reasoning.mapper import map_goal
from genome_studio.reasoning.planner import build_plan
from genome_studio.simulation import (
    Edit,
    EditError,
    EditKind,
    apply_edit,
    build_consequence_tree,
    predict_effect,
)
from genome_studio.warnings import (
    WarningError,
    WarningStatus,
    acknowledge_warning,
    get_warning,
    list_warnings,
    warnings_from_effect,
    warnings_from_plan,
)


# --- Schemas -------------------------------------------------------------

class GoalRequest(BaseModel):
    text: str
    project_id: int | None = None


class PlanResponse(BaseModel):
    plan: dict
    warning_ids: list[int] = []


class CrisprRequest(BaseModel):
    sequence: str = Field(..., min_length=23, max_length=100_000)
    top_n: int = Field(5, ge=1, le=50)
    min_score: float = Field(0.5, ge=0.0, le=1.0)


class CrisprResponse(BaseModel):
    guides: list[dict]


class OffTargetRequest(BaseModel):
    guide_spacer: str = Field(..., min_length=20, max_length=20)
    reference: str = Field(..., min_length=23, max_length=1_000_000)
    max_mismatches: int = Field(4, ge=0, le=10)
    reference_label: str = Field("ref", max_length=64)


class OffTargetResponse(BaseModel):
    hits: list[dict]
    summary: dict


class SimulateEditRequest(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=100_000)
    gene_name: str = Field("gene", max_length=64)
    kind: str
    position: int = Field(..., ge=0)
    ref: str = Field("", max_length=1000)
    alt: str = Field("", max_length=1000)
    project_id: int | None = None


class SimulateEditResponse(BaseModel):
    edited_sequence: str
    effect: dict
    consequence_tree: dict
    warning_ids: list[int] = []


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


class ExperimentResponse(BaseModel):
    experiment: dict


class ExperimentListResponse(BaseModel):
    experiments: list[dict]


class WarningListResponse(BaseModel):
    warnings: list[dict]


class WarningResponse(BaseModel):
    warning: dict


class AcknowledgeRequest(BaseModel):
    by: str = Field(..., min_length=1, max_length=64)
    note: str = Field(..., min_length=1, max_length=2000)


# --- Helpers -------------------------------------------------------------

def _clean_dna(seq: str) -> str:
    seq = seq.upper()
    return "".join(b for b in seq if b in "ACGTN")


# --- App factory ---------------------------------------------------------

def create_app() -> FastAPI:
    info = resolve_build()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await init_db()
        yield
        await dispose_engine()

    app = FastAPI(
        title="Genome Studio",
        version=__version__,
        docs_url="/docs" if info.mode.value != "prod" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

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

    kg = build_default_kg()

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/build")
    async def build_info() -> dict[str, object]:
        return {
            "mode": info.mode.value,
            "dev_override_available": info.dev_override_available,
            "isolated_environment": info.isolated_environment,
        }

    # --- Goal / Plan ---------------------------------------------------

    @app.post("/goal", response_model=PlanResponse)
    async def create_goal(
        req: GoalRequest,
        session: AsyncSession = Depends(get_session),
    ) -> PlanResponse:
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

    # --- CRISPR --------------------------------------------------------

    @app.post("/crispr/design", response_model=CrisprResponse)
    async def crispr_design(req: CrisprRequest) -> CrisprResponse:
        seq = _clean_dna(req.sequence)
        if len(seq) < 23:
            raise HTTPException(status_code=422, detail="Sequence too short")

        guides = design_guides(seq, top_n=req.top_n, min_score=req.min_score)
        if not guides:
            raise HTTPException(
                status_code=422,
                detail="No guide RNAs found with given criteria",
            )
        return CrisprResponse(guides=[g.to_dict() for g in guides])

    @app.post("/crispr/offtarget", response_model=OffTargetResponse)
    async def crispr_offtarget(req: OffTargetRequest) -> OffTargetResponse:
        guide = _clean_dna(req.guide_spacer)
        ref = _clean_dna(req.reference)
        if len(guide) != 20:
            raise HTTPException(status_code=422, detail="guide_spacer must be 20 nt")
        if len(ref) < 23:
            raise HTTPException(status_code=422, detail="reference too short")

        hits = find_offtargets(
            guide_spacer=guide,
            reference=ref,
            max_mismatches=req.max_mismatches,
            reference_label=req.reference_label,
        )
        summary = off_target_risk(hits)
        return OffTargetResponse(hits=[h.to_dict() for h in hits], summary=summary)

    # --- Simulation ----------------------------------------------------

    @app.post("/simulate/edit", response_model=SimulateEditResponse)
    async def simulate_edit(
        req: SimulateEditRequest,
        session: AsyncSession = Depends(get_session),
    ) -> SimulateEditResponse:
        seq = _clean_dna(req.sequence)
        if not seq:
            raise HTTPException(status_code=422, detail="empty sequence")

        try:
            kind = EditKind(req.kind)
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail=f"kind must be substitution|insertion|deletion, got {req.kind!r}",
            ) from e

        edit = Edit(kind=kind, position=req.position, ref=req.ref.upper(), alt=req.alt.upper())

        try:
            edited = apply_edit(seq, edit)
        except EditError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        effect = predict_effect(seq, edit)
        tree = build_consequence_tree(req.gene_name, effect)

        warning_ids: list[int] = []
        if req.project_id is not None:
            try:
                await get_project(session, req.project_id)
            except NotFoundError as e:
                raise HTTPException(status_code=404, detail=str(e)) from e

            warning_ids = await warnings_from_effect(
                session,
                project_id=req.project_id,
                gene_name=req.gene_name,
                effect=effect,
            )

        return SimulateEditResponse(
            edited_sequence=edited,
            effect=effect.to_dict(),
            consequence_tree=tree.to_dict(),
            warning_ids=warning_ids,
        )

    # --- Projects ------------------------------------------------------

    @app.get("/projects", response_model=ProjectListResponse)
    async def projects_list(
        session: AsyncSession = Depends(get_session),
    ) -> ProjectListResponse:
        items = await list_projects(session)
        return ProjectListResponse(projects=[p.to_dict() for p in items])

    @app.post("/projects", response_model=ProjectResponse)
    async def projects_create(
        req: ProjectCreate,
        session: AsyncSession = Depends(get_session),
    ) -> ProjectResponse:
        p = await create_project(
            session, name=req.name, description=req.description, organism=req.organism
        )
        return ProjectResponse(project=p.to_dict())

    @app.get("/projects/{project_id}", response_model=ProjectResponse)
    async def projects_get(
        project_id: int,
        session: AsyncSession = Depends(get_session),
    ) -> ProjectResponse:
        try:
            p = await get_project(session, project_id)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return ProjectResponse(project=p.to_dict(include_experiments=True))

    @app.delete("/projects/{project_id}")
    async def projects_delete(
        project_id: int,
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        try:
            await delete_project(session, project_id)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"status": "deleted", "id": project_id}

    # --- Experiments ---------------------------------------------------

    @app.get(
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

    @app.post(
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

    # --- Warnings ------------------------------------------------------

    @app.get(
        "/projects/{project_id}/warnings",
        response_model=WarningListResponse,
    )
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

    @app.post(
        "/warnings/{warning_id}/acknowledge",
        response_model=WarningResponse,
    )
    async def warnings_acknowledge(
        warning_id: int,
        req: AcknowledgeRequest,
        session: AsyncSession = Depends(get_session),
    ) -> WarningResponse:
        try:
            w = await acknowledge_warning(
                session, warning_id, by=req.by, note=req.note
            )
        except WarningError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        return WarningResponse(warning=w.to_dict())

    return app