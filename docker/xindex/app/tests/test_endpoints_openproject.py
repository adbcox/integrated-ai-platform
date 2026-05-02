"""OpenProject endpoint tests + ADR workpackage_tracking (D-17-04 WP-17-04-05.5).

Replaces test_endpoints_plane.py.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import db as _db
from app.ingest import openproject as _op


def _good_op_fetcher():
    """Return versions+statuses+workpackages covering ADR + deliverable + non-link."""
    def fetch(creds):
        versions = [
            {"name": "Phase-17", "id": 16, "external_id": "Phase-17",
             "description": ""},
        ]
        statuses = [
            {"name": "New", "id": 1, "is_closed": False},
            {"name": "In progress", "id": 7, "is_closed": False},
        ]
        wps = [
            {"external_id": "ADR-A-001", "name": "[ADR-A-001] sample",
             "id": 501, "state": 7, "version_id": 16,
             "description_html": "", "description_raw": "",
             "updated_at": "2026-05-02T12:00:00Z", "project_id": 1},
            {"external_id": "D-17-04",
             "name": "[D-17-04] Replace Plane CE with OpenProject",
             "id": 502, "state": 1, "version_id": 16,
             "description_html": "", "description_raw": "",
             "updated_at": "2026-05-02T12:00:00Z", "project_id": 1},
        ]
        return versions, statuses, wps
    return fetch


@pytest.fixture()
def client(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("XINDEX_DOCS_ROOT", str(fixture_docs))
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "op-fake-token")
    monkeypatch.setenv("OPENPROJECT_URL", "http://openproject.example")
    monkeypatch.setenv("OPENPROJECT_PROJECT", "roadmap")
    monkeypatch.setattr(
        _op, "CREDENTIALS_PATH", _op.Path("/nonexistent/openproject.env")
    )

    from app import main as main_mod
    importlib.reload(main_mod)

    with _db.connect(db_path) as conn:
        from app import ingest as _ingest
        _ingest.ingest_all(
            conn, str(fixture_docs), openproject_fetcher=_good_op_fetcher()
        )

    with TestClient(main_mod.app) as c:
        yield c


def test_healthz_includes_openproject_source(client: TestClient) -> None:
    r = client.get("/healthz")
    body = r.json()
    by_src = {s["source"]: s for s in body["sources"]}
    assert "openproject" in by_src
    assert by_src["openproject"]["status"] == "ok"
    # netbox skipped (no token in this test) → status='unknown' or 'error'
    assert "netbox" in by_src
    assert body["counts"]["op_workpackages"] == 2
    assert body["counts"]["op_versions"] == 1


def test_get_workpackage(client: TestClient) -> None:
    r = client.get("/workpackage/D-17-04")
    assert r.status_code == 200
    body = r.json()
    assert body["external_id"] == "D-17-04"
    assert body["status_name"] == "New"
    assert body["version_name"] == "Phase-17"
    # Inbound tracked_in link from deliverable
    inbound = [l for l in body["links"] if l["from_kind"] == "deliverable"]
    assert len(inbound) == 1
    assert inbound[0]["link_type"] == "tracked_in"


def test_get_workpackage_404(client: TestClient) -> None:
    r = client.get("/workpackage/NOPE-123")
    assert r.status_code == 404


def test_get_version(client: TestClient) -> None:
    r = client.get("/version/Phase-17")
    assert r.status_code == 200
    body = r.json()
    assert body["external_id"] == "Phase-17"
    assert {wp["external_id"] for wp in body["workpackages"]} == {
        "ADR-A-001", "D-17-04",
    }


def test_adr_detail_includes_workpackage_tracking(client: TestClient) -> None:
    r = client.get("/adr/A-001")
    assert r.status_code == 200
    body = r.json()
    assert body["workpackage_tracking"] is not None
    assert body["workpackage_tracking"]["external_id"] == "ADR-A-001"
    assert body["workpackage_tracking"]["status_name"] == "In progress"


def test_adr_detail_workpackage_tracking_null_when_unmapped(client: TestClient) -> None:
    # ADR-A-007 is in the fixture but has no OpenProject WP
    r = client.get("/adr/A-007")
    assert r.status_code == 200
    body = r.json()
    assert body["workpackage_tracking"] is None


def test_search_type_workpackage(client: TestClient) -> None:
    r = client.get("/search", params={"q": "OpenProject", "type": "workpackage"})
    body = r.json()
    assert body["count"] >= 1
    assert all(h["kind"] == "workpackage" for h in body["results"])
