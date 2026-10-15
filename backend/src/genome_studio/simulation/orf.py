"""ORF finding and translation.

Uses standard genetic code (NCBI table 1).
"""

from __future__ import annotations

from dataclasses import dataclass

# Standard genetic code
CODON_TABLE = {
    "TTT": "F", "TTC": "F", "TTA": "L", "TTG": "L",
    "CTT": "L", "CTC": "L", "CTA": "L", "CTG": "L",
    "ATT": "I", "ATC": "I", "ATA": "I", "ATG": "M",
    "GTT": "V", "GTC": "V", "GTA": "V", "GTG": "V",
    "TCT": "S", "TCC": "S", "TCA": "S", "TCG": "S",
    "CCT": "P", "CCC": "P", "CCA": "P", "CCG": "P",
    "ACT": "T", "ACC": "T", "ACA": "T", "ACG": "T",
    "GCT": "A", "GCC": "A", "GCA": "A", "GCG": "A",
    "TAT": "Y", "TAC": "Y", "TAA": "*", "TAG": "*",
    "CAT": "H", "CAC": "H", "CAA": "Q", "CAG": "Q",
    "AAT": "N", "AAC": "N", "AAA": "K", "AAG": "K",
    "GAT": "D", "GAC": "D", "GAA": "E", "GAG": "E",
    "TGT": "C", "TGC": "C", "TGA": "*", "TGG": "W",
    "CGT": "R", "CGC": "R", "CGA": "R", "CGG": "R",
    "AGT": "S", "AGC": "S", "AGA": "R", "AGG": "R",
    "GGT": "G", "GGC": "G", "GGA": "G", "GGG": "G",
}

STOP_CODONS = {"TAA", "TAG", "TGA"}
START_CODON = "ATG"


@dataclass(frozen=True)
class ORF:
    """Open reading frame."""

    start: int              # 0-based, position of ATG
    end: int                # 0-based, exclusive; position after stop codon
    frame: int              # 0, 1, 2
    protein: str            # translated (without stop)

    @property
    def length_aa(self) -> int:
        return len(self.protein)


def translate(seq: str) -> str:
    """Translate DNA (assumes in-frame, length % 3 == 0). Stops marked '*'."""
    seq = seq.upper()
    out: list[str] = []
    for i in range(0, len(seq) - 2, 3):
        codon = seq[i : i + 3]
        out.append(CODON_TABLE.get(codon, "X"))
    return "".join(out)


def find_orfs(seq: str, min_length_aa: int = 10) -> list[ORF]:
    """Find all ORFs across 3 frames on the + strand.

    Returns list sorted by length descending.
    """
    seq = seq.upper()
    orfs: list[ORF] = []

    for frame in range(3):
        i = frame
        while i + 3 <= len(seq):
            codon = seq[i : i + 3]
            if codon == START_CODON:
                # find next stop in this frame
                j = i + 3
                while j + 3 <= len(seq):
                    stop_codon = seq[j : j + 3]
                    if stop_codon in STOP_CODONS:
                        protein = translate(seq[i:j])
                        if len(protein) >= min_length_aa:
                            orfs.append(ORF(
                                start=i,
                                end=j + 3,
                                frame=frame,
                                protein=protein,
                            ))
                        break
                    j += 3
                i = j if j > i else i + 3
            else:
                i += 3

    orfs.sort(key=lambda o: o.length_aa, reverse=True)
    return orfs


def orf_containing(seq: str, position: int, min_length_aa: int = 10) -> ORF | None:
    """Find ORF containing the given position (0-based)."""
    for orf in find_orfs(seq, min_length_aa=min_length_aa):
        if orf.start <= position < orf.end:
            return orf
    return None