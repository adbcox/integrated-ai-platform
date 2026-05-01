"""Tests for the Plane ingester (D-16-02.2).

The Plane HTTP client is replaced via the `fetcher` injection on
`ingest.plane.ingest`. No real Plane API calls.
"""
from __future__ import annotations

import pytest

from app import db as _db
from app.ingest import plane as _pl


PROJ = "00000000-0000-0000-0000-000000000abc"


def _module(name, mid, ext=None, description=""):
    return {
        "name": name,
        "id": mid,
        "external_id": ext,
        "description": description,
    }


def _state(name, sid):
    return {"name": name, "id": sid}


def _issue(*, ext, name, plane_id, state, module_ids=None,
           description="", updated_at="2026-05-01T12:00:00Z"):
    return {
        "external_id": ext,
        "name": name,
        "id": plane_id,
        "state": state,
        "module_ids": list(module_ids or []),
        "description_html": description,
        "updated_at": updated_at,
        "project": PROJ,
    }


def _fetcher(modules, states, issues):
    def fetch(creds):
        assert creds["token"] == "plane-fake-token"
        return list(modules), list(states), list(issues)
    return fetch


def _full_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PLANE_API_TOKEN", "plane-fake-token")
    monkeypatch.setenv("PLANE_URL", "http://plane.example")
    monkeypatch.setenv("PLANE_WORKSPACE", "iap")
    monkeypatch.setenv("PLANE_PROJECT_ID", PROJ)
    monkeypatch.setattr(
        _pl, "CREDENTIALS_PATH", _pl.Path("/nonexistent/plane.env")
    )


@pytest.fixture()
def conn(db_path: str, monkeypatch: pytest.MonkeyPatch):
    _full_creds(monkeypatch)
    with _db.connect(db_path) as c:
        _db.init_schema(c)
        yield c


def test_ingest_writes_modules_and_issues(conn) -> None:
    mod = _module("Phase 16", "mod-16", ext="Phase-16")
    states = [_state("Backlog", "st-bl"), _state("Done", "st-dn")]
    issues = [
        _issue(
            ext="D-16-02.2",
            name="[D-16-02.2] Plane source ingestion",
            plane_id="iss-1",
            state="st-bl",
            module_ids=["mod-16"],
            description="<p>plane source</p>",
        ),
        _issue(
            ext="ADR-A-006",
            name="[ADR-A-006] one-way sync",
            plane_id="iss-2",
            state="st-dn",
            module_ids=["mod-16"],
        ),
    ]
    _db.reset_source(conn, "plane")
    res = _pl.ingest(conn, fetcher=_fetcher([mod], states, issues))
    assert res.ok
    assert res.plane_modules == 1
    assert res.plane_issues == 2
    # tracked_in for both: 1 ADR + 1 deliverable
    assert res.entity_links == 2

    counts = _db.counts(conn)
    assert counts["plane_modules"] == 1
    assert counts["plane_issues"] == 2

    # state and module names denormalized into rows
    row = conn.execute(
        "SELECT state_name, module_name FROM plane_issues WHERE external_id='D-16-02.2'"
    ).fetchone()
    assert row["state_name"] == "Backlog"
    assert row["module_name"] == "Phase 16"


def test_ingest_skips_issues_without_external_id(conn) -> None:
    states = [_state("Backlog", "st-bl")]
    issues = [
        _issue(ext="", name="legacy issue without external_id",
               plane_id="iss-x", state="st-bl"),
        _issue(ext="D-15-99", name="legit",
               plane_id="iss-y", state="st-bl"),
    ]
    _db.reset_source(conn, "plane")
    res = _pl.ingest(conn, fetcher=_fetcher([], states, issues))
    assert res.ok
    assert res.plane_issues == 1
    assert res.entity_links == 1


def test_ingest_unknown_external_id_prefix_no_link(conn) -> None:
    """Issues with non-matching prefix still ingest, but emit no link."""
    states = [_state("Backlog", "st-bl")]
    issues = [
        _issue(ext="MISC-42", name="random tracking",
               plane_id="iss-q", state="st-bl"),
    ]
    _db.reset_source(conn, "plane")
    res = _pl.ingest(conn, fetcher=_fetcher([], states, issues))
    assert res.ok
    assert res.plane_issues == 1
    assert res.entity_links == 0


def test_ingest_skipped_when_no_creds(conn, monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("PLANE_API_TOKEN", "PLANE_URL", "PLANE_WORKSPACE", "PLANE_PROJECT_ID"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(
        _pl, "CREDENTIALS_PATH", _pl.Path("/nonexistent/plane.env")
    )
    res = _pl.ingest(conn, fetcher=_fetcher([], [], []))
    assert not res.ok
    assert res.skipped is True
    assert "Plane credentials" in res.skip_reason


def test_rate_limit_error_surfaces_as_error(conn) -> None:
    def raiser(creds):
        raise _pl._RateLimitError("429 on /issues/")
    res = _pl.ingest(conn, fetcher=raiser)
    assert not res.ok
    assert res.skipped is False
    assert "rate-limited" in res.error


def test_fetch_returns_none_marks_error(conn) -> None:
    res = _pl.ingest(conn, fetcher=lambda creds: None)
    assert not res.ok
    assert res.skipped is False
    assert "unreachable" in res.error or "auth" in res.error


def test_plane_issue_searchable_via_fts(conn) -> None:
    states = [_state("Backlog", "st-bl")]
    issues = [
        _issue(
            ext="D-16-02.2",
            name="Plane source ingestion",
            plane_id="iss-1",
            state="st-bl",
            description="extends xindex with read-only Plane mirror",
        ),
    ]
    _db.reset_source(conn, "plane")
    _pl.ingest(conn, fetcher=_fetcher([], states, issues))
    rows = conn.execute(
        "SELECT kind, ref FROM xindex_fts WHERE xindex_fts MATCH 'Plane'"
    ).fetchall()
    kinds = {r["kind"] for r in rows}
    assert "plane_issue" in kinds
