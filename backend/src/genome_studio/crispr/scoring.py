"""Guide RNA scoring.

Simplified heuristics inspired by Doench 2016 and Hsu 2013.
NOT a replacement for production tools (CRISPRscan, Rule Set 2).
"""

from __future__ import annotations


def gc_content(seq: str) -> float:
    """GC fraction, 0..1."""
    if not seq:
        return 0.0
    gc = sum(1 for b in seq.upper() if b in "GC")
    return gc / len(seq)


def has_polyt(seq: str, run: int = 4) -> bool:
    """True if sequence has a run of TTTT (polymerase terminator)."""
    return "T" * run in seq.upper()


def has_homopolymer(seq: str, run: int = 5) -> bool:
    """True if sequence has a homopolymer run of length >= run."""
    seq = seq.upper()
    for base in "ACGT":
        if base * run in seq:
            return True
    return False


def score_guide(spacer: str) -> dict:
    """Score a 20 nt spacer.

    Returns:
        dict with keys: score (0..1), reasons (list of str), warnings (list of str).
    """
    spacer = spacer.upper()
    reasons: list[str] = []
    warnings: list[str] = []
    score = 1.0

    # GC content
    gc = gc_content(spacer)
    if 0.40 <= gc <= 0.60:
        reasons.append(f"GC content {gc:.2f} is in optimal range (0.40-0.60)")
    elif 0.30 <= gc <= 0.70:
        score -= 0.15
        warnings.append(f"GC content {gc:.2f} is suboptimal")
    else:
        score -= 0.4
        warnings.append(f"GC content {gc:.2f} is outside acceptable range")

    # Poly-T
    if has_polyt(spacer, 4):
        score -= 0.3
        warnings.append("Contains TTTT (possible Pol III terminator)")

    # Homopolymer
    if has_homopolymer(spacer, 5):
        score -= 0.15
        warnings.append("Contains homopolymer run (>=5)")

    # Position-specific preferences (Doench 2014 simplifications)
    # G at position 20 (last base before PAM) is favorable
    if spacer[-1] == "G":
        score += 0.05
        reasons.append("G at position 20 (favorable)")
    # C at position 20 is unfavorable
    elif spacer[-1] == "C":
        score -= 0.05
        warnings.append("C at position 20 (unfavorable)")

    # G at position 1 (first base) is unfavorable
    if spacer[0] == "G":
        score -= 0.05
        warnings.append("G at position 1 (unfavorable)")

    # Clamp score to 0..1
    score = max(0.0, min(1.0, score))

    return {
        "score": round(score, 3),
        "reasons": reasons,
        "warnings": warnings,
    }