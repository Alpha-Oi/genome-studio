"""Tests for Reasoning Layer (mapper + planner)."""

from __future__ import annotations

import pytest

from genome_studio.intent.parser import parse_goal
from genome_studio.knowledge.seed import build_default_kg
from genome_studio.reasoning.mapper import map_goal
from genome_studio.reasoning.planner import build_plan


@pytest.fixture
def kg():
    return build_default_kg()


def test_kg_has_ecoli_lacz(kg):
    gene = kg.find_gene_by_name("lacZ", "Escherichia coli")
    assert gene is not None
    assert gene.id == "ecoli.lacZ"


def test_kg_laci_inhibits_lacz(kg):
    from genome_studio.knowledge.graph import RelationType
    edges = kg.outgoing("ecoli.lacI", RelationType.INHIBITS)
    assert any(e.target == "ecoli.lacZ" for e in edges)


def test_map_knockout_essential(kg):
    goal = parse_goal("knockout gene recA in E. coli")
    iset = map_goal(goal, kg)
    assert iset.primary, "should suggest at least one intervention"
    top = iset.primary[0]
    assert top.kind == "knockout"
    assert top.essentiality_risk > 0.5
    assert any("essential" in w.lower() for w in top.warnings)


def test_map_increase_expression_suggests_repressor_knockout(kg):
    goal = parse_goal("increase expression of gene lacZ in E. coli")
    iset = map_goal(goal, kg)
    kinds = [i.kind for i in iset.primary + iset.alternatives]
    assert "promoter_swap" in kinds
    # должен предложить нокаут lacI как альтернативу
    lacI_alt = [i for i in iset.alternatives if i.target_gene == "ecoli.lacI"]
    assert lacI_alt, "should suggest knocking out lacI repressor"


def test_build_plan_for_knockout(kg):
    goal = parse_goal("knockout gene lacZ in E. coli")
    plan = build_plan(goal, kg)
    assert plan.intervention.kind == "knockout"
    assert len(plan.steps) >= 4
    actions = [s.action for s in plan.steps]
    assert "design_grna" in actions


def test_build_plan_for_increase(kg):
    goal = parse_goal("increase expression of gene lacZ in E. coli")
    plan = build_plan(goal, kg)
    assert plan.intervention.kind == "promoter_swap"
    assert len(plan.steps) >= 5


def test_do_not_modify_cds_respected(kg):
    from genome_studio.intent.goal import Constraint
    goal = parse_goal("modify gene lacZ in E. coli, do not modify CDS")
    assert Constraint.DO_NOT_MODIFY_CDS in goal.constraints
    iset = map_goal(goal, kg)
    kinds = [i.kind for i in iset.primary + iset.alternatives]
    assert "point_mutation" not in kinds