"""Predict edit effects on ORF/protein."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from genome_studio.simulation.edit import Edit, EditKind, apply_edit
from genome_studio.simulation.orf import ORF, find_orfs, translate


class EffectType(str, Enum):
    UNCHANGED = "unchanged"
    OUTSIDE_ORF = "outside_orf"
    SILENT = "silent"
    MISSENSE = "missense"
    NONSENSE = "nonsense"           # premature stop codon
    FRAMESHIFT = "frameshift"
    IN_FRAME_INDEL = "in_frame_indel"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class EditEffect:
    """Result of an edit on a sequence."""

    effect_type: EffectType
    ref_protein: str
    alt_protein: str
    description: str
    severity: float             # 0..1
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "effect_type": self.effect_type.value,
            "ref_protein": self.ref_protein,
            "alt_protein": self.alt_protein,
            "description": self.description,
            "severity": round(self.severity, 3),
            "evidence": list(self.evidence),
        }


def _translate_orfs(seq: str) -> list[ORF]:
    return find_orfs(seq, min_length_aa=5)


def predict_effect(ref_seq: str, edit: Edit) -> EditEffect:
    """Predict effect of edit on the main ORF."""
    ref_seq = ref_seq.upper()
    try:
        alt_seq = apply_edit(ref_seq, edit)
    except Exception as e:
        return EditEffect(
            effect_type=EffectType.UNKNOWN,
            ref_protein="",
            alt_protein="",
            description=f"Could not apply edit: {e}",
            severity=0.0,
        )

    ref_orfs = _translate_orfs(ref_seq)
    alt_orfs = _translate_orfs(alt_seq)

    if not ref_orfs:
        return EditEffect(
            effect_type=EffectType.OUTSIDE_ORF,
            ref_protein="",
            alt_protein="",
            description="No ORF found in reference; cannot predict effect.",
            severity=0.0,
        )

    main_ref = ref_orfs[0]
    main_alt = alt_orfs[0] if alt_orfs else None

    # Edit position relative to ORF?
    edit_start = edit.position
    edit_end = edit.position + len(edit.ref)
    in_orf = main_ref.start <= edit_start < main_ref.end

    if not in_orf:
        return EditEffect(
            effect_type=EffectType.OUTSIDE_ORF,
            ref_protein=main_ref.protein,
            alt_protein=main_alt.protein if main_alt else "",
            description="Edit lies outside the main ORF.",
            severity=0.05,
            evidence=("edit position outside ORF bounds",),
        )

    # Frame shift: length delta not multiple of 3
    length_delta = len(edit.alt) - len(edit.ref)
    is_frameshift = (length_delta % 3) != 0

    if is_frameshift:
        return EditEffect(
            effect_type=EffectType.FRAMESHIFT,
            ref_protein=main_ref.protein,
            alt_protein=main_alt.protein if main_alt else "",
            description="Frameshift: length change not multiple of 3; downstream translation altered.",
            severity=0.95,
            evidence=(f"length delta = {length_delta}",),
        )

    # Compare codons (substitution / in-frame indel)
    ref_codon_idx = (edit_start - main_ref.start) // 3
    ref_codon_start = main_ref.start + ref_codon_idx * 3
    ref_codon = ref_seq[ref_codon_start : ref_codon_start + 3]
    try:
        alt_codon = alt_seq[ref_codon_start : ref_codon_start + 3]
    except Exception:
        alt_codon = ""

    ref_aa = translate(ref_codon)[:1] or "?"
    alt_aa = translate(alt_codon)[:1] or "?"

    if edit.kind == EditKind.SUBSTITUTION and ref_aa == alt_aa:
        return EditEffect(
            effect_type=EffectType.SILENT,
            ref_protein=main_ref.protein,
            alt_protein=main_alt.protein if main_alt else main_ref.protein,
            description=f"Silent: codon {ref_codon}->{alt_codon}, amino acid unchanged ({ref_aa}).",
            severity=0.0,
            evidence=(f"codon {ref_codon}->{alt_codon}",),
        )

    if alt_aa == "*":
        return EditEffect(
            effect_type=EffectType.NONSENSE,
            ref_protein=main_ref.protein,
            alt_protein=main_alt.protein if main_alt else "",
            description=f"Nonsense: premature stop codon created ({ref_codon}->{alt_codon}).",
            severity=0.9,
            evidence=(f"codon {ref_codon}->{alt_codon}",),
        )

    if edit.kind == EditKind.SUBSTITUTION:
        return EditEffect(
            effect_type=EffectType.MISSENSE,
            ref_protein=main_ref.protein,
            alt_protein=main_alt.protein if main_alt else "",
            description=f"Missense: {ref_aa}->{alt_aa} ({ref_codon}->{alt_codon}).",
            severity=0.5,
            evidence=(f"codon {ref_codon}->{alt_codon}",),
        )

    return EditEffect(
        effect_type=EffectType.IN_FRAME_INDEL,
        ref_protein=main_ref.protein,
        alt_protein=main_alt.protein if main_alt else "",
        description="In-frame indel: protein length changes but frame preserved.",
        severity=0.4,
    )