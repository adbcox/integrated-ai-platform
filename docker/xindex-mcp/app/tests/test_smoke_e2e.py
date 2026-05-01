"""Smoke test against a real xindex.

Skipped unless XINDEX_BASE_URL is exported pointing at a reachable
xindex. Run locally with:

    XINDEX_BASE_URL=http://127.0.0.1:8095 \
        pytest docker/xindex-mcp/app/tests/test_smoke_e2e.py -q
"""
from __future__ import annotations

import os

import pytest

import server


def _xindex_reachable() -> bool:
    base = os.environ.get("XINDEX_BASE_URL")
    if not base:
        return False
    try:
        import urllib.request
        with urllib.request.urlopen(f"{base.rstrip('/')}/healthz", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _xindex_reachable(),
    reason="set XINDEX_BASE_URL to a reachable xindex to run smoke tests",
)


def test_health_round_trip():
    body = server._tool_health({})
    # /healthz shape: {sources: [...], counts: {...}}
    assert "sources" in body
    assert "counts" in body
    assert isinstance(body["sources"], list)


def test_search_round_trip():
    body = server._tool_search({"query": "vault", "limit": 3})
    assert "results" in body
    assert "count" in body
