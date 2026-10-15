"""NGS simulation.

Distribute a fixed number of reads across the mixture.
"""

from __future__ import annotations

from dataclasses import dataclass

from genome_studio.simulation.mixture import Allele


@dataclass(frozen=True)
class NgsAlleleCount:
    """Read count for one allele."""

    name: str
    fraction: float
    reads: int
    sequence: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fraction": round(self.fraction, 4),
            "reads": self.reads,
            "sequence": self.sequence,
        }


@dataclass(frozen=True)
class NgsSummary:
    """Summary of NGS simulation."""

    total_reads: int
    alleles: list[NgsAlleleCount]

    def to_dict(self) -> dict:
        return {
            "total_reads": self.total_reads,
            "alleles": [a.to_dict() for a in self.alleles],
        }


class NgsError(ValueError):
    """NGS simulation error."""


def simulate_ngs(
    alleles: list[Allele],
    total_reads: int = 1000,
) -> NgsSummary:
    """Distribute reads across alleles by fraction."""
    if not alleles:
        raise NgsError("empty allele list")
    if total_reads <= 0:
        raise NgsError("total_reads must be positive")

    counts: list[NgsAlleleCount] = []
    remaining = total_reads
    for i, a in enumerate(alleles):
        if i == len(alleles) - 1:
            reads = remaining
        else:
            reads = round(total_reads * a.fraction)
            remaining -= reads
        counts.append(NgsAlleleCount(
            name=a.name,
            fraction=a.fraction,
            reads=reads,
            sequence=a.sequence,
        ))

    return NgsSummary(total_reads=total_reads, alleles=counts)