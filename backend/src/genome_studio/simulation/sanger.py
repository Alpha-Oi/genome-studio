"""Sanger sequencing simulation.

Given a mixture of alleles, produce per-position peak heights for
each base (A, T, G, C). For heterozygous positions with different bases,
two peaks appear simultaneously.
"""

from __future__ import annotations

from dataclasses import dataclass

from genome_studio.simulation.mixture import Allele


@dataclass(frozen=True)
class SangerPosition:
    """Peak heights at one position."""

    position: int        # 0-based on + strand
    A: float
    T: float
    G: float
    C: float

    def to_dict(self) -> dict:
        return {
            "position": self.position,
            "A": round(self.A, 4),
            "T": round(self.T, 4),
            "G": round(self.G, 4),
            "C": round(self.C, 4),
        }

    @property
    def dominant(self) -> str:
        """Dominant base."""
        return max("ATGC", key=lambda b: getattr(self, b))

    @property
    def is_mixed(self) -> bool:
        """True if top-2 peaks are close (heterozygous-ish)."""
        vals = sorted(
            [(b, getattr(self, b)) for b in "ATGC"],
            key=lambda x: x[1],
            reverse=True,
        )
        top, second = vals[0][1], vals[1][1]
        return top > 0 and second / top > 0.3


class SangerError(ValueError):
    """Sanger simulation error."""


def simulate_sanger(
    alleles: list[Allele],
    start: int | None = None,
    end: int | None = None,
) -> list[SangerPosition]:
    """Simulate Sanger chromatogram peak heights.

    Args:
        alleles: mixture of alleles (validated externally).
        start: 0-based inclusive start (default: 0).
        end: 0-based exclusive end (default: full length).

    Returns:
        List of SangerPosition, one per position in range.
    """
    if not alleles:
        raise SangerError("empty allele list")

    length = len(alleles[0].sequence)
    if start is None:
        start = 0
    if end is None:
        end = length
    if not (0 <= start < end <= length):
        raise SangerError(f"invalid range [{start}, {end}) for length {length}")

    positions: list[SangerPosition] = []
    for pos in range(start, end):
        peaks = {"A": 0.0, "T": 0.0, "G": 0.0, "C": 0.0}
        for a in alleles:
            base = a.sequence[pos].upper()
            if base in peaks:
                peaks[base] += a.fraction
        positions.append(SangerPosition(
            position=pos,
            A=peaks["A"],
            T=peaks["T"],
            G=peaks["G"],
            C=peaks["C"],
        ))
    return positions