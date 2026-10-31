"""Tests for Goal Object."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from genome_studio.intent.goal import (
    Constraint,
    Direction,
    Goal,
    GoalIntent,
    Organism,
    PhenotypeTarget,
    Target,
)


def test_target_valid():
    t = Target(gene="lacZ", organism=Organism.E_COLI)
    assert t.gene == "lacZ"
    assert t.organism == Organism.E_COLI
    assert t.cell_line is None


def test_target_rejects_empty_gene():
    with pytest.raises(ValidationError):
        Target(gene="   ", organism=Organism.E_COLI)


def test_target_is_frozen():
    t = Target(gene="lacZ", organism=Organism.E_COLI)
    with pytest.raises(ValidationError):
        t.gene = "other"  # type: ignore[misc]


def test_phenotype_target():
    p = PhenotypeTarget(
        metric="protein_yield",
        direction=Direction.UP,
        magnitude=">=2x",
    )
    assert p.direction == Direction.UP
    assert p.magnitude == ">=2x"


def test_goal_full():
    g = Goal(
        raw_text="increase expression of gene lacZ in E. coli",
        intent=GoalIntent.INCREASE_EXPRESSION,
        target=Target(gene="lacZ", organism=Organism.E_COLI),
        phenotype_target=PhenotypeTarget(metric="protein_yield", direction=Direction.UP),
        constraints=(Constraint.DO_NOT_MODIFY_CDS,),
        confidence=0.9,
    )
    assert g.intent == GoalIntent.INCREASE_EXPRESSION
    assert g.target.gene == "lacZ"
    assert Constraint.DO_NOT_MODIFY_CDS in g.constraints


def test_goal_confidence_bounds():
    with pytest.raises(ValidationError):
        Goal(
            raw_text="x",
            intent=GoalIntent.KNOCKOUT,
            target=Target(gene="x", organism=Organism.E_COLI),
            confidence=1.5,
        )


def test_goal_to_dict():
    g = Goal(
        raw_text="x",
        intent=GoalIntent.KNOCKOUT,
        target=Target(gene="lacZ", organism=Organism.E_COLI),
    )
    d = g.to_dict()
    assert d["intent"] == "knockout"
    assert d["target"]["gene"] == "lacZ"
    assert d["target"]["organism"] == "Escherichia coli"
