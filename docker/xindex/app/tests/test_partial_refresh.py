"""Partial-refresh doctrine tests (D-16-02.1, extended D-17-04 WP-17-04-05.5).

Covers the core invariant: a failure in one external source on a
re-ingest must not wipe healthy rows from the previous run for that
source, and must not affect local sources or other external sources
at all. Both NetBox and OpenProject share this contract.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app import db as _db
from app import ingest as _ingest
from app.ingest import openproject as _op


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


def _good_op_fetcher():
    def fetch(creds):
        versions = [{"name": "Phase-17", "id": 16,
                     "external_id": "Phase-17", "description": ""}]
        statuses = [{"name": "New", "id": 1, "is_closed": False}]
        wps = [{
            "external_id": "D-17-04",
            "name": "[D-17-04] Replace Plane CE with OpenProject",
            "id": 601,
            "state": 1,
            "version_id": 16,
            "description_html": "",
            "description_raw": "",
            "updated_at": "2026-05-02T12:00:00Z",
            "project_id": 1,
        }]
        return versions, statuses, wps
    return fetch


def _broken_op_fetcher():
    return lambda creds: None


@pytest.fixture()
def env(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("NETBOX_API_TOKEN", "fake-token")
    monkeypatch.setenv("OPENPROJECT_API_TOKEN", "op-fake-token")
    monkeypatch.setenv("OPENPROJECT_URL", "http://openproject.example")
    monkeypatch.setenv("OPENPROJECT_PROJECT", "roadmap")
    monkeypatch.setattr(
        _op, "CREDENTIALS_PATH", _op.Path("/nonexistent/openproject.env")
    )
    return fixture_docs, db_path


def test_first_run_populates_all_sources(env) -> None:
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            openproject_fetcher=_good_op_fetcher(),
        )
    assert summary["adrs"] == 2
    assert summary["nodes"] == 1
    assert summary["services"] == 1
    assert summary["op_workpackages"] == 1
    assert summary["op_versions"] == 1

    with _db.connect(db_path) as conn:
        st = _db.get_source_status(conn, "netbox")
        assert st["status"] == "ok"
        opst = _db.get_source_status(conn, "openproject")
        assert opst["status"] == "ok"
        local = _db.get_source_status(conn, "adr")
        assert local["status"] == "ok"


def test_netbox_failure_preserves_prior_netbox_rows(env) -> None:
    """NetBox down on a re-run: prior services/nodes survive, status flips."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            openproject_fetcher=_good_op_fetcher(),
        )
        before = _db.counts(conn)

    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_broken_fetcher_returns_none(),
            openproject_fetcher=_good_op_fetcher(),
        )
        after = _db.counts(conn)
        st = _db.get_source_status(conn, "netbox")

    # local sources rebuilt fine
    assert summary["adrs"] == 2
    # external survival: NetBox rows kept
    assert after["services"] == before["services"] == 1
    assert after["nodes"] == before["nodes"] == 1
    # openproject unaffected
    assert after["op_workpackages"] == before["op_workpackages"] == 1
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
            openproject_fetcher=_good_op_fetcher(),
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
            openproject_fetcher=_good_op_fetcher(),
        )
        st1 = _db.get_source_status(conn, "netbox")
        assert st1["status"] == "error"

        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            openproject_fetcher=_good_op_fetcher(),
        )
        st2 = _db.get_source_status(conn, "netbox")
        assert st2["status"] == "ok"
        assert st2["error"] == ""


def test_openproject_failure_preserves_prior_op_rows_and_netbox(env) -> None:
    """OpenProject down on re-run: prior op data survives, NetBox unaffected."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            openproject_fetcher=_good_op_fetcher(),
        )
        before = _db.counts(conn)

    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs),
            netbox_fetcher=_good_fetcher(),
            openproject_fetcher=_broken_op_fetcher(),
        )
        after = _db.counts(conn)
        op_st = _db.get_source_status(conn, "openproject")
        nb_st = _db.get_source_status(conn, "netbox")

    # OpenProject data preserved
    assert after["op_workpackages"] == before["op_workpackages"] == 1
    assert after["op_versions"] == before["op_versions"] == 1
    # NetBox survived independently
    assert nb_st["status"] == "ok"
    # OpenProject status reflects unreachable failure
    assert op_st["status"] == "error"
    assert "unreachable" in op_st["error"] or "auth" in op_st["error"]
