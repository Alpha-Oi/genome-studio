"""Tests for DELETE /experiments/{id}."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.app import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_delete_experiment(client):
    pid = client.post("/projects", json={"name": "P"}).json()["project"]["id"]
    e = client.post(
        f"/projects/{pid}/experiments",
        json={"kind": "plan", "title": "x", "payload": {"a": 1}},
    ).json()["experiment"]
    eid = e["id"]

    r = client.delete(f"/experiments/{eid}")
    assert r.status_code == 200
    assert r.json()["id"] == eid

    listing = client.get(f"/projects/{pid}/experiments").json()["experiments"]
    assert all(x["id"] != eid for x in listing)


def test_delete_missing_experiment(client):
    r = client.delete("/experiments/99999")
    assert r.status_code == 404
