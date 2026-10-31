"""Batch operations: gRNA design for multiple sequences."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from genome_studio.api.rate_limit import limiter
from genome_studio.crispr.designer import design_guides

router = APIRouter(tags=["batch"])


class BatchSequence(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    sequence: str = Field(..., min_length=1, max_length=100_000)


class BatchDesignRequest(BaseModel):
    sequences: list[BatchSequence] = Field(..., min_length=1, max_length=200)
    top_n: int = Field(3, ge=1, le=20)
    min_score: float = Field(0.5, ge=0.0, le=1.0)


class BatchDesignResult(BaseModel):
    name: str
    length: int
    guides: list[dict]
    error: str | None = None


def _clean_dna(seq: str) -> str:
    seq = seq.upper()
    return "".join(b for b in seq if b in "ACGTN")


@router.post("/batch/design")
@limiter.limit("10/minute")
async def batch_design(request: Request, req: BatchDesignRequest) -> dict:
    results: list[BatchDesignResult] = []

    for item in req.sequences:
        seq = _clean_dna(item.sequence)
        if len(seq) < 23:
            results.append(
                BatchDesignResult(
                    name=item.name,
                    length=len(seq),
                    guides=[],
                    error="sequence too short (" + str(len(seq)) + " nt)",
                )
            )
            continue

        guides = design_guides(seq, top_n=req.top_n, min_score=req.min_score)
        results.append(
            BatchDesignResult(
                name=item.name,
                length=len(seq),
                guides=[g.to_dict() for g in guides],
                error=None if guides else "no guides found",
            )
        )

    return {"results": [r.model_dump() for r in results]}
