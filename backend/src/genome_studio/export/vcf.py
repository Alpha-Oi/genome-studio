"""VCF serialization.

VCF 4.2 format. Coordinates are 1-based on the + strand.
"""

from __future__ import annotations

from datetime import datetime, timezone

from genome_studio.simulation.edit import Edit, EditKind


VCF_HEADER = """##fileformat=VCFv4.2
##fileDate={date}
##source=GenomeStudio
##reference=local
##contig=<ID=ref,length={ref_len}>
##INFO=<ID=GS_EDIT_KIND,Number=1,Type=String,Description="Edit kind">
##INFO=<ID=GS_GENE,Number=1,Type=String,Description="Target gene">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO
"""


def edit_to_vcf(
    edit: Edit,
    ref_len: int,
    gene_name: str = "gene",
    contig: str = "ref",
) -> str:
    """Serialize an Edit as VCF.

    Args:
        edit: the edit.
        ref_len: length of the reference (for header).
        gene_name: gene symbol.
        contig: contig name (default 'ref').

    Returns:
        VCF string.
    """
    date = datetime.now(timezone.utc).strftime("%Y%m%d")
    header = VCF_HEADER.format(date=date, ref_len=ref_len)

    pos_1based = edit.position + 1
    ref_field = edit.ref.upper() if edit.ref else "."
    alt_field = edit.alt.upper() if edit.alt else "."

    # VCF uses '.' for empty deletion alt / insertion ref
    if edit.kind == EditKind.INSERTION:
        ref_field = ref_field if ref_field != "" else "."
        if ref_field == ".":
            # anchor base for insertion: VCF convention requires 1 anchor base
            ref_field = "N"
            pos_1based = edit.position + 1 if edit.position > 0 else 1
    elif edit.kind == EditKind.DELETION:
        alt_field = "."
    elif edit.kind == EditKind.SUBSTITUTION:
        pass  # both ref and alt provided

    info = f"GS_EDIT_KIND={edit.kind.value};GS_GENE={gene_name}"

    row = "\t".join([
        contig,
        str(pos_1based),
        ".",
        ref_field,
        alt_field,
        ".",
        "PASS",
        info,
    ])
    return header + row + "\n"