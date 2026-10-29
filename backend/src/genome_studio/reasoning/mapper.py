"""Intervention Mapper - цель -> вмешательства.

На старте - простые правила. Позже - графовые алгоритмы + ML.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from genome_studio.intent.goal import Constraint, Goal, GoalIntent
from genome_studio.knowledge.graph import BioKG, RelationType


@dataclass(frozen=True)
class Intervention:
    """Одно вмешательство."""

    kind: str  # "knockout", "promoter_swap", "crispri", ...
    target_gene: str  # id гена в BioKG
    rationale: str  # почему это предложено
    predicted_effect: float  # 0..1, ожидаемый эффект
    off_target_risk: float  # 0..1
    essentiality_risk: float  # 0..1
    complexity: int  # 1..5, сложность реализации
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass
class InterventionSet:
    """Набор предложенных вмешательств с альтернативами."""

    primary: list[Intervention] = field(default_factory=list)
    alternatives: list[Intervention] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _score(i: Intervention) -> float:
    """Простая функция ранжирования."""
    return (
        i.predicted_effect * 1.0
        - i.off_target_risk * 0.5
        - i.essentiality_risk * 0.7
        - (i.complexity - 1) * 0.1
    )


def _knows_gene(kg: BioKG, gene_name: str, organism: str) -> tuple[str | None, bool]:
    """Ищет ген в KG. Возвращает (gene_id, is_essential)."""
    node = kg.find_gene_by_name(gene_name, organism)
    if node is None:
        return None, False
    return node.id, node.essential


def map_goal(goal: Goal, kg: BioKG) -> InterventionSet:
    """Из цели строит набор вмешательств."""
    result = InterventionSet()
    gene_id, essential = _knows_gene(kg, goal.target.gene, goal.target.organism.value)

    if gene_id is None:
        result.notes.append(
            f"Gene {goal.target.gene!r} not in BioKG for {goal.target.organism.value}. "
            "Fallback to name-based suggestions."
        )
        gene_id = f"{goal.target.organism.value}.{goal.target.gene}"

    # --- Прямые цели ---------------------------------------------------
    if goal.intent == GoalIntent.KNOCKOUT:
        result.primary.append(
            Intervention(
                kind="knockout",
                target_gene=gene_id,
                rationale=f"Direct knockout of {goal.target.gene}.",
                predicted_effect=0.85,
                off_target_risk=0.2,
                essentiality_risk=0.9 if essential else 0.1,
                complexity=2,
                evidence=("standard CRISPR-Cas9 knockout",),
                warnings=("Gene is essential; knockout likely lethal.",) if essential else (),
            )
        )
        result.alternatives.append(
            Intervention(
                kind="crispri",
                target_gene=gene_id,
                rationale="Partial knockdown via CRISPRi, safer if essential.",
                predicted_effect=0.6,
                off_target_risk=0.1,
                essentiality_risk=0.3 if essential else 0.05,
                complexity=3,
                evidence=("dCas9-KRAB repression",),
            )
        )

    elif goal.intent == GoalIntent.INCREASE_EXPRESSION:
        result.primary.append(
            Intervention(
                kind="promoter_swap",
                target_gene=gene_id,
                rationale=f"Replace native promoter of {goal.target.gene} with strong one (e.g., T7, CMV).",
                predicted_effect=0.8,
                off_target_risk=0.05,
                essentiality_risk=0.05,
                complexity=3,
                evidence=("standard promoter engineering",),
            )
        )
        result.alternatives.append(
            Intervention(
                kind="copy_number",
                target_gene=gene_id,
                rationale="Increase gene copy number via multicopy plasmid.",
                predicted_effect=0.7,
                off_target_risk=0.1,
                essentiality_risk=0.1,
                complexity=2,
            )
        )

        # Если есть репрессор - предложить нокаут репрессора
        for edge in kg.incoming(gene_id, RelationType.INHIBITS):
            repressor_id = edge.source
            repressor = kg.genes.get(repressor_id)
            if repressor is not None:
                result.alternatives.append(
                    Intervention(
                        kind="knockout",
                        target_gene=repressor_id,
                        rationale=f"Knockout repressor {repressor.name} to de-repress {goal.target.gene}.",
                        predicted_effect=0.75,
                        off_target_risk=0.2,
                        essentiality_risk=0.9 if repressor.essential else 0.15,
                        complexity=2,
                        evidence=("repressor gene identified in BioKG",),
                    )
                )

    elif goal.intent == GoalIntent.DECREASE_EXPRESSION:
        result.primary.append(
            Intervention(
                kind="crispri",
                target_gene=gene_id,
                rationale=f"CRISPRi knockdown of {goal.target.gene}.",
                predicted_effect=0.7,
                off_target_risk=0.1,
                essentiality_risk=0.3 if essential else 0.05,
                complexity=3,
                evidence=("dCas9-KRAB repression",),
                warnings=("Gene is essential; strong knockdown may reduce growth.",)
                if essential
                else (),
            )
        )
        result.alternatives.append(
            Intervention(
                kind="rnai",
                target_gene=gene_id,
                rationale="RNAi knockdown (transient).",
                predicted_effect=0.5,
                off_target_risk=0.3,
                essentiality_risk=0.2,
                complexity=2,
            )
        )

    elif goal.intent == GoalIntent.KNOCKIN:
        result.primary.append(
            Intervention(
                kind="knockin",
                target_gene=gene_id,
                rationale="Insert gene at safe-harbor locus via HDR.",
                predicted_effect=0.7,
                off_target_risk=0.15,
                essentiality_risk=0.05,
                complexity=5,
                evidence=("HDR-mediated insertion",),
            )
        )

    elif goal.intent == GoalIntent.MODIFY_FUNCTION:
        result.primary.append(
            Intervention(
                kind="point_mutation",
                target_gene=gene_id,
                rationale="Introduce targeted point mutation via base editing.",
                predicted_effect=0.6,
                off_target_risk=0.15,
                essentiality_risk=0.2,
                complexity=3,
                evidence=("base editing (CBE/ABE)",),
            )
        )

    elif goal.intent == GoalIntent.PRODUCE_METABOLITE:
        pathways = kg.pathways_of_gene(gene_id)
        if pathways:
            for p in pathways:
                result.primary.append(
                    Intervention(
                        kind="pathway_upregulation",
                        target_gene=gene_id,
                        rationale=f"Upregulate entry into pathway {p.name}.",
                        predicted_effect=0.6,
                        off_target_risk=0.1,
                        essentiality_risk=0.1,
                        complexity=4,
                        evidence=(f"pathway: {p.name}",),
                    )
                )
        else:
            result.primary.append(
                Intervention(
                    kind="pathway_upregulation",
                    target_gene=gene_id,
                    rationale="Overexpress pathway entry point.",
                    predicted_effect=0.5,
                    off_target_risk=0.1,
                    essentiality_risk=0.1,
                    complexity=4,
                )
            )

    else:
        result.notes.append(f"No direct strategy for intent {goal.intent.value}.")

    # --- Ограничения ---------------------------------------------------
    if Constraint.DO_NOT_MODIFY_CDS in goal.constraints:
        result.primary = [i for i in result.primary if i.kind != "point_mutation"]
        result.alternatives = [i for i in result.alternatives if i.kind != "point_mutation"]
        result.notes.append("DO_NOT_MODIFY_CDS respected: point mutations filtered out.")

    # --- Сортировка ----------------------------------------------------
    result.primary.sort(key=_score, reverse=True)
    result.alternatives.sort(key=_score, reverse=True)

    return result
