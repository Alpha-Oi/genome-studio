"""Tests for PDF report generation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from genome_studio.api.app import create_app
from genome_studio.report import build_project_pdf


def _make_project() -> dict:
    return {
        "id": 1,
        "name": "Test project",
        "description": "Test description",
        "organism": "E. coli",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }


# --- Direct PDF build ---------------------------------------------------

def test_build_pdf_empty():
    pdf = build_project_pdf(
        project=_make_project(),
        experiments=[],
        warnings=[],
    )
    assert isinstance(pdf, bytes)
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 500


def test_build_pdf_with_plan():
    exp = {
        "id": 1,
        "project_id": 1,
        "kind": "plan",
        "title": "knockout lacZ in E. coli",
        "payload": {
            "goal": {
                "intent": "knockout",
                "target": {"gene": "lacZ", "organism": "Escherichia coli"},
            },
            "intervention": {
                "kind": "knockout",
                "rationale": "Direct knockout",
                "predicted_effect": 0.85,
                "off_target_risk": 0.2,
                "essentiality_risk": 0.1,
                "complexity": 2,
            },
            "steps": [
                {"order": 1, "action": "design_grna", "description": "Design gRNA"},
                {"order": 2, "action": "transfect", "description": "Transfect cells"},
            ],
            "notes": [],
        },
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    pdf = build_project_pdf(
        project=_make_project(),
        experiments=[exp],
        warnings=[],
    )
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000


def test_build_pdf_with_warnings():
    warning = {
        "id": 1,
        "project_id": 1,
        "experiment_id": None,
        "level": "T0_science",
        "severity": "high",
        "type": "essential_gene_risk",
        "message": "Essential gene recA may be lethal.",
        "evidence": ["standard CRISPR-Cas9 knockout"],
        "status": "open",
        "acknowledged_by": None,
        "acknowledged_at": None,
        "acknowledgment_note": "",
        "created_at": "2026-01-01T00:00:00+00:00",
    }
    pdf = build_project_pdf(
        project=_make_project(),
        experiments=[],
        warnings=[warning],
    )
    assert pdf.startswith(b"%PDF")


# --- API ----------------------------------------------------------------

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


def test_report_endpoint_empty_project(client):
    pid = client.post("/projects", json={"name": "RTest"}).json()["project"]["id"]
    r = client.get(f"/projects/{pid}/report.pdf")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "attachment" in r.headers["content-disposition"]
    assert r.content.startswith(b"%PDF")


def test_report_endpoint_with_experiment(client):
    pid = client.post("/projects", json={"name": "RTest"}).json()["project"]["id"]
    client.post(
        f"/projects/{pid}/experiments",
        json={
            "kind": "plan",
            "title": "test",
            "payload": {
                "goal": {
                    "intent": "knockout",
                    "target": {"gene": "lacZ", "organism": "E. coli"},
                },
                "intervention": {"kind": "knockout", "complexity": 2},
                "steps": [],
                "notes": [],
            },
        },
    )
    r = client.get(f"/projects/{pid}/report.pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")
    assert len(r.content) > 1000


def test_report_endpoint_missing_project(client):
    r = client.get("/projects/99999/report.pdf")
    assert r.status_code == 404