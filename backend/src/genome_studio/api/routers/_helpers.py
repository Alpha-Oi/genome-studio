"""Shared helpers for API routers."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from genome_studio.simulation import Edit, EditKind


def clean_dna(seq: str) -> str:
    seq = seq.upper()
    return "".join(b for b in seq if b in "ACGTN")


def parse_edit(req: Any) -> Edit:
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
