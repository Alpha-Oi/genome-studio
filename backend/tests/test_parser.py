"""Tests for Intent Parser."""

from __future__ import annotations

import pytest

from genome_studio.intent.goal import Constraint, Direction, GoalIntent, Organism
from genome_studio.intent.parser import ParseError, parse_goal


def test_parse_increase_expression():
    g = parse_goal("increase expression of gene lacZ in E. coli")
    assert g.intent == GoalIntent.INCREASE_EXPRESSION
    assert g.target.gene == "lacZ"
    assert g.target.organism == Organism.E_COLI
    assert g.phenotype_target is not None
    assert g.phenotype_target.direction == Direction.UP


def test_parse_knockout_russian():
    g = parse_goal("сделай нокаут гена GAL1 в дрожжах")
    assert g.intent == GoalIntent.KNOCKOUT
    assert g.target.gene == "GAL1"
    assert g.target.organism == Organism.YEAST


def test_parse_decrease_expression():
    g = parse_goal("downregulate gene TPI1 in yeast")
    assert g.intent == GoalIntent.DECREASE_EXPRESSION
    assert g.target.gene == "TPI1"
    assert g.target.organism == Organism.YEAST


def test_parse_with_constraints():
    g = parse_goal("increase expression of gene X in E. coli, do not modify CDS")
    assert Constraint.DO_NOT_MODIFY_CDS in g.constraints


def test_parse_stable_integration_constraint():
    g = parse_goal("knock-in of gene GFP in CHO, stable integration")
    assert Constraint.STABLE_INTEGRATION in g.constraints


def test_parse_error_empty():
    with pytest.raises(ParseError):
        parse_goal("")


def test_parse_error_no_intent():
    with pytest.raises(ParseError):
        parse_goal("hello world")


def test_parse_error_no_organism():
    with pytest.raises(ParseError):
        parse_goal("increase expression of gene lacZ")


def test_parse_error_no_gene():
    with pytest.raises(ParseError):
        parse_goal("knockout something in E. coli")