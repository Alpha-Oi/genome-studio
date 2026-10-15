"""JSON report builder - consolidated view of a plan + edit."""

from __future__ import annotations

from datetime import datetime, timezone

from genome_studio.reasoning.planner import Plan
from genome_studio.simulation.effects import EditEffect
from genome_studio.simulation.consequence import ConsequenceNode


def build_report(
    *,
    title: str,
    plan: Plan | None = None,
    effect: EditEffect | None = None,
    consequence_tree: ConsequenceNode | None = None,
    warnings: list[dict] | None = None,
    project_name: str = "",
) -> dict:
    """Build a consolidated JSON report.

    Any of plan/effect/tree/warnings may be omitted.
    """
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generator": "Genome Studio",
        "title": title,
        "project_name": project_name,
    }

    if plan is not None:
        report["plan"] = plan.to_dict()

    if effect is not None:
        report["edit_effect"] = effect.to_dict()

    if consequence_tree is not None:
        report["consequence_tree"] = consequence_tree.to_dict()

    if warnings:
        report["warnings"] = warnings

    return report