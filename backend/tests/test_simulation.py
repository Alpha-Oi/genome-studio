"""Tests for simulation module."""

from __future__ import annotations

import pytest
from genome_studio.simulation import (
    Edit,
    EditError,
    EditKind,
    apply_edit,
    build_consequence_tree,
    find_orfs,
    predict_effect,
    translate,
)
from genome_studio.simulation.effects import EffectType

# --- edit -----------------------------------------------------------------


def test_apply_substitution():
    seq = "ACGTACGT"
    edit = Edit(EditKind.SUBSTITUTION, 0, "A", "T")
    assert apply_edit(seq, edit) == "TCGTACGT"


def test_apply_substitution_ref_mismatch():
    seq = "ACGT"
    edit = Edit(EditKind.SUBSTITUTION, 0, "G", "T")
    with pytest.raises(EditError):
        apply_edit(seq, edit)


def test_apply_insertion():
    seq = "ACGT"
    edit = Edit(EditKind.INSERTION, 2, "", "TT")
    assert apply_edit(seq, edit) == "ACTTGT"


def test_apply_deletion():
    seq = "ACGTACGT"
    edit = Edit(EditKind.DELETION, 2, "GT", "")
    assert apply_edit(seq, edit) == "ACACGT"


def test_apply_deletion_mismatch():
    with pytest.raises(EditError):
        apply_edit("ACGT", Edit(EditKind.DELETION, 0, "TT", ""))


# --- translate / orf ------------------------------------------------------


def test_translate_simple():
    # ATG = M, GCT = A, TAA = *
    assert translate("ATGGCTTAA") == "MA*"


def test_find_orfs_simple():
    seq = "AA" + "ATG" + "GCT" * 20 + "TAA" + "AA"
    orfs = find_orfs(seq, min_length_aa=10)
    assert len(orfs) >= 1
    top = orfs[0]
    assert top.protein.startswith("M")
    assert top.protein[1:4] == "AAA"  # GCT GCT GCT


# --- effects --------------------------------------------------------------


def _make_orf(start_offset: int = 0, n_codons: int = 20) -> str:
    """Build DNA with one clean ORF."""
    seq = "A" * start_offset + "ATG" + ("GCT" * n_codons) + "TAA"
    return seq


def test_effect_outside_orf():
    seq = _make_orf(start_offset=5)
    # edit at position 0 (before ATG)
    edit = Edit(EditKind.SUBSTITUTION, 0, "A", "C")
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.OUTSIDE_ORF


def test_effect_silent():
    # ATG GCT GCT ... ; mutate 2nd position of GCT (GCT -> GCC, both Ala)
    seq = "ATG" + "GCT" + "GCT" * 20 + "TAA"
    # codon index 1 starts at position 3. GCT -> GCC: change position 5 (T->C)
    edit = Edit(EditKind.SUBSTITUTION, 5, "T", "C")
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.SILENT


def test_effect_missense():
    # GCT (Ala) -> CCT (Pro): position 3 G->C
    seq = "ATG" + "GCT" + "GCT" * 20 + "TAA"
    edit = Edit(EditKind.SUBSTITUTION, 3, "G", "C")
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.MISSENSE
    assert "A" in eff.description and "P" in eff.description


def test_effect_nonsense():
    # GCT -> TAA (stop): need 3 changes... use TAT->TAA instead for simplicity
    # Let's build ORF with TAT codon then mutate 3rd position: TAT (Tyr) -> TAA (stop)
    seq = "ATG" + "TAT" + "GCT" * 20 + "TAA"
    edit = Edit(EditKind.SUBSTITUTION, 5, "T", "A")  # 3rd position of TAT
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.NONSENSE


def test_effect_frameshift():
    seq = _make_orf()
    # Insert 1 base - frameshift
    edit = Edit(EditKind.INSERTION, 5, "", "A")
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.FRAMESHIFT


def test_effect_in_frame_indel():
    seq = _make_orf()
    # Insert 3 bases - in frame
    edit = Edit(EditKind.INSERTION, 5, "", "AAA")
    eff = predict_effect(seq, edit)
    assert eff.effect_type == EffectType.IN_FRAME_INDEL


# --- consequence tree -----------------------------------------------------


def test_consequence_tree_structure():
    seq = _make_orf()
    edit = Edit(EditKind.INSERTION, 5, "", "A")
    eff = predict_effect(seq, edit)
    tree = build_consequence_tree("testGene", eff)
    assert tree.type == "edit"
    assert len(tree.children) == 1
    t = tree.children[0]
    assert t.type == "transcript"
    assert len(t.children) == 1
    p = t.children[0]
    assert p.type == "protein"
    assert len(p.children) == 1
    pw = p.children[0]
    assert pw.type == "pathway"
    assert len(pw.children) == 1
    assert pw.children[0].type == "phenotype"


def test_consequence_tree_to_dict():
    seq = _make_orf()
    edit = Edit(EditKind.SUBSTITUTION, 5, "T", "C")
    eff = predict_effect(seq, edit)
    tree = build_consequence_tree("g", eff)
    d = tree.to_dict()
    assert d["type"] == "edit"
    assert isinstance(d["children"], list)
    assert d["children"][0]["type"] == "transcript"


# --- API ------------------------------------------------------------------


def test_simulate_api_substitution():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)

    seq = "ATG" + "GCT" * 20 + "TAA"
    r = client.post(
        "/simulate/edit",
        json={
            "sequence": seq,
            "gene_name": "testGene",
            "kind": "substitution",
            "position": 5,
            "ref": "T",
            "alt": "C",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "edited_sequence" in body
    assert "effect" in body
    assert body["effect"]["effect_type"] == "silent"
    assert "consequence_tree" in body


def test_simulate_api_frameshift():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)

    seq = "ATG" + "GCT" * 20 + "TAA"
    r = client.post(
        "/simulate/edit",
        json={
            "sequence": seq,
            "gene_name": "testGene",
            "kind": "insertion",
            "position": 5,
            "ref": "",
            "alt": "A",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["effect"]["effect_type"] == "frameshift"


def test_simulate_api_bad_kind():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.post(
        "/simulate/edit",
        json={
            "sequence": "ATGGCTTAA",
            "kind": "weird",
            "position": 0,
            "ref": "",
            "alt": "",
        },
    )
    assert r.status_code == 422
