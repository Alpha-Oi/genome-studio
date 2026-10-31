"""Simulation endpoints: edit, sanger, ngs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.api.routers._helpers import clean_dna, parse_edit
from genome_studio.data import NotFoundError, get_project, get_session
from genome_studio.simulation import (
    EditError,
    apply_edit,
    build_consequence_tree,
    default_mixture,
    predict_effect,
    simulate_ngs,
    simulate_sanger,
    validate_mixture,
)
from genome_studio.warnings import warnings_from_effect

router = APIRouter(tags=["simulate"])


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


class SequencingRequest(BaseModel):
    wt_sequence: str = Field(..., min_length=10, max_length=100_000)
    edited_sequence: str = Field(..., min_length=10, max_length=100_000)
    edited_fraction: float = Field(0.7, ge=0.0, le=1.0)
    heterozygote_fraction: float = Field(0.0, ge=0.0, le=1.0)
    total_reads: int = Field(1000, ge=10, le=1_000_000)
    window: int = Field(40, ge=5, le=500)


@router.post("/simulate/edit", response_model=SimulateEditResponse)
async def simulate_edit(
    req: SimulateEditRequest,
    session: AsyncSession = Depends(get_session),
) -> SimulateEditResponse:
    seq = clean_dna(req.sequence)
    if not seq:
        raise HTTPException(status_code=422, detail="empty sequence")

    edit = parse_edit(req)

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


@router.post("/simulate/sanger")
async def simulate_sanger_endpoint(req: SequencingRequest) -> dict:
    wt = clean_dna(req.wt_sequence)
    edited = clean_dna(req.edited_sequence)
    if len(wt) != len(edited):
        raise HTTPException(
            status_code=422,
            detail=f"WT and edited must have same length: {len(wt)} != {len(edited)}",
        )

    try:
        alleles = default_mixture(
            wt,
            edited,
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


@router.post("/simulate/ngs")
async def simulate_ngs_endpoint(req: SequencingRequest) -> dict:
    wt = clean_dna(req.wt_sequence)
    edited = clean_dna(req.edited_sequence)
    if len(wt) != len(edited):
        raise HTTPException(
            status_code=422,
            detail=f"WT and edited must have same length: {len(wt)} != {len(edited)}",
        )

    try:
        alleles = default_mixture(
            wt,
            edited,
            edited_fraction=req.edited_fraction,
            heterozygote_fraction=req.heterozygote_fraction,
        )
        validate_mixture(alleles)
        summary = simulate_ngs(alleles, total_reads=req.total_reads)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return summary.to_dict()
