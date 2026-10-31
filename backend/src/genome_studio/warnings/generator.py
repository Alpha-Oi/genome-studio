"""Generate warnings automatically from interventions and effects.

Rule-based. Later can plug in ML predictors.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from genome_studio.reasoning.mapper import InterventionSet
from genome_studio.reasoning.planner import Plan
from genome_studio.simulation.effects import EditEffect, EffectType
from genome_studio.warnings.models import WarningLevel, WarningSeverity
from genome_studio.warnings.registry import create_warning


async def warnings_from_plan(
    session: AsyncSession,
    *,
    project_id: int,
    plan: Plan,
    iset: InterventionSet,
    experiment_id: int | None = None,
) -> list[int]:
    """Create warnings for a plan (all interventions + alternatives)."""
    created: list[int] = []
    gene = plan.goal.target.gene

    all_interventions = list(iset.primary) + list(iset.alternatives)
    for iv in all_interventions:
        if iv.essentiality_risk >= 0.7:
            w = await create_warning(
                session,
                project_id=project_id,
                level=WarningLevel.T0_SCIENCE,
                severity=WarningSeverity.HIGH,
                type="essential_gene_risk",
                message=(
                    f"Intervention {iv.kind!r} targets essential gene {gene!r}. "
                    f"Essentiality risk {iv.essentiality_risk:.2f}; may be lethal."
                ),
                evidence=list(iv.warnings) + list(iv.evidence),
                experiment_id=experiment_id,
                target_gene=gene,
            )
            created.append(w.id)

    for iv in all_interventions:
        if iv.off_target_risk >= 0.25:
            w = await create_warning(
                session,
                project_id=project_id,
                level=WarningLevel.T0_SCIENCE,
                severity=WarningSeverity.MEDIUM,
                type="off_target_risk",
                message=(
                    f"Intervention {iv.kind!r} on {gene!r} has elevated off-target "
                    f"risk {iv.off_target_risk:.2f}. Screen carefully."
                ),
                evidence=list(iv.evidence),
                experiment_id=experiment_id,
                target_gene=gene,
            )
            created.append(w.id)

    for iv in all_interventions:
        if iv.complexity >= 5:
            w = await create_warning(
                session,
                project_id=project_id,
                level=WarningLevel.T0_SCIENCE,
                severity=WarningSeverity.LOW,
                type="high_complexity",
                message=(
                    f"Intervention {iv.kind!r} has complexity {iv.complexity}/5. "
                    "Plan extra validation steps."
                ),
                experiment_id=experiment_id,
                target_gene=gene,
            )
            created.append(w.id)

    return created


async def warnings_from_effect(
    session: AsyncSession,
    *,
    project_id: int,
    gene_name: str,
    effect: EditEffect,
    experiment_id: int | None = None,
) -> list[int]:
    """Create warnings from a simulated edit effect."""
    created: list[int] = []

    if effect.effect_type == EffectType.FRAMESHIFT:
        w = await create_warning(
            session,
            project_id=project_id,
            level=WarningLevel.T0_SCIENCE,
            severity=WarningSeverity.HIGH,
            type="frameshift",
            message=(
                f"Frameshift in {gene_name!r}: downstream protein almost certainly "
                "non-functional. Verify by sequencing."
            ),
            evidence=[effect.description],
            experiment_id=experiment_id,
            target_gene=gene_name,
        )
        created.append(w.id)

    elif effect.effect_type == EffectType.NONSENSE:
        w = await create_warning(
            session,
            project_id=project_id,
            level=WarningLevel.T0_SCIENCE,
            severity=WarningSeverity.MEDIUM,
            type="premature_stop",
            message=(
                f"Premature stop codon in {gene_name!r}: likely loss-of-function and possible NMD."
            ),
            evidence=[effect.description],
            experiment_id=experiment_id,
            target_gene=gene_name,
        )
        created.append(w.id)

    elif effect.effect_type == EffectType.MISSENSE:
        w = await create_warning(
            session,
            project_id=project_id,
            level=WarningLevel.T0_SCIENCE,
            severity=WarningSeverity.LOW,
            type="missense",
            message=(
                f"Missense mutation in {gene_name!r}: functional impact uncertain, "
                "requires experimental validation."
            ),
            evidence=[effect.description],
            experiment_id=experiment_id,
            target_gene=gene_name,
        )
        created.append(w.id)

    return created
