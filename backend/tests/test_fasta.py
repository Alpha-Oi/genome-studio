"""Tests for FASTA parser."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from genome_studio.api.app import create_app
from genome_studio.io.fasta import FastaError, parse_fasta

# --- parser -------------------------------------------------------------


def test_parse_single_record():
    text = ">gene1 description here\nACGTACGT\nACGTACGT\n"
    records = parse_fasta(text)
    assert len(records) == 1
    r = records[0]
    assert r.name == "gene1"
    assert r.description == "description here"
    assert r.sequence == "ACGTACGTACGTACGT"
    assert r.length == 16


def test_parse_multi_records():
    text = ">seq1\nACGTACGT\n>seq2 some desc\nTTTTGGGG\n>seq3\nAAAACCCC\n"
    records = parse_fasta(text)
    assert len(records) == 3
    assert records[0].name == "seq1"
    assert records[0].description == ""
    assert records[1].name == "seq2"
    assert records[1].description == "some desc"
    assert records[2].sequence == "AAAACCCC"


def test_parse_lowercase_uppercased():
    text = ">x\nacgtacgt\n"
    r = parse_fasta(text)[0]
    assert r.sequence == "ACGTACGT"


def test_parse_strips_non_acgtn():
    text = ">x\nACGT-ACGT NNN 123\n"
    r = parse_fasta(text)[0]
    assert r.sequence == "ACGTACGTNNN"


def test_parse_empty_raises():
    with pytest.raises(FastaError):
        parse_fasta("")
    with pytest.raises(FastaError):
        parse_fasta("   \n  \n")


def test_parse_no_header_unnamed():
    text = "ACGTACGT\nACGTACGT\n"
    records = parse_fasta(text)
    assert len(records) == 1
    assert records[0].name == "unnamed"
    assert records[0].sequence == "ACGTACGTACGTACGT"


def test_gc_content():
    text = ">x\nGCGCATAT\n"  # 50% GC
    r = parse_fasta(text)[0]
    assert abs(r.gc_content - 0.5) < 1e-6


def test_to_dict():
    text = ">gene1\nACGT\n"
    d = parse_fasta(text)[0].to_dict()
    assert d["name"] == "gene1"
    assert d["sequence"] == "ACGT"
    assert d["length"] == 4
    assert "gc_content" in d


# --- API ----------------------------------------------------------------


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


def test_parse_fasta_endpoint_single(client):
    r = client.post(
        "/parse/fasta",
        json={"content": ">gene1 test\nACGTACGTACGT\n"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["records"]) == 1
    assert body["records"][0]["name"] == "gene1"
    assert body["records"][0]["sequence"] == "ACGTACGTACGT"


def test_parse_fasta_endpoint_multi(client):
    r = client.post(
        "/parse/fasta",
        json={"content": ">a\nACGT\n>b\nTTTT\n>c\nGGGG\n"},
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["records"]) == 3
    assert [rec["name"] for rec in body["records"]] == ["a", "b", "c"]


def test_parse_fasta_endpoint_bad_input(client):
    r = client.post("/parse/fasta", json={"content": "   "})
    assert r.status_code == 422
