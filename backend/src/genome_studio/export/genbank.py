"""GenBank flat-file serialization.

Minimal subset: LOCUS, DEFINITION, ORIGIN.
Enough for import into SnapGene / Geneious / Benchling.
"""

from __future__ import annotations

from datetime import UTC, datetime


def _wrap_seq(seq: str, width: int = 60, group: int = 10, indent: int = 9) -> str:
    lines = []
    for i in range(0, len(seq), width):
        chunk = seq[i : i + width]
        parts = [chunk[j : j + group] for j in range(0, len(chunk), group)]
        lines.append(f"{i + 1:>{indent - 1}} {(' '.join(parts))}")
    return "\n".join(lines)


def to_genbank(
    seq: str,
    locus: str = "SEQ",
    definition: str = "Exported sequence",
    organism: str = "unknown",
    topology: str = "linear",
) -> str:
    """Serialize a DNA sequence as a minimal GenBank record.

    Args:
        seq: nucleotide sequence (ACGTN).
        locus: locus name (short).
        definition: description line.
        organism: source organism.
        topology: linear | circular.

    Returns:
        GenBank flat-file string.
    """
    seq = seq.upper()
    date = datetime.now(UTC).strftime("%d-%b-%Y").upper()
    length = len(seq)

    lines = []
    lines.append(f"LOCUS       {locus[:16]:<16}{length} bp    DNA     {topology:<8} {date}")
    lines.append(f"DEFINITION  {definition}")
    lines.append("ACCESSION   .")
    lines.append("VERSION     .")
    lines.append("KEYWORDS    .")
    lines.append(f"SOURCE      {organism}")
    lines.append(f"  ORGANISM  {organism}")
    lines.append("COMMENT     Exported by Genome Studio")
    lines.append("FEATURES             Location/Qualifiers")
    lines.append("     source          1.." + str(length))
    lines.append('                     /organism="' + organism + '"')
    lines.append("ORIGIN")
    lines.append(_wrap_seq(seq))
    lines.append("//")
    return "\n".join(lines) + "\n"
