"""Tests for CRISPR module."""

from __future__ import annotations

import pytest

from genome_studio.crispr.designer import design_guides
from genome_studio.crispr.pam import find_pam_sites
from genome_studio.crispr.scoring import gc_content, has_homopolymer, has_polyt, score_guide


# --- pam.py ---------------------------------------------------------------

def test_find_pam_basic():
    # spacer(20) + N + GG
    seq = "A" * 20 + "C" + "GG"
    hits = find_pam_sites(seq, both_strands=False)
    assert len(hits) == 1
    assert hits[0].pam == "CGG"
    assert hits[0].spacer == "A" * 20
    assert hits[0].position == 20
    assert hits[0].strand == "+"


def test_find_pam_no_hit():
    seq = "A" * 30  # no GG
    hits = find_pam_sites(seq, both_strands=False)
    assert hits == []


def test_find_pam_both_strands():
    seq = "A" * 20 + "C" + "GG"
    hits = find_pam_sites(seq, both_strands=True)
    # reverse complement contains CC + G + TTT... no PAM there
    # but at least the + hit exists
    assert any(h.strand == "+" for h in hits)


def test_find_pam_multiple():
    seq = "A" * 20 + "C" + "GG" + "A" * 20 + "T" + "GG"
    hits = find_pam_sites(seq, both_strands=False)
    assert len(hits) == 2
    assert hits[0].pam == "CGG"
    assert hits[1].pam == "TGG"


# --- scoring.py -----------------------------------------------------------

def test_gc_content():
    assert gc_content("GCGC") == 1.0
    assert gc_content("ATAT") == 0.0
    assert gc_content("GCAT") == 0.5


def test_has_polyt():
    assert has_polyt("AAAATTTTAAA")
    assert not has_polyt("AAAATTTAAA")


def test_has_homopolymer():
    assert has_homopolymer("AAAAA", 5)
    assert not has_homopolymer("AAAA", 5)


def test_score_perfect_guide():
    # 40-60% GC, no TTTT, no homopolymer, ends with G
    s = score_guide("ACGTACGTACGTACGTACGG")
    assert s["score"] >= 0.8
    assert any("optimal" in r.lower() for r in s["reasons"])


def test_score_low_gc():
    s = score_guide("ATATATATATATATATATAT")
    assert s["score"] < 0.8
    assert any("GC" in w for w in s["warnings"])


def test_score_polyt_warning():
    s = score_guide("ACGTACGTTTTTACGTACGT")
    assert any("TTTT" in w for w in s["warnings"])


# --- designer.py ----------------------------------------------------------

def test_design_guides_from_sequence():
    # Build sequence with 2 PAM sites, well-spaced, good GC
    seq = (
        "ACGTACGTACGTACGTACGT"  # 20 nt spacer 1
        + "C" + "GG"             # PAM 1
        + "GGGGCCCCGGGGCCCCGGGG" # filler (good GC)
        + "A" + "GG"             # PAM 2
        + "TTTTAAAATTTTAAAATTTT"
    )
    guides = design_guides(seq, top_n=5, min_score=0.0)
    assert len(guides) >= 2
    # sorted by score descending
    scores = [g.score for g in guides]
    assert scores == sorted(scores, reverse=True)


def test_design_guides_respects_min_score():
    seq = "ATATATATATATATATATAT" + "C" + "GG" + "A" * 30
    guides_strict = design_guides(seq, min_score=0.9)
    guides_loose = design_guides(seq, min_score=0.0)
    assert len(guides_loose) >= len(guides_strict)


def test_design_guides_top_n():
    seq = ("ACGTACGTACGTACGTACGT" + "C" + "GG") * 10
    guides = design_guides(seq, top_n=3, min_score=0.0)
    assert len(guides) <= 3


# --- API ------------------------------------------------------------------

def test_crispr_api_endpoint():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)

    seq = "ACGTACGTACGTACGTACGT" + "C" + "GG" + "GGGGCCCCGGGGCCCCGGGG" + "A" + "GG"
    r = client.post("/crispr/design", json={"sequence": seq, "top_n": 5, "min_score": 0.0})
    assert r.status_code == 200
    body = r.json()
    assert "guides" in body
    assert len(body["guides"]) >= 1
    g = body["guides"][0]
    assert "spacer" in g
    assert len(g["spacer"]) == 20
    assert "score" in g


def test_crispr_api_short_sequence():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.post("/crispr/design", json={"sequence": "ACGT"})
    assert r.status_code == 422