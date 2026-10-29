"""Tests for export module and endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from genome_studio.api.app import create_app
from genome_studio.export import edit_to_vcf, to_fasta, to_genbank
from genome_studio.simulation import Edit, EditKind


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    from genome_studio.data import db as _db

    _db._engine = None
    _db._session_factory = None
    app = create_app()
    with TestClient(app) as c:
        yield c
    _db._engine = None
    _db._session_factory = None


# --- FASTA --------------------------------------------------------------


def test_fasta_basic():
    out = to_fasta("ACGTACGT", header="test")
    assert out.startswith(">test\n")
    assert "ACGTACGT" in out
    assert out.endswith("\n")


def test_fasta_wrap():
    seq = "A" * 130
    out = to_fasta(seq, header="x", width=60)
    lines = out.strip().split("\n")
    assert lines[0] == ">x"
    assert len(lines[1]) == 60
    assert len(lines[2]) == 60
    assert len(lines[3]) == 10


# --- VCF ----------------------------------------------------------------


def test_vcf_substitution():
    edit = Edit(EditKind.SUBSTITUTION, 5, "T", "C")
    vcf = edit_to_vcf(edit, ref_len=100, gene_name="lacZ")
    assert "##fileformat=VCFv4.2" in vcf
    lines = vcf.strip().split("\n")
    # find the data row (not starting with #)
    data = [ln for ln in lines if not ln.startswith("#")]
    assert len(data) == 1
    cols = data[0].split("\t")
    assert cols[0] == "ref"
    assert cols[1] == "6"  # position + 1
    assert cols[3] == "T"
    assert cols[4] == "C"
    assert "GS_GENE=lacZ" in cols[7]


def test_vcf_deletion():
    edit = Edit(EditKind.DELETION, 10, "ACGT", "")
    vcf = edit_to_vcf(edit, ref_len=100, gene_name="g")
    data = next(ln for ln in vcf.split("\n") if not ln.startswith("#"))
    cols = data.split("\t")
    assert cols[1] == "11"
    assert cols[3] == "ACGT"
    assert cols[4] == "."


def test_vcf_insertion():
    edit = Edit(EditKind.INSERTION, 10, "", "ACGT")
    vcf = edit_to_vcf(edit, ref_len=100, gene_name="g")
    data = next(ln for ln in vcf.split("\n") if not ln.startswith("#"))
    cols = data.split("\t")
    assert cols[1] == "11"
    assert cols[4] == "ACGT"


# --- GenBank ------------------------------------------------------------


def test_genbank_basic():
    seq = "ATGGCTTAA"
    gb = to_genbank(seq, locus="TEST", definition="my test", organism="E. coli")
    assert gb.startswith("LOCUS")
    assert "TEST" in gb
    assert "9 bp" in gb
    assert "DEFINITION  my test" in gb
    assert "ORIGIN" in gb
    assert gb.rstrip().endswith("//")


def test_genbank_origin_has_groups():
    seq = "A" * 70
    gb = to_genbank(seq, locus="x")
    origin_lines = gb.split("ORIGIN")[1].split("//")[0].strip().split("\n")
    # 70 bases -> 2 lines (60 + 10)
    assert len(origin_lines) == 2


# --- API ----------------------------------------------------------------


def _seq():
    return "ATG" + "GCT" * 20 + "TAA"


def test_export_fasta_api(client):
    r = client.post(
        "/export/edit/fasta",
        json={
            "sequence": _seq(),
            "gene_name": "testGene",
            "kind": "substitution",
            "position": 5,
            "ref": "T",
            "alt": "C",
        },
    )
    assert r.status_code == 200
    assert ">testGene_edited" in r.text
    assert r.headers["content-type"].startswith("text/x-fasta")
    assert "attachment" in r.headers["content-disposition"]


def test_export_vcf_api(client):
    r = client.post(
        "/export/edit/vcf",
        json={
            "sequence": _seq(),
            "gene_name": "testGene",
            "kind": "substitution",
            "position": 5,
            "ref": "T",
            "alt": "C",
        },
    )
    assert r.status_code == 200
    assert "##fileformat=VCFv4.2" in r.text
    assert "testGene" in r.text


def test_export_genbank_api(client):
    r = client.post(
        "/export/edit/genbank",
        json={
            "sequence": _seq(),
            "gene_name": "testGene",
            "kind": "substitution",
            "position": 5,
            "ref": "T",
            "alt": "C",
        },
    )
    assert r.status_code == 200
    assert r.text.startswith("LOCUS")
    assert "testGene" in r.text


def test_export_vcf_bad_edit(client):
    r = client.post(
        "/export/edit/vcf",
        json={
            "sequence": _seq(),
            "gene_name": "g",
            "kind": "substitution",
            "position": 5,
            "ref": "G",  # mismatch
            "alt": "C",
        },
    )
    assert r.status_code == 422
