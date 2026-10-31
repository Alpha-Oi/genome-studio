"""Tests for Sanger/NGS simulation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.app import create_app
from genome_studio.simulation import (
    Allele,
    MixtureError,
    default_mixture,
    simulate_ngs,
    simulate_sanger,
    validate_mixture,
)

# --- mixture ------------------------------------------------------------


def test_default_mixture_70_30():
    wt = "ACGT" * 10
    edited = "ACGA" + "CGT" * 9  # arbitrary
    alleles = default_mixture(wt, edited, edited_fraction=0.7)
    assert len(alleles) == 2
    total = sum(a.fraction for a in alleles)
    assert abs(total - 1.0) < 1e-6
    names = {a.name for a in alleles}
    assert names == {"WT", "edited_hom"}


def test_mixture_with_heterozygote():
    wt = "A" * 40
    edited = "T" * 40
    alleles = default_mixture(wt, edited, edited_fraction=0.7, heterozygote_fraction=0.3)
    names = {a.name for a in alleles}
    assert names == {"WT", "edited_hom", "edited_het"}
    total = sum(a.fraction for a in alleles)
    assert abs(total - 1.0) < 1e-6


def test_validate_mixture_bad_sum():
    alleles = [
        Allele("a", 0.5, "ACGT"),
        Allele("b", 0.3, "ACGT"),  # sum = 0.8
    ]
    with pytest.raises(MixtureError):
        validate_mixture(alleles)


def test_validate_mixture_bad_lengths():
    alleles = [
        Allele("a", 0.5, "ACGT"),
        Allele("b", 0.5, "ACGTTT"),
    ]
    with pytest.raises(MixtureError):
        validate_mixture(alleles)


# --- sanger -------------------------------------------------------------


def test_sanger_homozygous():
    wt = "A" * 20
    edited = "T" * 20
    alleles = default_mixture(wt, edited, edited_fraction=1.0)
    peaks = simulate_sanger(alleles)
    # all positions should be pure T
    for p in peaks:
        assert p.T > 0.99
        assert p.A < 0.01
        assert not p.is_mixed


def test_sanger_heterozygous():
    wt = "A" * 20
    edited = "T" * 20
    # 50% WT, 50% edited hom - would give two peaks at each position
    alleles = [
        Allele("wt", 0.5, wt),
        Allele("ed", 0.5, edited),
    ]
    peaks = simulate_sanger(alleles)
    for p in peaks:
        assert abs(p.A - 0.5) < 1e-6
        assert abs(p.T - 0.5) < 1e-6
        assert p.is_mixed  # top/second ratio = 1.0 > 0.3


def test_sanger_window():
    wt = "A" * 100
    edited = "T" * 100
    alleles = default_mixture(wt, edited, edited_fraction=1.0)
    peaks = simulate_sanger(alleles, start=10, end=20)
    assert len(peaks) == 10
    assert peaks[0].position == 10
    assert peaks[-1].position == 19


# --- ngs ----------------------------------------------------------------


def test_ngs_counts():
    alleles = [
        Allele("wt", 0.7, "A" * 10),
        Allele("ed", 0.3, "T" * 10),
    ]
    summary = simulate_ngs(alleles, total_reads=1000)
    assert summary.total_reads == 1000
    assert len(summary.alleles) == 2
    counts = {a.name: a.reads for a in summary.alleles}
    assert counts["wt"] == 700
    assert counts["ed"] == 300


def test_ngs_rounds():
    alleles = [
        Allele("a", 0.333, "A" * 10),
        Allele("b", 0.333, "C" * 10),
        Allele("c", 0.334, "G" * 10),
    ]
    summary = simulate_ngs(alleles, total_reads=1000)
    total = sum(a.reads for a in summary.alleles)
    assert total == 1000


# --- API ----------------------------------------------------------------


def _seqs():
    # same length, differ at one position
    wt = "ATG" + "GCT" * 5 + "TAA"
    edited = "ATG" + "GCT" * 5 + "TAG"  # last codon changed (TAA->TAG)
    return wt, edited


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_sanger_api(client):
    wt, edited = _seqs()
    r = client.post(
        "/simulate/sanger",
        json={
            "wt_sequence": wt,
            "edited_sequence": edited,
            "edited_fraction": 0.5,
            "heterozygote_fraction": 0.0,
            "total_reads": 1000,
            "window": 20,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "peaks" in body
    assert "alleles" in body
    assert len(body["alleles"]) >= 2


def test_ngs_api(client):
    wt, edited = _seqs()
    r = client.post(
        "/simulate/ngs",
        json={
            "wt_sequence": wt,
            "edited_sequence": edited,
            "edited_fraction": 0.6,
            "heterozygote_fraction": 0.2,
            "total_reads": 500,
            "window": 20,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total_reads"] == 500
    total = sum(a["reads"] for a in body["alleles"])
    assert total == 500


def test_sanger_api_length_mismatch(client):
    r = client.post(
        "/simulate/sanger",
        json={
            "wt_sequence": "ACGT" * 5,
            "edited_sequence": "ACGT" * 6,
            "edited_fraction": 0.5,
            "window": 20,
        },
    )
    assert r.status_code == 422
