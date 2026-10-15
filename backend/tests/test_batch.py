"""Tests for batch design endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    from genome_studio.data import db as _db
    _db._engine = None
    _db._session_factory = None
    app = create_app()
    with TestClient(app) as c:
        yield c
    _db._engine = None
    _db._session_factory = None


def _seq_with_pam():
    # 20 spacer + PAM + filler
    return "ACGTACGTACGTACGTACGT" + "C" + "GG" + "GGGGCCCCGGGGCCCCGGGG" + "A" + "GG"


def test_batch_design_single(client):
    r = client.post(
        "/batch/design",
        json={
            "sequences": [{"name": "gene1", "sequence": _seq_with_pam()}],
            "top_n": 3,
            "min_score": 0.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 1
    res = body["results"][0]
    assert res["name"] == "gene1"
    assert res["length"] > 0
    assert len(res["guides"]) >= 1
    assert res["error"] is None


def test_batch_design_multi(client):
    r = client.post(
        "/batch/design",
        json={
            "sequences": [
                {"name": "a", "sequence": _seq_with_pam()},
                {"name": "b", "sequence": _seq_with_pam()},
                {"name": "c", "sequence": _seq_with_pam()},
            ],
            "top_n": 2,
            "min_score": 0.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert len(body["results"]) == 3
    names = [r["name"] for r in body["results"]]
    assert names == ["a", "b", "c"]


def test_batch_design_short_sequence(client):
    r = client.post(
        "/batch/design",
        json={
            "sequences": [{"name": "short", "sequence": "ACGTACGT"}],
            "top_n": 3,
            "min_score": 0.0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["results"][0]["error"] is not None
    assert body["results"][0]["guides"] == []


def test_batch_design_empty_list_rejected(client):
    r = client.post(
        "/batch/design",
        json={"sequences": [], "top_n": 3, "min_score": 0.0},
    )
    assert r.status_code == 422