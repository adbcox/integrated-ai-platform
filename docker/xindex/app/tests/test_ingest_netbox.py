"""Tests for the NetBox ingester (D-16-02.1).

Pynetbox is replaced with a minimal stub via the `fetcher` injection
hook on `ingest.netbox.ingest`. No real NetBox calls.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app import db as _db
from app.ingest import netbox as _nb


def _svc(
    *,
    name,
    id_=1,
    protocol="tcp",
    ports=(80,),
    device=None,
    vm=None,
    description="",
    custom=None,
):
    return SimpleNamespace(
        name=name,
        id=id_,
        protocol=SimpleNamespace(value=protocol),
        ports=list(ports),
        device=device,
        virtual_machine=vm,
        description=description,
        custom_fields=custom or {},
    )


def _dev(*, name, id_=10, role="server", site="lab", status="active",
         primary_ip=None, description="", custom=None):
    return SimpleNamespace(
        name=name,
        id=id_,
        role=SimpleNamespace(name=role),
        site=SimpleNamespace(name=site),
        status=SimpleNamespace(value=status),
        primary_ip=SimpleNamespace(address=primary_ip) if primary_ip else None,
        description=description,
        custom_fields=custom or {},
    )


def _fetcher(devices, services):
    def fetch(token, url):
        assert token == "fake-token"
        return list(devices), list(services)
    return fetch


@pytest.fixture()
def conn(db_path: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("NETBOX_API_TOKEN", "fake-token")
    with _db.connect(db_path) as c:
        _db.init_schema(c)
        yield c


def test_ingest_writes_services_and_nodes(conn) -> None:
    dev_a = _dev(name="mac-mini", id_=10, primary_ip="192.168.10.145/24")
    svc_caddy = _svc(name="caddy", id_=1, protocol="tcp", ports=[443], device=dev_a)
    svc_vault = _svc(name="vault", id_=2, protocol="tcp", ports=[8200], device=dev_a)
    _db.reset_source(conn, "netbox")
    res = _nb.ingest(conn, fetcher=_fetcher([dev_a], [svc_caddy, svc_vault]))
    assert res.ok
    assert res.nodes == 1
    assert res.services == 2
    # 2 hosted_on links (one per service)
    assert res.entity_links == 2

    counts = _db.counts(conn)
    assert counts["nodes"] == 1
    assert counts["services"] == 2
    assert counts["entity_links"] == 2


def test_ingest_emits_depends_on_links_from_custom_field(conn) -> None:
    dev = _dev(name="mac-mini", id_=10)
    target = _svc(name="postgres", id_=1, ports=[5432], device=dev)
    consumer = _svc(
        name="netbox-app",
        id_=2,
        ports=[8084],
        device=dev,
        custom={"service_dependencies": [SimpleNamespace(name="postgres")]},
    )
    _db.reset_source(conn, "netbox")
    res = _nb.ingest(conn, fetcher=_fetcher([dev], [target, consumer]))
    assert res.ok
    rows = conn.execute(
        "SELECT from_ref, to_ref, link_type FROM entity_links "
        "WHERE link_type='depends_on'"
    ).fetchall()
    assert [(r["from_ref"], r["to_ref"]) for r in rows] == [
        ("netbox-app", "postgres")
    ]


def test_ingest_skipped_when_no_token(conn, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NETBOX_API_TOKEN", raising=False)
    monkeypatch.setattr(
        _nb, "CREDENTIALS_PATH", _nb.Path("/nonexistent/credentials.env")
    )
    res = _nb.ingest(conn, fetcher=_fetcher([], []))
    assert not res.ok
    assert res.skipped is True
    assert "NETBOX_API_TOKEN" in res.skip_reason


def test_ingest_marks_error_when_fetch_returns_none(conn) -> None:
    res = _nb.ingest(conn, fetcher=lambda token, url: None)
    assert not res.ok
    assert res.skipped is False
    assert "unreachable" in res.error or "auth failed" in res.error


def test_service_fts_searchable(conn) -> None:
    dev = _dev(name="mac-mini", id_=10)
    svc = _svc(name="caddy", id_=1, protocol="tcp", ports=[443], device=dev,
               description="reverse proxy")
    _db.reset_source(conn, "netbox")
    _nb.ingest(conn, fetcher=_fetcher([dev], [svc]))
    rows = conn.execute(
        "SELECT kind, ref FROM xindex_fts WHERE xindex_fts MATCH 'caddy'"
    ).fetchall()
    kinds = {r["kind"] for r in rows}
    assert "service" in kinds
