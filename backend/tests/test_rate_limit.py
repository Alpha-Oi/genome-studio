"""Tests for rate limiting."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.rate_limit import limiter


@pytest.fixture
def client_with_limit(tmp_path, monkeypatch):
    """Client with rate limiter forcibly enabled (default is off in local mode)."""
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    from genome_studio.api.app import create_app

    limiter.reset()
    limiter.enabled = True
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    limiter.enabled = False
    limiter.reset()


@pytest.fixture
def client_local(tmp_path, monkeypatch):
    """Client in local mode — limiter disabled."""
    monkeypatch.setenv("GS_DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("GS_SKIP_MIGRATIONS", "1")
    from genome_studio.api.app import create_app

    limiter.reset()
    limiter.enabled = False
    app = create_app()
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def test_batch_design_rate_limit(client_with_limit):
    """11th request to /batch/design should return 429 (limit 10/min)."""
    payload = {
        "sequences": [{"name": "x", "sequence": "ACGTACGTACGTACGTACGT" + "CGG"}],
        "top_n": 1,
        "min_score": 0.0,
    }
    for i in range(10):
        r = client_with_limit.post("/batch/design", json=payload)
        assert r.status_code == 200, f"hit {i}: {r.status_code} {r.text}"
    r = client_with_limit.post("/batch/design", json=payload)
    assert r.status_code == 429, f"expected 429, got {r.status_code} {r.text}"
    assert "Retry-After" in r.headers


def test_health_no_global_limit(client_with_limit):
    """/health has no per-endpoint limit and no global limit — 150 hits OK."""
    for i in range(150):
        r = client_with_limit.get("/health")
        assert r.status_code == 200, f"hit {i}: {r.status_code}"


def test_local_mode_no_rate_limit(client_local):
    """In local mode, limiter is disabled — no rate limits applied."""
    for i in range(150):
        r = client_local.post(
            "/batch/design",
            json={
                "sequences": [{"name": "x", "sequence": "ACGTACGTACGTACGTACGT" + "CGG"}],
                "top_n": 1,
                "min_score": 0.0,
            },
        )
        assert r.status_code == 200, f"hit {i}: {r.status_code}"
