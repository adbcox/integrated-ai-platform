"""End-to-end endpoint tests using FastAPI's TestClient."""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(
    fixture_docs: Path,
    db_path: str,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setenv("XINDEX_DOCS_ROOT", str(fixture_docs))

    # Re-import the module so the env vars take effect for module-level globals.
    from app import main as main_mod

    importlib.reload(main_mod)

    with TestClient(main_mod.app) as c:
        yield c


def test_healthz_reports_counts(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["counts"]["adrs"] == 2
    assert body["counts"]["runbooks"] == 1
    assert body["counts"]["decision_register_entries"] == 2


def test_adr_lookup_accepts_short_and_long_form(client: TestClient) -> None:
    for variant in ("A-001", "ADR-A-001", "adr-a-1"):
        r = client.get(f"/adr/{variant}")
        assert r.status_code == 200, variant
        assert r.json()["id"] == "ADR-A-001"
        assert "Decision" in r.json()["sections"]


def test_adr_lookup_returns_404_for_missing(client: TestClient) -> None:
    r = client.get("/adr/A-999")
    assert r.status_code == 404


def test_adr_lookup_carries_register_entry(client: TestClient) -> None:
    r = client.get("/adr/A-001")
    body = r.json()
    assert body["register_entry"] is not None
    assert body["register_entry"]["category"] == "Architecture and runtime"


def test_runbook_endpoint(client: TestClient) -> None:
    r = client.get("/runbook/sample-runbook")
    assert r.status_code == 200
    assert r.json()["title"] == "Sample Runbook"

    r2 = client.get("/runbook/missing")
    assert r2.status_code == 404


def test_search_returns_hits(client: TestClient) -> None:
    r = client.get("/search", params={"q": "NetBox"})
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    assert any(h["ref"] == "ADR-A-001" for h in body["results"])


def test_search_type_filter(client: TestClient) -> None:
    r = client.get("/search", params={"q": "Procedure", "type": "runbook"})
    assert r.status_code == 200
    body = r.json()
    assert all(h["kind"] == "runbook" for h in body["results"])


def test_refresh_accepts(client: TestClient) -> None:
    r = client.post("/refresh")
    assert r.status_code == 202
    assert r.json()["accepted"] is True
