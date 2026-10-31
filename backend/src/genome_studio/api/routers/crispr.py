"""CRISPR design and off-target endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genome_studio.api.routers._helpers import clean_dna
from genome_studio.crispr.designer import design_guides
from genome_studio.crispr.offtarget import find_offtargets, off_target_risk

router = APIRouter(tags=["crispr"])


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


@router.post("/crispr/design", response_model=CrisprResponse)
async def crispr_design(req: CrisprRequest) -> CrisprResponse:
    seq = clean_dna(req.sequence)
    if len(seq) < 23:
        raise HTTPException(status_code=422, detail="Sequence too short")

    guides = design_guides(seq, top_n=req.top_n, min_score=req.min_score)
    if not guides:
        raise HTTPException(
            status_code=422,
            detail="No guide RNAs found with given criteria",
        )
    return CrisprResponse(guides=[g.to_dict() for g in guides])


@router.post("/crispr/offtarget", response_model=OffTargetResponse)
async def crispr_offtarget(req: OffTargetRequest) -> OffTargetResponse:
    guide = clean_dna(req.guide_spacer)
    ref = clean_dna(req.reference)
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
