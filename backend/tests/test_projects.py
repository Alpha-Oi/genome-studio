"""Tests for projects / experiments persistence."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from genome_studio.api.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    # reset global singletons so each test uses its own DB
    from genome_studio.data import db as _db

    _db._engine = None
    _db._session_factory = None
    app = create_app()
    with TestClient(app) as c:
        yield c
    _db._engine = None
    _db._session_factory = None


def test_projects_empty(client):
    r = client.get("/projects")
    assert r.status_code == 200
    assert r.json()["projects"] == []


def test_create_project(client):
    r = client.post(
        "/projects",
        json={"name": "Test project", "description": "hello", "organism": "E. coli"},
    )
    assert r.status_code == 200
    body = r.json()["project"]
    assert body["id"] > 0
    assert body["name"] == "Test project"
    assert body["organism"] == "E. coli"


def test_list_projects(client):
    client.post("/projects", json={"name": "A"})
    client.post("/projects", json={"name": "B"})
    r = client.get("/projects")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["projects"]]
    assert set(names) == {"A", "B"}


def test_get_project(client):
    created = client.post("/projects", json={"name": "X"}).json()["project"]
    pid = created["id"]
    r = client.get(f"/projects/{pid}")
    assert r.status_code == 200
    body = r.json()["project"]
    assert body["name"] == "X"
    assert body["experiments"] == []


def test_get_project_404(client):
    r = client.get("/projects/99999")
    assert r.status_code == 404


def test_delete_project(client):
    created = client.post("/projects", json={"name": "ToDelete"}).json()["project"]
    pid = created["id"]
    r = client.delete(f"/projects/{pid}")
    assert r.status_code == 200
    r2 = client.get(f"/projects/{pid}")
    assert r2.status_code == 404


def test_create_experiment(client):
    pid = client.post("/projects", json={"name": "P"}).json()["project"]["id"]
    r = client.post(
        f"/projects/{pid}/experiments",
        json={
            "kind": "plan",
            "title": "knockout lacZ",
            "payload": {"goal": {"intent": "knockout"}},
        },
    )
    assert r.status_code == 200
    e = r.json()["experiment"]
    assert e["id"] > 0
    assert e["kind"] == "plan"
    assert e["payload"]["goal"]["intent"] == "knockout"


def test_list_experiments(client):
    pid = client.post("/projects", json={"name": "P"}).json()["project"]["id"]
    client.post(f"/projects/{pid}/experiments", json={"kind": "plan", "title": "1"})
    client.post(f"/projects/{pid}/experiments", json={"kind": "crispr", "title": "2"})
    r = client.get(f"/projects/{pid}/experiments")
    assert r.status_code == 200
    kinds = [e["kind"] for e in r.json()["experiments"]]
    assert set(kinds) == {"plan", "crispr"}


def test_experiment_on_missing_project(client):
    r = client.post(
        "/projects/99999/experiments",
        json={"kind": "plan", "title": "x"},
    )
    assert r.status_code == 404


def test_delete_project_cascades_experiments(client):
    pid = client.post("/projects", json={"name": "P"}).json()["project"]["id"]
    client.post(f"/projects/{pid}/experiments", json={"kind": "plan", "title": "x"})
    client.delete(f"/projects/{pid}")
    r = client.get(f"/projects/{pid}/experiments")
    assert r.status_code == 404
