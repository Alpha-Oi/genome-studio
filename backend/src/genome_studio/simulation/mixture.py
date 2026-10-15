"""Allele mixture model.

After CRISPR editing, a cell population is usually a mix of:
- WT (unedited)
- edited homozygote
- edited heterozygote

We model this as a list of (name, fraction, sequence).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Allele:
    """One allele in the mixture."""

    name: str
    fraction: float
    sequence: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fraction": round(self.fraction, 4),
            "sequence": self.sequence,
        }


class MixtureError(ValueError):
    """Invalid mixture."""


def validate_mixture(alleles: list[Allele]) -> None:
    """Ensure fractions sum to ~1 and all sequences have same length."""
    if not alleles:
        raise MixtureError("empty mixture")

    total = sum(a.fraction for a in alleles)
    if abs(total - 1.0) > 1e-3:
        raise MixtureError(f"fractions must sum to 1.0, got {total}")

    for a in alleles:
        if a.fraction < 0:
            raise MixtureError(f"negative fraction in {a.name}")

    lengths = {len(a.sequence) for a in alleles}
    if len(lengths) > 1:
        raise MixtureError(
            f"all alleles must have same length, got lengths {sorted(lengths)}"
        )


def default_mixture(
    wt_sequence: str,
    edited_sequence: str,
    edited_fraction: float = 0.7,
    heterozygote_fraction: float = 0.0,
) -> list[Allele]:
    """Build a typical post-edit mixture.

    Args:
        wt_sequence: wild-type sequence.
        edited_sequence: fully edited sequence.
        edited_fraction: fraction of edited cells (rest is WT).
        heterozygote_fraction: fraction of heterozygotes (subset of edited).

    Returns:
        List of Allele. Fractions sum to 1.0.
    """
    if not 0.0 <= edited_fraction <= 1.0:
        raise MixtureError("edited_fraction must be in [0, 1]")
    if not 0.0 <= heterozygote_fraction <= 1.0:
        raise MixtureError("heterozygote_fraction must be in [0, 1]")
    if heterozygote_fraction > edited_fraction:
        raise MixtureError("heterozygote_fraction cannot exceed edited_fraction")

    wt_fraction = 1.0 - edited_fraction
    hom_fraction = edited_fraction - heterozygote_fraction

    alleles = []
    if wt_fraction > 0:
        alleles.append(Allele("WT", wt_fraction, wt_sequence))
    if hom_fraction > 0:
        alleles.append(Allele("edited_hom", hom_fraction, edited_sequence))
    if heterozygote_fraction > 0:
        # heterozygote = half WT, half edited at each position
        alleles.append(Allele("edited_het", heterozygote_fraction, edited_sequence))

    if not alleles:
        raise MixtureError("all fractions are zero")

    # Normalize (in case rounding shifted sum)
    total = sum(a.fraction for a in alleles)
    alleles = [Allele(a.name, a.fraction / total, a.sequence) for a in alleles]
    return alleles