"""FastAPI app factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio import __version__
from genome_studio.api.batch import router as batch_router
from genome_studio.api.mode import router as mode_router
from genome_studio.api.parse import router as parse_router
from genome_studio.build_resolver import resolve_build
from genome_studio.crispr.designer import design_guides
from genome_studio.crispr.offtarget import find_offtargets, off_target_risk
from genome_studio.data import (
    NotFoundError,
    create_experiment,
    create_project,
    delete_experiment,
    delete_project,
    dispose_engine,
    get_project,
    get_session,
    init_db,
    list_experiments,
    list_projects,
)
from genome_studio.export import edit_to_vcf, to_fasta, to_genbank
from genome_studio.intent.parser import ParseError, parse_goal
from genome_studio.knowledge.seed import build_default_kg
from genome_studio.reasoning.mapper import map_goal
from genome_studio.reasoning.planner import build_plan
from genome_studio.report import build_project_pdf
from genome_studio.simulation import (
    Edit,
    EditError,
    EditKind,
    apply_edit,
    build_consequence_tree,
    default_mixture,
    predict_effect,
    simulate_ngs,
    simulate_sanger,
    validate_mixture,
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
    original_sequence: str
    effect: dict
    consequence_tree: dict
    warning_ids: list[int] = []
    edit: dict


class ExportEditRequest(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=100_000)
    gene_name: str = Field("gene", max_length=64)
    kind: str
    position: int = Field(..., ge=0)
    ref: str = Field("", max_length=1000)
    alt: str = Field("", max_length=1000)


class SequencingRequest(BaseModel):
    wt_sequence: str = Field(..., min_length=10, max_length=100_000)
    edited_sequence: str = Field(..., min_length=10, max_length=100_000)
    edited_fraction: float = Field(0.7, ge=0.0, le=1.0)
    heterozygote_fraction: float = Field(0.0, ge=0.0, le=1.0)
    total_reads: int = Field(1000, ge=10, le=1_000_000)
    window: int = Field(40, ge=5, le=500)


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


def _clean_dna(seq: str) -> str:
    seq = seq.upper()
    return "".join(b for b in seq if b in "ACGTN")


def _parse_edit(req) -> Edit:
    try:
        kind = EditKind(req.kind)
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"kind must be substitution|insertion|deletion, got {req.kind!r}",
        ) from e
    return Edit(
        kind=kind,
        position=req.position,
        ref=req.ref.upper(),
        alt=req.alt.upper(),
    )


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

    # --- Mode router ---------------------------------------------------

    app.include_router(mode_router)
    app.include_router(batch_router)
    app.include_router(parse_router)

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

    @app.post("/simulate/edit", response_model=SimulateEditResponse)
    async def simulate_edit(
        req: SimulateEditRequest,
        session: AsyncSession = Depends(get_session),
    ) -> SimulateEditResponse:
        seq = _clean_dna(req.sequence)
        if not seq:
            raise HTTPException(status_code=422, detail="empty sequence")

        edit = _parse_edit(req)

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
            original_sequence=seq,
            effect=effect.to_dict(),
            consequence_tree=tree.to_dict(),
            warning_ids=warning_ids,
            edit=edit.to_dict(),
        )

    @app.post("/simulate/sanger")
    async def simulate_sanger_endpoint(req: SequencingRequest) -> dict:
        wt = _clean_dna(req.wt_sequence)
        edited = _clean_dna(req.edited_sequence)
        if len(wt) != len(edited):
            raise HTTPException(
                status_code=422,
                detail=f"WT and edited must have same length: {len(wt)} != {len(edited)}",
            )

        try:
            alleles = default_mixture(
                wt, edited,
                edited_fraction=req.edited_fraction,
                heterozygote_fraction=req.heterozygote_fraction,
            )
            validate_mixture(alleles)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        diffs = [i for i in range(len(wt)) if wt[i] != edited[i]]
        edit_pos = diffs[0] if diffs else len(wt) // 2

        half = req.window // 2
        start = max(0, edit_pos - half)
        end = min(len(wt), edit_pos + half)

        peaks = simulate_sanger(alleles, start=start, end=end)

        return {
            "wt_sequence": wt,
            "edited_sequence": edited,
            "edit_position": edit_pos,
            "window_start": start,
            "window_end": end,
            "alleles": [a.to_dict() for a in alleles],
            "peaks": [p.to_dict() for p in peaks],
        }

    @app.post("/simulate/ngs")
    async def simulate_ngs_endpoint(req: SequencingRequest) -> dict:
        wt = _clean_dna(req.wt_sequence)
        edited = _clean_dna(req.edited_sequence)
        if len(wt) != len(edited):
            raise HTTPException(
                status_code=422,
                detail=f"WT and edited must have same length: {len(wt)} != {len(edited)}",
            )

        try:
            alleles = default_mixture(
                wt, edited,
                edited_fraction=req.edited_fraction,
                heterozygote_fraction=req.heterozygote_fraction,
            )
            validate_mixture(alleles)
            summary = simulate_ngs(alleles, total_reads=req.total_reads)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        return summary.to_dict()

    @app.post("/export/edit/fasta")
    async def export_fasta(req: ExportEditRequest) -> Response:
        seq = _clean_dna(req.sequence)
        if not seq:
            raise HTTPException(status_code=422, detail="empty sequence")
        edit = _parse_edit(req)
        try:
            edited = apply_edit(seq, edit)
        except EditError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        content = to_fasta(edited, header=f"{req.gene_name}_edited")
        return Response(
            content=content,
            media_type="text/x-fasta",
            headers={
                "Content-Disposition": f'attachment; filename="{req.gene_name}_edited.fasta"'
            },
        )

    @app.post("/export/edit/vcf")
    async def export_vcf(req: ExportEditRequest) -> Response:
        seq = _clean_dna(req.sequence)
        if not seq:
            raise HTTPException(status_code=422, detail="empty sequence")
        edit = _parse_edit(req)
        try:
            apply_edit(seq, edit)
        except EditError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        content = edit_to_vcf(edit, ref_len=len(seq), gene_name=req.gene_name)
        return Response(
            content=content,
            media_type="text/vcf",
            headers={
                "Content-Disposition": f'attachment; filename="{req.gene_name}_edit.vcf"'
            },
        )

    @app.post("/export/edit/genbank")
    async def export_genbank(req: ExportEditRequest) -> Response:
        seq = _clean_dna(req.sequence)
        if not seq:
            raise HTTPException(status_code=422, detail="empty sequence")
        edit = _parse_edit(req)
        try:
            edited = apply_edit(seq, edit)
        except EditError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e
        content = to_genbank(
            edited,
            locus=req.gene_name[:16],
            definition=f"{req.gene_name} with {edit.kind.value} at {edit.position}",
            organism="synthetic",
        )
        return Response(
            content=content,
            media_type="text/plain",
            headers={
                "Content-Disposition": f'attachment; filename="{req.gene_name}_edited.gb"'
            },
        )

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

    @app.delete("/experiments/{experiment_id}")
    async def experiments_delete(
        experiment_id: int,
        session: AsyncSession = Depends(get_session),
    ) -> dict:
        try:
            await delete_experiment(session, experiment_id)
        except NotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"status": "deleted", "id": experiment_id}

    @app.get("/projects/{project_id}/warnings", response_model=WarningListResponse)
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

    @app.get("/projects/{project_id}/report.pdf")
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

        safe_name = "".join(
            c if c.isalnum() or c in "-_" else "_" for c in project.name
        )[:60] or "project"

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_name}_report.pdf"'
            },
        )

    return app