"""FASTA serialization."""

from __future__ import annotations


def _wrap(seq: str, width: int = 60) -> str:
    return "\n".join(seq[i : i + width] for i in range(0, len(seq), width))


def to_fasta(seq: str, header: str = "sequence", width: int = 60) -> str:
    """Serialize a DNA sequence as FASTA.

    Args:
        seq: nucleotide sequence (ACGTN).
        header: description line (without '>').
        width: line wrap.

    Returns:
        Multi-line FASTA string.
    """
    seq = seq.upper()
    header = header.strip() or "sequence"
    return f">{header}\n{_wrap(seq, width)}\n"