"""Planner - из InterventionSet строит исполнимый план.

Дерево: Goal -> Intervention -> Steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from genome_studio.intent.goal import Goal
from genome_studio.knowledge.graph import BioKG
from genome_studio.reasoning.mapper import Intervention, map_goal


@dataclass(frozen=True)
class PlanStep:
    """Шаг плана."""

    order: int
    action: str  # "design_grna", "validate_offtarget", "clone", ...
    description: str
    depends_on: tuple[int, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass
class Plan:
    """Готовый план."""

    goal: Goal
    intervention: Intervention
    steps: list[PlanStep] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "goal": self.goal.to_dict(),
            "intervention": {
                "kind": self.intervention.kind,
                "target_gene": self.intervention.target_gene,
                "rationale": self.intervention.rationale,
                "predicted_effect": self.intervention.predicted_effect,
                "off_target_risk": self.intervention.off_target_risk,
                "essentiality_risk": self.intervention.essentiality_risk,
                "complexity": self.intervention.complexity,
                "warnings": list(self.intervention.warnings),
                "evidence": list(self.intervention.evidence),
            },
            "steps": [
                {
                    "order": s.order,
                    "action": s.action,
                    "description": s.description,
                    "depends_on": list(s.depends_on),
                    "warnings": list(s.warnings),
                }
                for s in self.steps
            ],
            "notes": self.notes,
        }


def _steps_for(intervention: Intervention) -> list[PlanStep]:
    """Генерирует шаги по типу вмешательства."""
    kind = intervention.kind

    if kind == "knockout":
        return [
            PlanStep(1, "select_target_exon", "Choose common exon of target gene."),
            PlanStep(2, "design_grna", "Design 3-5 candidate gRNAs with PAM."),
            PlanStep(3, "check_offtarget", "Screen off-targets genome-wide.", depends_on=(2,)),
            PlanStep(
                4, "clone_into_vector", "Clone selected gRNA into Cas9 vector.", depends_on=(3,)
            ),
            PlanStep(
                5, "transfect", "Transfect cells, select, validate knockout.", depends_on=(4,)
            ),
            PlanStep(
                6, "validate_knockout", "Verify frameshift/indel by sequencing.", depends_on=(5,)
            ),
        ]
    if kind == "crispri":
        return [
            PlanStep(1, "design_grna", "Design gRNAs targeting promoter/TSS."),
            PlanStep(2, "check_offtarget", "Screen off-targets.", depends_on=(1,)),
            PlanStep(3, "clone_dcas9_krab", "Clone into dCas9-KRAB vector.", depends_on=(2,)),
            PlanStep(4, "transfect", "Deliver into cells.", depends_on=(3,)),
            PlanStep(5, "measure_knockdown", "Measure mRNA/protein levels.", depends_on=(4,)),
        ]
    if kind == "promoter_swap":
        return [
            PlanStep(1, "select_promoter", "Choose strong promoter (T7, CMV, EF1a)."),
            PlanStep(2, "design_hdr_template", "Design HDR donor with promoter + homology arms."),
            PlanStep(3, "design_grna", "Design gRNA near promoter region.", depends_on=(2,)),
            PlanStep(4, "check_offtarget", "Screen off-targets.", depends_on=(3,)),
            PlanStep(5, "transfect", "Co-deliver gRNA + donor.", depends_on=(4,)),
            PlanStep(6, "validate_insertion", "Verify promoter integration.", depends_on=(5,)),
            PlanStep(7, "measure_expression", "qPCR / Western / fluorescence.", depends_on=(6,)),
        ]
    if kind == "copy_number":
        return [
            PlanStep(1, "choose_plasmid", "Select multicopy plasmid backbone."),
            PlanStep(2, "clone_gene", "Clone gene into plasmid."),
            PlanStep(3, "transform", "Transform into host.", depends_on=(2,)),
            PlanStep(4, "select_clones", "Select clones with resistance marker.", depends_on=(3,)),
        ]
    if kind == "rnai":
        return [
            PlanStep(1, "design_sirna", "Design 3 siRNA sequences."),
            PlanStep(2, "check_specificity", "BLAST to avoid off-targets.", depends_on=(1,)),
            PlanStep(3, "transfect", "Transfect siRNA.", depends_on=(2,)),
            PlanStep(4, "measure_knockdown", "Measure mRNA/protein.", depends_on=(3,)),
        ]
    if kind == "knockin":
        return [
            PlanStep(1, "choose_locus", "Choose safe-harbor locus (e.g., AAVS1, ROSA26)."),
            PlanStep(2, "design_hdr_donor", "Design HDR donor with cargo + arms."),
            PlanStep(3, "design_grna", "Design gRNA to locus.", depends_on=(2,)),
            PlanStep(4, "check_offtarget", "Screen off-targets.", depends_on=(3,)),
            PlanStep(5, "transfect", "Co-deliver gRNA + donor.", depends_on=(4,)),
            PlanStep(6, "validate_knockin", "PCR + sequencing.", depends_on=(5,)),
        ]
    if kind == "point_mutation":
        return [
            PlanStep(1, "choose_base_editor", "Select CBE or ABE based on target base."),
            PlanStep(2, "design_grna", "Design gRNA placing target in editing window."),
            PlanStep(3, "check_offtarget", "Screen off-targets.", depends_on=(2,)),
            PlanStep(4, "transfect", "Deliver base editor + gRNA.", depends_on=(3,)),
            PlanStep(5, "validate_edit", "Sanger / NGS to confirm edit.", depends_on=(4,)),
        ]
    if kind == "pathway_upregulation":
        return [
            PlanStep(1, "map_pathway", "Retrieve full pathway from BioKG."),
            PlanStep(2, "identify_flux_node", "Find rate-limiting enzyme."),
            PlanStep(
                3, "overexpress_node", "Overexpress via promoter swap or plasmid.", depends_on=(2,)
            ),
            PlanStep(4, "measure_output", "Measure metabolite production.", depends_on=(3,)),
        ]

    return [PlanStep(1, "manual_review", f"Custom plan needed for {kind}.")]


def build_plan(goal: Goal, kg: BioKG) -> Plan:
    """Строит план для лучшего вмешательства."""
    iset = map_goal(goal, kg)

    if not iset.primary:
        raise ValueError("No intervention could be mapped for this goal.")

    best = iset.primary[0]
    steps = _steps_for(best)

    plan = Plan(goal=goal, intervention=best, steps=steps, notes=list(iset.notes))
    return plan
