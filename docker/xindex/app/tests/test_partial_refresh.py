"""Partial-refresh doctrine tests (D-16-02.1, extended D-16-02.2).

Covers the core invariant: a failure in one external source on a
re-ingest must not wipe healthy rows from the previous run for that
source, and must not affect local sources or other external sources
at all. Both NetBox and Plane share this contract.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app import db as _db
from app import ingest as _ingest
from app.ingest import plane as _pl


PROJ = "00000000-0000-0000-0000-000000000abc"


def _dev(name):
    return SimpleNamespace(
        name=name, id=1,
        role=SimpleNamespace(name="server"),
        site=SimpleNamespace(name="lab"),
        status=SimpleNamespace(value="active"),
        primary_ip=None,
        description="",
        custom_fields={},
    )


def _svc(name, dev):
    return SimpleNamespace(
        name=name, id=2,
        protocol=SimpleNamespace(value="tcp"),
        ports=[80],
        device=dev,
        virtual_machine=None,
        description="",
        custom_fields={},
    )


def _good_fetcher():
    def fetch(token, url):
        d = _dev("mac-mini")
        return [d], [_svc("caddy", d)]
    return fetch


def _broken_fetcher_returns_none():
    return lambda token, url: None


def _good_plane_fetcher():
    def fetch(creds):
        modules = [{"name": "Phase 16", "id": "mod-16",
                    "external_id": "Phase-16", "description": ""}]
        states = [{"name": "Backlog", "id": "st-bl"}]
        issues = [{
            "external_id": "D-16-02.2",
            "name": "[D-16-02.2] Plane source ingestion",
            "id": "iss-1",
            "state": "st-bl",
            "module_ids": ["mod-16"],
            "description_html": "",
            "updated_at": "2026-05-01T12:00:00Z",
            "project": PROJ,
        }]
        return modules, states, issues
    return fetch


def _plane_429_fetcher():
    def fetch(creds):
        raise _pl._RateLimitError("429 on /issues/")
    return fetch


@pytest.fixture()
def env(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("NETBOX_API_TOKEN", "fake-token")
    monkeypatch.setenv("PLANE_API_TOKEN", "plane-fake-token")
    monkeypatch.setenv("PLANE_URL", "http://plane.example")
    monkeypatch.setenv("PLANE_WORKSPACE", "iap")
    monkeypatch.setenv("PLANE_PROJECT_ID", PROJ)
    monkeypatch.setattr(
        _pl, "CREDENTIALS_PATH", _pl.Path("/nonexistent/plane.env")
    )
    return fixture_docs, db_path


def test_first_run_populates_all_sources(env) -> None:
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            plane_fetcher=_good_plane_fetcher(),
        )
    assert summary["adrs"] == 2
    assert summary["nodes"] == 1
    assert summary["services"] == 1
    assert summary["plane_issues"] == 1
    assert summary["plane_modules"] == 1

    with _db.connect(db_path) as conn:
        st = _db.get_source_status(conn, "netbox")
        assert st["status"] == "ok"
        pst = _db.get_source_status(conn, "plane")
        assert pst["status"] == "ok"
        local = _db.get_source_status(conn, "adr")
        assert local["status"] == "ok"


def test_netbox_failure_preserves_prior_netbox_rows(env) -> None:
    """NetBox down on a re-run: prior services/nodes survive, status flips."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            plane_fetcher=_good_plane_fetcher(),
        )
        before = _db.counts(conn)

    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_broken_fetcher_returns_none(),
            plane_fetcher=_good_plane_fetcher(),
        )
        after = _db.counts(conn)
        st = _db.get_source_status(conn, "netbox")

    # local sources rebuilt fine
    assert summary["adrs"] == 2
    # external survival: NetBox rows kept
    assert after["services"] == before["services"] == 1
    assert after["nodes"] == before["nodes"] == 1
    # plane unaffected
    assert after["plane_issues"] == before["plane_issues"] == 1
    # but NetBox status reflects the failure
    assert st["status"] == "error"
    assert "unreachable" in st["error"] or "auth" in st["error"]


def test_netbox_failure_does_not_affect_local_sources(env) -> None:
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn,
            str(fixture_docs),
            netbox_fetcher=_broken_fetcher_returns_none(),
            plane_fetcher=_good_plane_fetcher(),
        )
    # local sources still ingested even though netbox failed
    assert summary["adrs"] == 2
    assert summary["runbooks"] == 1
    assert summary["decision_register_entries"] == 2


def test_recovery_from_failure(env) -> None:
    """After a failed run + a good run, status returns to 'ok'."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_broken_fetcher_returns_none(),
            plane_fetcher=_good_plane_fetcher(),
        )
        st1 = _db.get_source_status(conn, "netbox")
        assert st1["status"] == "error"

        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            plane_fetcher=_good_plane_fetcher(),
        )
        st2 = _db.get_source_status(conn, "netbox")
        assert st2["status"] == "ok"
        assert st2["error"] == ""


def test_plane_429_preserves_prior_plane_rows_and_netbox(env) -> None:
    """Plane 429 on re-run: prior plane data survives, NetBox unaffected."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            plane_fetcher=_good_plane_fetcher(),
        )
        before = _db.counts(conn)

    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            plane_fetcher=_plane_429_fetcher(),
        )
        after = _db.counts(conn)
        plane_st = _db.get_source_status(conn, "plane")
        nb_st = _db.get_source_status(conn, "netbox")

    # Plane data preserved
    assert after["plane_issues"] == before["plane_issues"] == 1
    assert after["plane_modules"] == before["plane_modules"] == 1
    # NetBox survived independently
    assert nb_st["status"] == "ok"
    # Plane status reflects rate-limit failure
    assert plane_st["status"] == "error"
    assert "rate-limited" in plane_st["error"]
