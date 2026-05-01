"""Partial-refresh doctrine tests (D-16-02.1).

Covers the core invariant: a NetBox failure on a re-ingest must not
wipe healthy NetBox rows from the previous run, and must not affect
local sources at all.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app import db as _db
from app import ingest as _ingest


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


@pytest.fixture()
def env(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("NETBOX_API_TOKEN", "fake-token")
    return fixture_docs, db_path


def test_first_run_populates_all_sources(env) -> None:
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs), netbox_fetcher=_good_fetcher()
        )
    assert summary["adrs"] == 2
    assert summary["nodes"] == 1
    assert summary["services"] == 1

    with _db.connect(db_path) as conn:
        st = _db.get_source_status(conn, "netbox")
        assert st["status"] == "ok"
        local = _db.get_source_status(conn, "adr")
        assert local["status"] == "ok"


def test_netbox_failure_preserves_prior_netbox_rows(env) -> None:
    """NetBox down on a re-run: prior services/nodes survive, status flips."""
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        _ingest.ingest_all(
            conn, str(fixture_docs), netbox_fetcher=_good_fetcher()
        )
        before = _db.counts(conn)

    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn, str(fixture_docs), netbox_fetcher=_broken_fetcher_returns_none()
        )
        after = _db.counts(conn)
        st = _db.get_source_status(conn, "netbox")

    # local sources rebuilt fine
    assert summary["adrs"] == 2
    # external survival: rows kept
    assert after["services"] == before["services"] == 1
    assert after["nodes"] == before["nodes"] == 1
    # but status reflects the failure
    assert st["status"] == "error"
    assert "unreachable" in st["error"] or "auth" in st["error"]


def test_netbox_failure_does_not_affect_local_sources(env) -> None:
    fixture_docs, db_path = env
    with _db.connect(db_path) as conn:
        summary = _ingest.ingest_all(
            conn,
            str(fixture_docs),
            netbox_fetcher=_broken_fetcher_returns_none(),
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
            conn, str(fixture_docs), netbox_fetcher=_broken_fetcher_returns_none()
        )
        st1 = _db.get_source_status(conn, "netbox")
        assert st1["status"] == "error"

        _ingest.ingest_all(
            conn, str(fixture_docs), netbox_fetcher=_good_fetcher()
        )
        st2 = _db.get_source_status(conn, "netbox")
        assert st2["status"] == "ok"
        assert st2["error"] == ""
