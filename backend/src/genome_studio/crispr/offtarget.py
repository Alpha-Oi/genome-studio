"""Off-target screening for guide RNAs.

Naive Hamming-distance search over a reference sequence.
For production use: Cas-OFFinder, FlashFry, etc.
"""

from __future__ import annotations

from dataclasses import dataclass


def _revcomp(seq: str) -> str:
    comp = {"A": "T", "T": "A", "G": "C", "C": "G", "N": "N"}
    return "".join(comp.get(b, "N") for b in reversed(seq.upper()))


def hamming(a: str, b: str) -> int:
    """Hamming distance. Assumes equal length."""
    if len(a) != len(b):
        raise ValueError("lengths must match")
    return sum(1 for x, y in zip(a, b, strict=False) if x != y)


@dataclass(frozen=True)
class OffTargetHit:
    """One off-target site."""

    position: int  # 0-based position of PAM start
    strand: str  # "+" or "-"
    mismatches: int
    spacer: str  # actual sequence found
    pam: str  # actual PAM
    locus_label: str  # e.g., "chr1:12345" or "ref:pos"

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "strand": self.strand,
            "mismatches": self.mismatches,
            "spacer": self.spacer,
            "pam": self.pam,
            "locus_label": self.locus_label,
        }


def find_offtargets(
    guide_spacer: str,
    reference: str,
    max_mismatches: int = 4,
    pam_suffix: str = "GG",
    reference_label: str = "ref",
) -> list[OffTargetHit]:
    """Find candidate off-targets of a guide in a reference sequence.

    Args:
        guide_spacer: 20 nt guide spacer (5'->3' on + strand).
        reference: reference DNA sequence (any length).
        max_mismatches: allow up to this many mismatches (inclusive).
        pam_suffix: PAM suffix (default GG for SpCas9).
        reference_label: label for loci (e.g., "chr1").

    Returns:
        Sorted list of OffTargetHit (fewest mismatches first).
    """
    guide = guide_spacer.upper()
    ref = reference.upper()
    seq_len = len(guide)
    pam_len = 1 + len(pam_suffix)
    total = seq_len + pam_len
    hits: list[OffTargetHit] = []

    # + strand
    for i in range(0, len(ref) - total + 1):
        cand = ref[i : i + seq_len]
        pam_start = i + seq_len
        n_base = ref[pam_start]
        tail = ref[pam_start + 1 : pam_start + 1 + len(pam_suffix)]
        if n_base not in "ACGT" or tail != pam_suffix:
            continue
        try:
            mm = hamming(guide, cand)
        except ValueError:
            continue
        if mm <= max_mismatches:
            hits.append(
                OffTargetHit(
                    position=pam_start,
                    strand="+",
                    mismatches=mm,
                    spacer=cand,
                    pam=n_base + tail,
                    locus_label=f"{reference_label}:{pam_start}",
                )
            )

    # - strand
    rc_ref = _revcomp(ref)
    for i in range(0, len(rc_ref) - total + 1):
        cand = rc_ref[i : i + seq_len]
        pam_start = i + seq_len
        n_base = rc_ref[pam_start]
        tail = rc_ref[pam_start + 1 : pam_start + 1 + len(pam_suffix)]
        if n_base not in "ACGT" or tail != pam_suffix:
            continue
        try:
            mm = hamming(guide, cand)
        except ValueError:
            continue
        if mm <= max_mismatches:
            orig_pos = len(ref) - 1 - pam_start
            hits.append(
                OffTargetHit(
                    position=orig_pos,
                    strand="-",
                    mismatches=mm,
                    spacer=cand,
                    pam=n_base + tail,
                    locus_label=f"{reference_label}:{orig_pos}(-)",
                )
            )

    hits.sort(key=lambda h: (h.mismatches, h.position))
    return hits


def off_target_risk(hits: list[OffTargetHit]) -> dict:
    """Summarize off-target risk.

    Returns dict with:
        total: total hit count
        perfect: hits with 0 mismatches (real target)
        near: hits with 1-2 mismatches (high concern)
        distant: hits with >=3 mismatches
        risk: 0..1 score
    """
    perfect = sum(1 for h in hits if h.mismatches == 0)
    near = sum(1 for h in hits if 1 <= h.mismatches <= 2)
    distant = sum(1 for h in hits if h.mismatches >= 3)

    # risk: near-misses dominate
    risk = min(1.0, near * 0.3 + distant * 0.05)

    return {
        "total": len(hits),
        "perfect": perfect,
        "near": near,
        "distant": distant,
        "risk": round(risk, 3),
    }
