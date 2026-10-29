"""Tests for related history endpoint."""

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


def _create_plan(client, project_id, gene, organism, intent):
    client.post(
        f"/projects/{project_id}/experiments",
        json={
            "kind": "plan",
            "title": intent + " " + gene + " in " + organism,
            "payload": {
                "goal": {
                    "intent": intent,
                    "target": {"gene": gene, "organism": organism},
                },
                "intervention": {
                    "kind": intent,
                    "predicted_effect": 0.85,
                    "off_target_risk": 0.2,
                    "essentiality_risk": 0.1,
                },
                "steps": [],
                "notes": [],
            },
        },
    )


def test_related_empty_when_no_match(client):
    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=knockout")
    assert r.status_code == 200
    assert r.json()["related"] == []


def test_related_finds_exact_match(client):
    pid = client.post("/projects", json={"name": "P1"}).json()["project"]["id"]
    _create_plan(client, pid, "lacZ", "Escherichia coli", "knockout")

    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=knockout")
    assert r.status_code == 200
    body = r.json()
    assert len(body["related"]) == 1
    m = body["related"][0]
    assert m["project_id"] == pid
    assert m["project_name"] == "P1"
    assert m["intervention_kind"] == "knockout"


def test_related_ignores_different_gene(client):
    pid = client.post("/projects", json={"name": "P1"}).json()["project"]["id"]
    _create_plan(client, pid, "recA", "Escherichia coli", "knockout")

    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=knockout")
    assert r.json()["related"] == []


def test_related_ignores_different_intent(client):
    pid = client.post("/projects", json={"name": "P1"}).json()["project"]["id"]
    _create_plan(client, pid, "lacZ", "Escherichia coli", "knockout")

    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=increase_expression")
    assert r.json()["related"] == []


def test_related_returns_multiple(client):
    p1 = client.post("/projects", json={"name": "P1"}).json()["project"]["id"]
    p2 = client.post("/projects", json={"name": "P2"}).json()["project"]["id"]
    _create_plan(client, p1, "lacZ", "Escherichia coli", "knockout")
    _create_plan(client, p2, "lacZ", "Escherichia coli", "knockout")

    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=knockout")
    assert len(r.json()["related"]) == 2


def test_related_limit(client):
    pid = client.post("/projects", json={"name": "P1"}).json()["project"]["id"]
    for _ in range(5):
        _create_plan(client, pid, "lacZ", "Escherichia coli", "knockout")

    r = client.get("/related?gene=lacZ&organism=Escherichia+coli&intent=knockout&limit=2")
    assert len(r.json()["related"]) == 2
