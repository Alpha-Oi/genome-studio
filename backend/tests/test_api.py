"""Tests for FastAPI endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from genome_studio.api.app import create_app


def test_health():
    app = create_app()
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_build_info():
    app = create_app()
    client = TestClient(app)
    r = client.get("/build")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "prod"
    assert body["dev_override_available"] is False


def test_goal_endpoint():
    app = create_app()
    client = TestClient(app)
    r = client.post("/goal", json={"text": "knockout gene lacZ in E. coli"})
    assert r.status_code == 200
    body = r.json()
    assert body["plan"]["intervention"]["kind"] == "knockout"
    assert body["plan"]["goal"]["target"]["gene"] == "lacZ"
    assert len(body["plan"]["steps"]) >= 4


def test_goal_endpoint_bad_input():
    app = create_app()
    client = TestClient(app)
    r = client.post("/goal", json={"text": "hello world"})
    assert r.status_code == 422


def test_goal_endpoint_increase():
    app = create_app()
    client = TestClient(app)
    r = client.post("/goal", json={"text": "increase expression of gene lacZ in E. coli"})
    assert r.status_code == 200
    body = r.json()
    assert body["plan"]["intervention"]["kind"] == "promoter_swap"