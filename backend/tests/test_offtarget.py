"""Tests for off-target screening."""

from __future__ import annotations

from genome_studio.crispr.offtarget import (
    find_offtargets,
    hamming,
    off_target_risk,
)


def test_hamming_identical():
    assert hamming("ACGT", "ACGT") == 0


def test_hamming_one():
    assert hamming("ACGT", "ACGA") == 1


def test_hamming_length_mismatch():
    import pytest
    with pytest.raises(ValueError):
        hamming("ACGT", "ACG")


def test_find_offtargets_perfect_match():
    # guide = 20 A's; reference has that + PAM
    guide = "A" * 20
    ref = "A" * 20 + "C" + "GG"
    hits = find_offtargets(guide, ref, max_mismatches=0)
    assert len(hits) == 1
    assert hits[0].mismatches == 0
    assert hits[0].strand == "+"


def test_find_offtargets_one_mismatch():
    guide = "A" * 20
    # candidate has one C in spacer
    cand = "A" * 10 + "C" + "A" * 9
    ref = cand + "C" + "GG"
    hits = find_offtargets(guide, ref, max_mismatches=1)
    assert len(hits) >= 1
    assert any(h.mismatches == 1 for h in hits)


def test_find_offtargets_no_hits_above_threshold():
    guide = "A" * 20
    cand = "C" * 20
    ref = cand + "C" + "GG"
    hits = find_offtargets(guide, ref, max_mismatches=2)
    assert hits == []


def test_off_target_risk_empty():
    r = off_target_risk([])
    assert r["total"] == 0
    assert r["risk"] == 0.0


def test_off_target_risk_perfect():
    guide = "A" * 20
    ref = "A" * 20 + "C" + "GG"
    hits = find_offtargets(guide, ref, max_mismatches=4)
    r = off_target_risk(hits)
    assert r["perfect"] == 1
    assert r["near"] == 0
    # risk from perfect = 0 (perfect hit is the target itself)
    assert r["risk"] == 0.0


def test_off_target_risk_near_miss():
    guide = "A" * 20
    cand = "A" * 10 + "C" + "A" * 9  # 1 mismatch
    ref = "A" * 20 + "C" + "GG" + "GGGG" + cand + "C" + "GG"
    hits = find_offtargets(guide, ref, max_mismatches=4)
    r = off_target_risk(hits)
    assert r["perfect"] >= 1
    assert r["near"] >= 1
    assert r["risk"] > 0.0


# --- API ------------------------------------------------------------------

def test_offtarget_api_endpoint():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)

    guide = "ACGTACGTACGTACGTACGT"
    ref = "ACGTACGTACGTACGTACGT" + "C" + "GG" + "GGGGCCCC" + guide[:10] + "TTTT" + "TTTTTT"

    r = client.post(
        "/crispr/offtarget",
        json={
            "guide_spacer": guide,
            "reference": ref,
            "max_mismatches": 4,
            "reference_label": "test",
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "hits" in body
    assert "summary" in body
    assert body["summary"]["perfect"] >= 1


def test_offtarget_api_bad_guide_length():
    from fastapi.testclient import TestClient
    from genome_studio.api.app import create_app

    app = create_app()
    client = TestClient(app)
    r = client.post(
        "/crispr/offtarget",
        json={"guide_spacer": "ACGT", "reference": "A" * 50},
    )
    assert r.status_code == 422