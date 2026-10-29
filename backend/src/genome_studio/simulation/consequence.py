"""Consequence tree builder.

Edit -> Transcript -> Protein -> Pathway -> Phenotype.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from genome_studio.simulation.effects import EditEffect, EffectType


@dataclass
class ConsequenceNode:
    """One node in the consequence tree."""

    node_id: str
    type: str  # "transcript", "protein", "pathway", "phenotype"
    description: str
    confidence: float  # 0..1
    method: str = "rule-based"
    evidence: tuple[str, ...] = ()
    children: list[ConsequenceNode] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "type": self.type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "method": self.method,
            "evidence": list(self.evidence),
            "children": [c.to_dict() for c in self.children],
        }


def build_consequence_tree(
    gene_name: str,
    effect: EditEffect,
) -> ConsequenceNode:
    """Build a tree of consequences from an edit effect."""
    root = ConsequenceNode(
        node_id="root",
        type="edit",
        description=f"Edit to {gene_name}",
        confidence=1.0,
    )

    # --- Transcript level ------------------------------------------
    transcript = ConsequenceNode(
        node_id="t1",
        type="transcript",
        description="",
        confidence=0.7,
    )

    if effect.effect_type == EffectType.OUTSIDE_ORF:
        transcript.description = "No effect on main transcript."
        transcript.confidence = 0.9
    elif effect.effect_type == EffectType.SILENT:
        transcript.description = "Transcript produced, no amino acid change."
        transcript.confidence = 0.95
    elif effect.effect_type == EffectType.MISSENSE:
        transcript.description = "Full-length transcript, one amino acid changed."
        transcript.confidence = 0.9
    elif effect.effect_type == EffectType.NONSENSE:
        transcript.description = "Premature stop codon; transcript may undergo NMD."
        transcript.confidence = 0.75
    elif effect.effect_type == EffectType.FRAMESHIFT:
        transcript.description = "Frameshift; downstream sequence misread, likely NMD."
        transcript.confidence = 0.8
    elif effect.effect_type == EffectType.IN_FRAME_INDEL:
        transcript.description = "In-frame indel; transcript length altered."
        transcript.confidence = 0.85
    else:
        transcript.description = effect.description
        transcript.confidence = 0.4

    root.children.append(transcript)

    # --- Protein level ---------------------------------------------
    protein = ConsequenceNode(
        node_id="p1",
        type="protein",
        description="",
        confidence=0.7,
    )

    if effect.effect_type == EffectType.OUTSIDE_ORF:
        protein.description = "Protein unchanged."
        protein.confidence = 0.9
    elif effect.effect_type == EffectType.SILENT:
        protein.description = "Protein unchanged."
        protein.confidence = 0.95
    elif effect.effect_type == EffectType.MISSENSE:
        protein.description = "Altered protein; function may be affected partially or fully."
        protein.confidence = 0.6
    elif effect.effect_type == EffectType.NONSENSE:
        protein.description = "Truncated protein; likely loss-of-function."
        protein.confidence = 0.85
    elif effect.effect_type == EffectType.FRAMESHIFT:
        protein.description = "Frameshifted protein; almost certainly non-functional."
        protein.confidence = 0.9
    elif effect.effect_type == EffectType.IN_FRAME_INDEL:
        protein.description = "Protein with insertion/deletion; function may be impaired."
        protein.confidence = 0.5
    else:
        protein.description = "Unknown protein effect."
        protein.confidence = 0.3

    transcript.children.append(protein)

    # --- Pathway level (generic note) ------------------------------
    pathway = ConsequenceNode(
        node_id="pw1",
        type="pathway",
        description=(
            f"Effect on pathways containing {gene_name} depends on its role. "
            "Check BioKG for pathway membership."
        ),
        confidence=0.4,
        method="note",
    )
    protein.children.append(pathway)

    # --- Phenotype level -------------------------------------------
    if effect.effect_type in (EffectType.NONSENSE, EffectType.FRAMESHIFT):
        pheno_desc = "Likely loss-of-function phenotype downstream."
        pheno_conf = 0.6
    elif effect.effect_type == EffectType.MISSENSE:
        pheno_desc = "Phenotype depends on functional impact of substitution."
        pheno_conf = 0.4
    elif effect.effect_type == EffectType.SILENT:
        pheno_desc = "No phenotype expected."
        pheno_conf = 0.9
    else:
        pheno_desc = "Phenotype uncertain; requires experimental validation."
        pheno_conf = 0.3

    phenotype = ConsequenceNode(
        node_id="ph1",
        type="phenotype",
        description=pheno_desc,
        confidence=pheno_conf,
        method="heuristic",
    )
    pathway.children.append(phenotype)

    return root
