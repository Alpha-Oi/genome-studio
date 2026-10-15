"""Tests for Warnings Registry."""

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


@pytest.fixture
def pid(client):
    return client.post("/projects", json={"name": "WTest"}).json()["project"]["id"]


def test_no_warnings_initially(client, pid):
    r = client.get(f"/projects/{pid}/warnings")
    assert r.status_code == 200
    assert r.json()["warnings"] == []


def test_goal_with_project_creates_warnings(client, pid):
    r = client.post(
        "/goal",
        json={"text": "knockout gene recA in E. coli", "project_id": pid},
    )
    assert r.status_code == 200
    warning_ids = r.json()["warning_ids"]
    assert len(warning_ids) >= 1

    r2 = client.get(f"/projects/{pid}/warnings")
    assert r2.status_code == 200
    warnings = r2.json()["warnings"]
    assert len(warnings) >= 1
    types = [w["type"] for w in warnings]
    assert "essential_gene_risk" in types


def test_goal_without_project_creates_no_warnings(client, pid):
    r = client.post("/goal", json={"text": "knockout gene recA in E. coli"})
    assert r.status_code == 200
    assert r.json()["warning_ids"] == []


def test_simulate_frameshift_creates_warning(client, pid):
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
            "project_id": pid,
        },
    )
    assert r.status_code == 200
    warning_ids = r.json()["warning_ids"]
    assert len(warning_ids) >= 1

    r2 = client.get(f"/projects/{pid}/warnings")
    types = [w["type"] for w in r2.json()["warnings"]]
    assert "frameshift" in types


def test_simulate_silent_no_warning(client, pid):
    seq = "ATG" + "GCT" * 20 + "TAA"
    r = client.post(
        "/simulate/edit",
        json={
            "sequence": seq,
            "gene_name": "g",
            "kind": "substitution",
            "position": 5,
            "ref": "T",
            "alt": "C",
            "project_id": pid,
        },
    )
    assert r.status_code == 200
    assert r.json()["warning_ids"] == []


def test_acknowledge_warning(client, pid):
    r = client.post(
        "/goal",
        json={"text": "knockout gene recA in E. coli", "project_id": pid},
    )
    wid = r.json()["warning_ids"][0]

    r2 = client.post(
        f"/warnings/{wid}/acknowledge",
        json={"by": "testuser", "note": "I understand the risk"},
    )
    assert r2.status_code == 200
    w = r2.json()["warning"]
    assert w["status"] == "acknowledged"
    assert w["acknowledged_by"] == "testuser"
    assert w["acknowledgment_note"] == "I understand the risk"


def test_acknowledge_twice_fails(client, pid):
    r = client.post(
        "/goal",
        json={"text": "knockout gene recA in E. coli", "project_id": pid},
    )
    wid = r.json()["warning_ids"][0]
    client.post(
        f"/warnings/{wid}/acknowledge",
        json={"by": "u", "note": "first"},
    )
    r2 = client.post(
        f"/warnings/{wid}/acknowledge",
        json={"by": "u", "note": "second"},
    )
    assert r2.status_code == 422


def test_acknowledge_empty_note_fails(client, pid):
    r = client.post(
        "/goal",
        json={"text": "knockout gene recA in E. coli", "project_id": pid},
    )
    wid = r.json()["warning_ids"][0]
    r2 = client.post(
        f"/warnings/{wid}/acknowledge",
        json={"by": "u", "note": "   "},
    )
    assert r2.status_code == 422


def test_filter_by_status(client, pid):
    r = client.post(
        "/goal",
        json={"text": "knockout gene recA in E. coli", "project_id": pid},
    )
    wid = r.json()["warning_ids"][0]

    r_open = client.get(f"/projects/{pid}/warnings?status=open")
    assert any(w["id"] == wid for w in r_open.json()["warnings"])

    client.post(
        f"/warnings/{wid}/acknowledge",
        json={"by": "u", "note": "ok"},
    )
    r_open2 = client.get(f"/projects/{pid}/warnings?status=open")
    assert not any(w["id"] == wid for w in r_open2.json()["warnings"])

    r_ack = client.get(f"/projects/{pid}/warnings?status=acknowledged")
    assert any(w["id"] == wid for w in r_ack.json()["warnings"])


def test_warning_for_missing_project_404(client):
    r = client.get("/projects/99999/warnings")
    assert r.status_code == 404