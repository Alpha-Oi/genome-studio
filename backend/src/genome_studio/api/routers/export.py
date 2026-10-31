"""Export edit to FASTA, VCF, GenBank."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel, Field

from genome_studio.api.routers._helpers import clean_dna, parse_edit
from genome_studio.export import edit_to_vcf, to_fasta, to_genbank
from genome_studio.simulation import EditError, apply_edit

router = APIRouter(tags=["export"])


class ExportEditRequest(BaseModel):
    sequence: str = Field(..., min_length=10, max_length=100_000)
    gene_name: str = Field("gene", max_length=64)
    kind: str
    position: int = Field(..., ge=0)
    ref: str = Field("", max_length=1000)
    alt: str = Field("", max_length=1000)


@router.post("/export/edit/fasta")
async def export_fasta(req: ExportEditRequest) -> Response:
    seq = clean_dna(req.sequence)
    if not seq:
        raise HTTPException(status_code=422, detail="empty sequence")
    edit = parse_edit(req)
    try:
        edited = apply_edit(seq, edit)
    except EditError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    content = to_fasta(edited, header=f"{req.gene_name}_edited")
    return Response(
        content=content,
        media_type="text/x-fasta",
        headers={"Content-Disposition": f'attachment; filename="{req.gene_name}_edited.fasta"'},
    )


@router.post("/export/edit/vcf")
async def export_vcf(req: ExportEditRequest) -> Response:
    seq = clean_dna(req.sequence)
    if not seq:
        raise HTTPException(status_code=422, detail="empty sequence")
    edit = parse_edit(req)
    try:
        apply_edit(seq, edit)
    except EditError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    content = edit_to_vcf(edit, ref_len=len(seq), gene_name=req.gene_name)
    return Response(
        content=content,
        media_type="text/vcf",
        headers={"Content-Disposition": f'attachment; filename="{req.gene_name}_edit.vcf"'},
    )


@router.post("/export/edit/genbank")
async def export_genbank(req: ExportEditRequest) -> Response:
    seq = clean_dna(req.sequence)
    if not seq:
        raise HTTPException(status_code=422, detail="empty sequence")
    edit = parse_edit(req)
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
        headers={"Content-Disposition": f'attachment; filename="{req.gene_name}_edited.gb"'},
    )
