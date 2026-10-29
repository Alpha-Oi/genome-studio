"""Apply edits to a DNA sequence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EditKind(str, Enum):
    SUBSTITUTION = "substitution"
    INSERTION = "insertion"
    DELETION = "deletion"


@dataclass(frozen=True)
class Edit:
    """One edit to apply to a sequence.

    Coordinates are 0-based, half-open, on the + strand.
    """

    kind: EditKind
    position: int
    ref: str  # reference bases affected (for validation)
    alt: str  # replacement bases (empty for pure deletion)

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "position": self.position,
            "ref": self.ref,
            "alt": self.alt,
        }


class EditError(ValueError):
    """Invalid edit."""


def apply_edit(sequence: str, edit: Edit) -> str:
    """Apply an edit to the sequence.

    Validates that reference bases match (for substitution/deletion).
    """
    seq = sequence.upper()
    pos = edit.position

    if pos < 0 or pos > len(seq):
        raise EditError(f"position {pos} out of bounds (len={len(seq)})")

    if edit.kind == EditKind.SUBSTITUTION:
        end = pos + len(edit.ref)
        if end > len(seq):
            raise EditError("substitution extends past end")
        if seq[pos:end] != edit.ref.upper():
            raise EditError(
                f"reference mismatch at {pos}: expected {edit.ref!r}, got {seq[pos:end]!r}"
            )
        return seq[:pos] + edit.alt.upper() + seq[end:]

    if edit.kind == EditKind.INSERTION:
        return seq[:pos] + edit.alt.upper() + seq[pos:]

    if edit.kind == EditKind.DELETION:
        end = pos + len(edit.ref)
        if end > len(seq):
            raise EditError("deletion extends past end")
        if seq[pos:end] != edit.ref.upper():
            raise EditError(
                f"reference mismatch at {pos}: expected {edit.ref!r}, got {seq[pos:end]!r}"
            )
        return seq[:pos] + seq[end:]

    raise EditError(f"unknown edit kind: {edit.kind}")
