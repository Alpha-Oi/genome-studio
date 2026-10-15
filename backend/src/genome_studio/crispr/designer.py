"""Top-level guide RNA designer."""

from __future__ import annotations

from dataclasses import dataclass, field

from genome_studio.crispr.pam import find_pam_sites
from genome_studio.crispr.scoring import score_guide


@dataclass(frozen=True)
class Guide:
    """Candidate guide RNA."""

    spacer: str              # 20 nt
    pam: str                 # e.g., "AGG"
    position: int            # 0-based position of PAM on + strand
    strand: str              # "+" or "-"
    gc_content: float
    score: float             # 0..1
    reasons: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "spacer": self.spacer,
            "pam": self.pam,
            "position": self.position,
            "strand": self.strand,
            "gc_content": round(self.gc_content, 3),
            "score": self.score,
            "reasons": list(self.reasons),
            "warnings": list(self.warnings),
        }


def _gc(seq: str) -> float:
    if not seq:
        return 0.0
    return sum(1 for b in seq if b in "GC") / len(seq)


def design_guides(
    sequence: str,
    top_n: int = 5,
    min_score: float = 0.5,
) -> list[Guide]:
    """Design top guide RNAs for a given DNA sequence.

    Args:
        sequence: target DNA (uppercase or not).
        top_n: max guides to return.
        min_score: filter threshold.

    Returns:
        Sorted list (best first) of up to top_n guides.
    """
    hits = find_pam_sites(sequence)
    guides: list[Guide] = []

    seen_spacers: set[str] = set()
    for h in hits:
        if h.spacer in seen_spacers:
            continue
        seen_spacers.add(h.spacer)

        s = score_guide(h.spacer)
        if s["score"] < min_score:
            continue

        guides.append(Guide(
            spacer=h.spacer,
            pam=h.pam,
            position=h.position,
            strand=h.strand,
            gc_content=_gc(h.spacer),
            score=s["score"],
            reasons=tuple(s["reasons"]),
            warnings=tuple(s["warnings"]),
        ))

    guides.sort(key=lambda g: g.score, reverse=True)
    return guides[:top_n]