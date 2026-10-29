"""PAM site search.

SpCas9 PAM = NGG (N = any base, G = guanine).
Guide RNA (spacer) = 20 nt immediately upstream of PAM.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PamHit:
    """One PAM hit."""

    position: int  # 0-based, index of PAM start (N in NGG)
    strand: str  # "+" or "-"
    pam: str  # actual PAM sequence (e.g., "AGG", "TGG")
    spacer: str  # 20 nt spacer (5'->3' on + strand)


def _revcomp(seq: str) -> str:
    """Reverse complement."""
    comp = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}
    return "".join(comp.get(b, "N") for b in reversed(seq.upper()))


def find_pam_sites(
    sequence: str,
    pam_suffix: str = "GG",
    spacer_length: int = 20,
    both_strands: bool = True,
) -> list[PamHit]:
    """Find all SpCas9-like PAM sites (N{spacer_length}<pam_suffix>).

    Args:
        sequence: DNA sequence (uppercase or not).
        pam_suffix: two bases after N. Default "GG" for SpCas9.
        spacer_length: length of spacer (default 20 nt).
        both_strands: search both + and - strands.

    Returns:
        List of PamHit, sorted by position.
    """
    seq = sequence.upper()
    hits: list[PamHit] = []
    total = spacer_length + 1 + len(pam_suffix)

    for i in range(0, len(seq) - total + 1):
        # i = start of spacer; PAM starts at i + spacer_length
        pam_start = i + spacer_length
        n_base = seq[pam_start]
        pam_tail = seq[pam_start + 1 : pam_start + 1 + len(pam_suffix)]
        if n_base in "ACGT" and pam_tail == pam_suffix:
            hits.append(
                PamHit(
                    position=pam_start,
                    strand="+",
                    pam=n_base + pam_tail,
                    spacer=seq[i:pam_start],
                )
            )

    if both_strands:
        rc = _revcomp(seq)
        for i in range(0, len(rc) - total + 1):
            pam_start = i + spacer_length
            n_base = rc[pam_start]
            pam_tail = rc[pam_start + 1 : pam_start + 1 + len(pam_suffix)]
            if n_base in "ACGT" and pam_tail == pam_suffix:
                orig_pos = len(seq) - 1 - pam_start
                hits.append(
                    PamHit(
                        position=orig_pos,
                        strand="-",
                        pam=n_base + pam_tail,
                        spacer=rc[i:pam_start],
                    )
                )

    hits.sort(key=lambda h: (h.position, h.strand))
    return hits
