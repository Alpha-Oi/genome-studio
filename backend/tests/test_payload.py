"""Tests for payload validation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.data.payload import (
    MAX_PAYLOAD_DEPTH,
    MAX_PAYLOAD_SIZE,
    PayloadNotJsonError,
    PayloadTooDeepError,
    PayloadTooLargeError,
    validate_payload,
)


def test_valid_small_payload():
    p = {"a": 1, "b": "test", "c": [1, 2, 3]}
    assert validate_payload(p) == p


def test_valid_empty():
    assert validate_payload({}) == {}


def test_too_large_rejected():
    p = {"data": "x" * (MAX_PAYLOAD_SIZE + 100)}
    with pytest.raises(PayloadTooLargeError):
        validate_payload(p)


def test_too_deep_rejected():
    p: dict = {}
    current = p
    for _ in range(MAX_PAYLOAD_DEPTH + 5):
        current["next"] = {}
        current = current["next"]
    with pytest.raises(PayloadTooDeepError):
        validate_payload(p)


def test_null_byte_rejected():
    with pytest.raises(PayloadNotJsonError):
        validate_payload({"data": "a\x00b"})


def test_non_json_rejected():
    with pytest.raises(PayloadNotJsonError):
        validate_payload({"data": {1, 2, 3}})


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    from genome_studio.api.app import create_app

    app = create_app()
    with TestClient(app) as c:
        yield c


def test_api_rejects_too_large(client):
    r = client.post("/projects", json={"name": "test"})
    pid = r.json()["project"]["id"]
    p = {"data": "x" * (MAX_PAYLOAD_SIZE + 100)}
    r = client.post(
        f"/projects/{pid}/experiments",
        json={"kind": "x", "title": "y", "payload": p},
    )
    assert r.status_code == 422


def test_api_rejects_too_deep(client):
    r = client.post("/projects", json={"name": "test"})
    pid = r.json()["project"]["id"]
    p: dict = {}
    current = p
    for _ in range(MAX_PAYLOAD_DEPTH + 5):
        current["next"] = {}
        current = current["next"]
    r = client.post(
        f"/projects/{pid}/experiments",
        json={"kind": "x", "title": "y", "payload": p},
    )
    assert r.status_code == 422


def test_api_accepts_valid(client):
    r = client.post("/projects", json={"name": "test"})
    pid = r.json()["project"]["id"]
    r = client.post(
        f"/projects/{pid}/experiments",
        json={"kind": "x", "title": "y", "payload": {"a": 1, "b": [1, 2]}},
    )
    assert r.status_code == 200
