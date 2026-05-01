"""Endpoint extension tests (D-16-02.1)."""
from __future__ import annotations

import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app import db as _db
from app.ingest import netbox as _nb


def _dev(name, ip=None):
    return SimpleNamespace(
        name=name, id=10,
        role=SimpleNamespace(name="server"),
        site=SimpleNamespace(name="lab"),
        status=SimpleNamespace(value="active"),
        primary_ip=SimpleNamespace(address=ip) if ip else None,
        description="control plane",
        custom_fields={},
    )


def _svc(name, dev, *, deps=()):
    return SimpleNamespace(
        name=name, id=1,
        protocol=SimpleNamespace(value="tcp"),
        ports=[443],
        device=dev,
        virtual_machine=None,
        description="reverse proxy",
        custom_fields={
            "service_dependencies": [SimpleNamespace(name=d) for d in deps]
        } if deps else {},
    )


@pytest.fixture()
def client(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("XINDEX_DOCS_ROOT", str(fixture_docs))
    monkeypatch.setenv("NETBOX_API_TOKEN", "fake-token")
    # Ensure no Plane creds leak in from the host env; the Plane
    # ingester should skip cleanly in this fixture.
    for k in ("PLANE_API_TOKEN", "PLANE_URL", "PLANE_WORKSPACE", "PLANE_PROJECT_ID"):
        monkeypatch.delenv(k, raising=False)
    from app.ingest import plane as _pl
    monkeypatch.setattr(
        _pl, "CREDENTIALS_PATH", _pl.Path("/nonexistent/plane.env")
    )

    from app import main as main_mod
    importlib.reload(main_mod)

    # Pre-populate: bypass startup (which would skip netbox without
    # a fetcher) and seed via direct ingest_all with a stub fetcher.
    dev = _dev("mac-mini", ip="192.168.10.145/24")
    pg = _svc("postgres", dev)
    caddy = _svc("caddy", dev, deps=["postgres"])

    def fetcher(token, url):
        return [dev], [pg, caddy]

    with _db.connect(db_path) as conn:
        from app import ingest as _ingest
        _ingest.ingest_all(conn, str(fixture_docs), netbox_fetcher=fetcher)

    with TestClient(main_mod.app) as c:
        yield c


def test_healthz_returns_per_source_health(client: TestClient) -> None:
    r = client.get("/healthz")
    body = r.json()
    by_src = {s["source"]: s for s in body["sources"]}
    assert "netbox" in by_src
    assert by_src["netbox"]["status"] == "ok"
    assert by_src["adr"]["status"] == "ok"
    # counts now include the new tables
    assert body["counts"]["services"] == 2
    assert body["counts"]["nodes"] == 1
    assert body["counts"]["entity_links"] >= 2  # 2 hosted_on + 1 depends_on


def test_get_service_returns_detail_and_links(client: TestClient) -> None:
    r = client.get("/service/caddy")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "caddy"
    assert body["protocol"] == "tcp"
    assert 443 in body["ports"]
    assert body["parent_kind"] == "device"
    assert body["parent_ref"] == "mac-mini"
    link_types = {l["link_type"] for l in body["links"]}
    assert "hosted_on" in link_types
    assert "depends_on" in link_types


def test_get_service_404(client: TestClient) -> None:
    r = client.get("/service/nope")
    assert r.status_code == 404


def test_get_node_returns_detail_and_links(client: TestClient) -> None:
    r = client.get("/node/mac-mini")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "mac-mini"
    assert body["site"] == "lab"
    assert body["status"] == "active"
    assert "192.168.10.145" in body["primary_ip"]
    # node has 2 inbound hosted_on links from postgres + caddy
    inbound = [l for l in body["links"] if l["to_kind"] == "node"]
    assert len(inbound) == 2


def test_links_query_filters(client: TestClient) -> None:
    r = client.get("/links", params={"link_type": "depends_on"})
    body = r.json()
    assert body["count"] >= 1
    assert all(l["link_type"] == "depends_on" for l in body["results"])


def test_search_type_service(client: TestClient) -> None:
    r = client.get("/search", params={"q": "caddy", "type": "service"})
    body = r.json()
    assert body["count"] >= 1
    assert all(h["kind"] == "service" for h in body["results"])
