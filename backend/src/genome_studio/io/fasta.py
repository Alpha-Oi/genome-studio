"""FASTA parser.

Handles:
- single and multi-record files
- multi-line sequences
- lowercase and uppercase
- extra whitespace / empty lines
- non-ACGTN characters are stripped (with note)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FastaRecord:
    """One FASTA record."""

    name: str
    description: str
    sequence: str

    @property
    def length(self) -> int:
        return len(self.sequence)

    @property
    def gc_content(self) -> float:
        if not self.sequence:
            return 0.0
        gc = sum(1 for b in self.sequence.upper() if b in "GC")
        return gc / len(self.sequence)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "sequence": self.sequence,
            "length": self.length,
            "gc_content": round(self.gc_content, 4),
        }


class FastaError(ValueError):
    """Invalid FASTA content."""


def _clean(seq: str) -> str:
    """Uppercase, strip non-ACGTN."""
    return "".join(b for b in seq.upper() if b in "ACGTN")


def parse_fasta(text: str) -> list[FastaRecord]:
    """Parse FASTA text into records.

    Args:
        text: full content of a .fasta / .fa / .fas / .txt file.

    Returns:
        List of FastaRecord. Empty if no records.

    Raises:
        FastaError: if text is empty.
    """
    if not text or not text.strip():
        raise FastaError("empty input")

    records: list[FastaRecord] = []
    current_name: str | None = None
    current_desc: str = ""
    current_seq: list[str] = []

    def flush() -> None:
        nonlocal current_name, current_desc, current_seq
        if current_name is None:
            return
        seq = _clean("".join(current_seq))
        records.append(FastaRecord(current_name, current_desc, seq))
        current_name = None
        current_desc = ""
        current_seq = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith(">"):
            flush()
            header = line[1:].strip()
            if not header:
                current_name = "unnamed"
                current_desc = ""
            else:
                parts = header.split(None, 1)
                current_name = parts[0] or "unnamed"
                current_desc = parts[1] if len(parts) > 1 else ""
        else:
            if current_name is None:
                # FASTA content without a header line - treat as a single unnamed record
                current_name = "unnamed"
                current_desc = ""
            current_seq.append(line)

    flush()
    return records