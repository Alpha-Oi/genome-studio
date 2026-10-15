"""Tests for /mode endpoint and AppMode resolve."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.app import create_app
from genome_studio.auth import AppMode, LOCAL_USER, User, resolve_mode
from genome_studio.auth.dependencies import get_current_user


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


# --- resolve_mode -------------------------------------------------------

def test_default_mode_is_local(monkeypatch):
    monkeypatch.delenv("GS_MODE", raising=False)
    assert resolve_mode() == AppMode.LOCAL


def test_resolve_mode_reads_env(monkeypatch):
    monkeypatch.setenv("GS_MODE", "multi")
    assert resolve_mode() == AppMode.MULTI


def test_resolve_mode_bad_value_falls_back_to_local(monkeypatch):
    monkeypatch.setenv("GS_MODE", "weird")
    assert resolve_mode() == AppMode.LOCAL


# --- User / LOCAL_USER --------------------------------------------------

def test_local_user_is_local():
    assert LOCAL_USER.is_local
    assert LOCAL_USER.id == 0
    assert LOCAL_USER.is_admin


def test_user_from_id_is_not_local():
    u = User(id=42, email="a@b.c", name="Alice")
    assert not u.is_local


# --- get_current_user ---------------------------------------------------

@pytest.mark.asyncio
async def test_get_current_user_returns_local(monkeypatch):
    monkeypatch.setenv("GS_MODE", "local")
    user = await get_current_user()
    assert user == LOCAL_USER


# --- API ----------------------------------------------------------------

def test_mode_endpoint_local(client):
    r = client.get("/mode")
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "local"
    assert body["user"]["id"] == 0
    assert body["user"]["is_local"] is True
    assert body["user"]["is_admin"] is True
    assert "local" in body["available_modes"]
    assert "multi" in body["available_modes"]
    assert body["switchable"] is False