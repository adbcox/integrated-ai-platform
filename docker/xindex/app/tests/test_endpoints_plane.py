"""Plane endpoint tests + ADR plane_tracking (D-16-02.2)."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db as _db
from app.ingest import plane as _pl


PROJ = "00000000-0000-0000-0000-000000000abc"


def _good_plane_fetcher():
    """Return modules+states+issues covering ADR + deliverable + phase + non-link."""
    def fetch(creds):
        modules = [
            {"name": "Phase-16", "id": "mod-16", "external_id": "Phase-16",
             "description": ""},
        ]
        states = [
            {"name": "Backlog", "id": "st-bl"},
            {"name": "In Progress", "id": "st-pr"},
        ]
        issues = [
            {"external_id": "ADR-A-001", "name": "[ADR-A-001] sample",
             "id": "iss-adr", "state": "st-pr",
             "module_ids": ["mod-16"], "description_html": "",
             "updated_at": "2026-05-01T12:00:00Z", "project": PROJ},
            {"external_id": "D-16-02.2", "name": "[D-16-02.2] Plane source ingestion",
             "id": "iss-d", "state": "st-bl",
             "module_ids": ["mod-16"], "description_html": "",
             "updated_at": "2026-05-01T12:00:00Z", "project": PROJ},
        ]
        return modules, states, issues
    return fetch


@pytest.fixture()
def client(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("XINDEX_DOCS_ROOT", str(fixture_docs))
    monkeypatch.setenv("PLANE_API_TOKEN", "plane-fake-token")
    monkeypatch.setenv("PLANE_URL", "http://plane.example")
    monkeypatch.setenv("PLANE_WORKSPACE", "iap")
    monkeypatch.setenv("PLANE_PROJECT_ID", PROJ)
    monkeypatch.setattr(
        _pl, "CREDENTIALS_PATH", _pl.Path("/nonexistent/plane.env")
    )

    from app import main as main_mod
    importlib.reload(main_mod)

    with _db.connect(db_path) as conn:
        from app import ingest as _ingest
        _ingest.ingest_all(
            conn, str(fixture_docs), plane_fetcher=_good_plane_fetcher()
        )

    with TestClient(main_mod.app) as c:
        yield c


def test_healthz_includes_plane_source(client: TestClient) -> None:
    r = client.get("/healthz")
    body = r.json()
    by_src = {s["source"]: s for s in body["sources"]}
    assert "plane" in by_src
    assert by_src["plane"]["status"] == "ok"
    # netbox skipped (no token in this test) → status='unknown' or 'error'
    assert "netbox" in by_src
    assert body["counts"]["plane_issues"] == 2
    assert body["counts"]["plane_modules"] == 1


def test_get_plane_issue(client: TestClient) -> None:
    r = client.get("/plane/D-16-02.2")
    assert r.status_code == 200
    body = r.json()
    assert body["external_id"] == "D-16-02.2"
    assert body["state_name"] == "Backlog"
    assert body["module_name"] == "Phase-16"
    # Inbound tracked_in link from deliverable
    inbound = [l for l in body["links"] if l["from_kind"] == "deliverable"]
    assert len(inbound) == 1
    assert inbound[0]["link_type"] == "tracked_in"


def test_get_plane_issue_404(client: TestClient) -> None:
    r = client.get("/plane/NOPE-123")
    assert r.status_code == 404


def test_get_plane_module(client: TestClient) -> None:
    r = client.get("/plane/module/Phase-16")
    assert r.status_code == 200
    body = r.json()
    assert body["external_id"] == "Phase-16"
    assert {i["external_id"] for i in body["issues"]} == {"ADR-A-001", "D-16-02.2"}


def test_adr_detail_includes_plane_tracking(client: TestClient) -> None:
    r = client.get("/adr/A-001")
    assert r.status_code == 200
    body = r.json()
    assert body["plane_tracking"] is not None
    assert body["plane_tracking"]["external_id"] == "ADR-A-001"
    assert body["plane_tracking"]["state_name"] == "In Progress"


def test_adr_detail_plane_tracking_null_when_unmapped(client: TestClient) -> None:
    # ADR-A-007 is in the fixture but has no Plane issue
    r = client.get("/adr/A-007")
    assert r.status_code == 200
    body = r.json()
    assert body["plane_tracking"] is None


def test_search_type_plane_issue(client: TestClient) -> None:
    r = client.get("/search", params={"q": "Plane", "type": "plane_issue"})
    body = r.json()
    assert body["count"] >= 1
    assert all(h["kind"] == "plane_issue" for h in body["results"])
