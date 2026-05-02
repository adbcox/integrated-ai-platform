"""Tests for the OpenProject ingester (D-17-04 WP-17-04-05.5).

The OpenProject HTTP client is replaced via the `fetcher` injection on
`ingest.openproject.ingest`. No real OpenProject API calls.

Replaces test_ingest_plane.py (Plane CE retired in D-17-04 WP-17-04-06).
"""
from __future__ import annotations

import pytest

from app import db as _db
from app.ingest import openproject as _op


def _version(name, vid, ext=None, description=""):
    return {
        "name": name,
        "id": vid,
        "external_id": ext or name,
        "description": description,
    }


def _status(name, sid, is_closed=False):
    return {"name": name, "id": sid, "is_closed": is_closed}


def _wp(*, ext, name, op_id, status, version_id=None,
        description="", updated_at="2026-05-02T12:00:00Z"):
    return {
        "external_id": ext,
        "name": name,
        "id": op_id,
        "state": status,
        "version_id": version_id,
        "description_html": "",
        "description_raw": description,
        "updated_at": updated_at,
        "project_id": 1,
    }


def _fetcher(versions, statuses, workpackages):
    def fetch(creds):
        assert creds["token"] == "op-fake-token"
        return list(versions), list(statuses), list(workpackages)
    return fetch


def _full_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "op-fake-token")
    monkeypatch.setenv("OPENPROJECT_URL", "http://openproject.example")
    monkeypatch.setenv("OPENPROJECT_PROJECT", "roadmap")
    monkeypatch.setattr(
        _op, "CREDENTIALS_PATH", _op.Path("/nonexistent/openproject.env")
    )


@pytest.fixture()
def conn(db_path: str, monkeypatch: pytest.MonkeyPatch):
    _full_creds(monkeypatch)
    with _db.connect(db_path) as c:
        _db.init_schema(c)
        yield c


def test_ingest_writes_versions_and_workpackages(conn) -> None:
    ver = _version("Phase-17", 16, ext="Phase-17")
    statuses = [_status("New", 1), _status("Closed", 12, is_closed=True)]
    wps = [
        _wp(
            ext="D-17-04",
            name="[D-17-04] Replace Plane CE with OpenProject",
            op_id=101,
            status=1,
            version_id=16,
            description="op source",
        ),
        _wp(
            ext="ADR-A-006",
            name="[ADR-A-006] one-way sync",
            op_id=102,
            status=12,
            version_id=16,
        ),
    ]
    _db.reset_source(conn, "openproject")
    res = _op.ingest(conn, fetcher=_fetcher([ver], statuses, wps))
    assert res.ok
    assert res.op_versions == 1
    assert res.op_workpackages == 2
    # tracked_in for both: 1 ADR + 1 deliverable
    assert res.entity_links == 2

    counts = _db.counts(conn)
    assert counts["op_versions"] == 1
    assert counts["op_workpackages"] == 2

    # status and version names denormalized into rows
    row = conn.execute(
        "SELECT status_name, version_name FROM op_workpackages WHERE external_id='D-17-04'"
    ).fetchone()
    assert row["status_name"] == "New"
    assert row["version_name"] == "Phase-17"


def test_ingest_skips_workpackages_without_external_id(conn) -> None:
    statuses = [_status("New", 1)]
    wps = [
        _wp(ext="", name="legacy WP without external_id",
            op_id=200, status=1),
        _wp(ext="D-15-99", name="legit", op_id=201, status=1),
    ]
    _db.reset_source(conn, "openproject")
    res = _op.ingest(conn, fetcher=_fetcher([], statuses, wps))
    assert res.ok
    assert res.op_workpackages == 1
    assert res.entity_links == 1


def test_ingest_unknown_external_id_prefix_no_link(conn) -> None:
    """WPs with non-matching prefix still ingest, but emit no link."""
    statuses = [_status("New", 1)]
    wps = [
        _wp(ext="MISC-42", name="random tracking", op_id=300, status=1),
    ]
    _db.reset_source(conn, "openproject")
    res = _op.ingest(conn, fetcher=_fetcher([], statuses, wps))
    assert res.ok
    assert res.op_workpackages == 1
    assert res.entity_links == 0


def test_ingest_skipped_when_no_creds(conn, monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("OPENPROJECT_API_TOKEN", "OPENPROJECT_URL", "OPENPROJECT_PROJECT"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        _op, "CREDENTIALS_PATH", _op.Path("/nonexistent/openproject.env")
    )
    res = _op.ingest(conn, fetcher=_fetcher([], [], []))
    assert not res.ok
    assert res.skipped is True
    assert "OpenProject credentials" in res.skip_reason


def test_fetch_returns_none_marks_error(conn) -> None:
    res = _op.ingest(conn, fetcher=lambda creds: None)
    assert not res.ok
    assert res.skipped is False
    assert "unreachable" in res.error or "auth" in res.error


def test_workpackage_searchable_via_fts(conn) -> None:
    statuses = [_status("New", 1)]
    wps = [
        _wp(
            ext="D-17-04",
            name="OpenProject substrate flip",
            op_id=400,
            status=1,
            description="extends xindex with read-only OpenProject mirror",
        ),
    ]
    _db.reset_source(conn, "openproject")
    _op.ingest(conn, fetcher=_fetcher([], statuses, wps))
    rows = conn.execute(
        "SELECT kind, ref FROM xindex_fts WHERE xindex_fts MATCH 'OpenProject'"
    ).fetchall()
    kinds = {r["kind"] for r in rows}
    assert "workpackage" in kinds
