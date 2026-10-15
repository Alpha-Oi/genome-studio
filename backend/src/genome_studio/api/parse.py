"""Parsing endpoints: FASTA, etc."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from genome_studio.io.fasta import FastaError, parse_fasta


router = APIRouter(tags=["parse"])


class FastaRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10_000_000)


@router.post("/parse/fasta")
async def parse_fasta_endpoint(req: FastaRequest) -> dict:
    try:
        records = parse_fasta(req.content)
    except FastaError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    if not records:
        raise HTTPException(status_code=422, detail="no FASTA records found")

    return {"records": [r.to_dict() for r in records]}