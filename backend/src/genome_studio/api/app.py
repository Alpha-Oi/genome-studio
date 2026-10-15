"""FastAPI app factory."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from genome_studio import __version__
from genome_studio.build_resolver import resolve_build
from genome_studio.crispr.designer import design_guides
from genome_studio.intent.parser import ParseError, parse_goal
from genome_studio.knowledge.seed import build_default_kg
from genome_studio.reasoning.planner import build_plan


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


# --- Helpers -------------------------------------------------------------

def _clean_dna(seq: str) -> str:
    """Uppercase, strip non-ACGTN."""
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

    return app