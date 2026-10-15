"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from genome_studio import __version__
from genome_studio.build_resolver import resolve_build
from genome_studio.crispr.designer import design_guides
from genome_studio.crispr.offtarget import find_offtargets, off_target_risk
from genome_studio.intent.parser import ParseError, parse_goal
from genome_studio.knowledge.seed import build_default_kg
from genome_studio.reasoning.planner import build_plan
from genome_studio.simulation import (
    Edit,
    EditError,
    EditKind,
    apply_edit,
    build_consequence_tree,
    predict_effect,
)


# --- Schemas -------------------------------------------------------------

class GoalRequest(BaseModel):
    text: str


class PlanResponse(BaseModel):
    plan: dict


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
    kind: str = Field(..., description="substitution | insertion | deletion")
    position: int = Field(..., ge=0)
    ref: str = Field("", max_length=1000)
    alt: str = Field("", max_length=1000)


class SimulateEditResponse(BaseModel):
    edited_sequence: str
    effect: dict
    consequence_tree: dict


# --- Helpers -------------------------------------------------------------

def _clean_dna(seq: str) -> str:
    seq = seq.upper()
    return "".join(b for b in seq if b in "ACGTN")


# --- App factory ---------------------------------------------------------

def create_app() -> FastAPI:
    info = resolve_build()

    app = FastAPI(
        title="Genome Studio",
        version=__version__,
        docs_url="/docs" if info.mode.value != "prod" else None,
        redoc_url=None,
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

    @app.post("/goal", response_model=PlanResponse)
    async def create_goal(req: GoalRequest) -> PlanResponse:
        try:
            goal = parse_goal(req.text)
        except ParseError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        try:
            plan = build_plan(goal, kg)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e)) from e

        return PlanResponse(plan=plan.to_dict())

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

        return OffTargetResponse(
            hits=[h.to_dict() for h in hits],
            summary=summary,
        )

    @app.post("/simulate/edit", response_model=SimulateEditResponse)
    async def simulate_edit(req: SimulateEditRequest) -> SimulateEditResponse:
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

        edit = Edit(
            kind=kind,
            position=req.position,
            ref=req.ref.upper(),
            alt=req.alt.upper(),
        )

        try:
            edited = apply_edit(seq, edit)
        except EditError as e:
            raise HTTPException(status_code=422, detail=str(e)) from e

        effect = predict_effect(seq, edit)
        tree = build_consequence_tree(req.gene_name, effect)

        return SimulateEditResponse(
            edited_sequence=edited,
            effect=effect.to_dict(),
            consequence_tree=tree.to_dict(),
        )

    return app