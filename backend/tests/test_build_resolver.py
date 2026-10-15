"""Tests for build_resolver."""

from __future__ import annotations

import os
from unittest.mock import patch

from genome_studio.build_resolver import BuildMode, resolve_build


def test_prod_by_default(monkeypatch):
    """Без GS_DEV_OVERRIDE_AVAILABLE всегда prod."""
    monkeypatch.delenv("GS_DEV_OVERRIDE_AVAILABLE", raising=False)
    monkeypatch.delenv("GS_BUILD", raising=False)

    info = resolve_build()
    assert info.mode == BuildMode.PROD
    assert info.dev_override_available is False


def test_dev_requires_signing_key(monkeypatch, tmp_path):
    """Dev не активируется без ключа."""
    monkeypatch.setenv("GS_DEV_OVERRIDE_AVAILABLE", "1")
    monkeypatch.setenv("GS_BUILD", "dev")
    monkeypatch.setenv("HOME", str(tmp_path))

    info = resolve_build()
    assert info.mode == BuildMode.PROD
    assert "no signing key" in " ".join(info.reasons)


def test_dev_requires_isolation(monkeypatch, tmp_path):
    """Dev не активируется с внешней сетью."""
    monkeypatch.setenv("GS_DEV_OVERRIDE_AVAILABLE", "1")
    monkeypatch.setenv("GS_BUILD", "dev")
    monkeypatch.setenv("HOME", str(tmp_path))

    key = tmp_path / ".gs" / "keys" / "dev-signing.key"
    key.parent.mkdir(parents=True)
    key.write_text("dummy")

    with patch("genome_studio.build_resolver._is_isolated", return_value=False):
        info = resolve_build()
        assert info.mode == BuildMode.PROD
        assert "external network" in " ".join(info.reasons)


def test_dev_activated_when_all_conditions_met(monkeypatch, tmp_path):
    """Dev активируется при всех условиях."""
    monkeypatch.setenv("GS_DEV_OVERRIDE_AVAILABLE", "1")
    monkeypatch.setenv("GS_BUILD", "dev")
    monkeypatch.setenv("HOME", str(tmp_path))

    key = tmp_path / ".gs" / "keys" / "dev-signing.key"
    key.parent.mkdir(parents=True)
    key.write_text("dummy")

    with patch("genome_studio.build_resolver._is_isolated", return_value=True):
        info = resolve_build()
        assert info.mode == BuildMode.DEV
        assert info.dev_override_available is True
        assert info.signing_key_present is True
        assert info.isolated_environment is True
