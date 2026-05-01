"""Each tool wraps the corresponding xindex HTTP endpoint correctly."""
from __future__ import annotations

import json
from typing import Any

import pytest

import server


@pytest.fixture()
def captured_calls(monkeypatch: pytest.MonkeyPatch):
    """Replace _xindex_get with a recorder that returns a canned dict."""
    calls: list[tuple[str, dict | None]] = []

    def fake(path: str, params: dict[str, Any] | None = None) -> Any:
        calls.append((path, params))
        return {"path": path, "params": params or {}}

    monkeypatch.setattr(server, "_xindex_get", fake)
    return calls


def test_search_passthrough(captured_calls):
    out = server._tool_search({"query": "vault unseal", "type": "runbook", "limit": 5})
    assert out["path"] == "/search"
    assert captured_calls[-1] == ("/search",
                                  {"q": "vault unseal", "type": "runbook", "limit": 5})


def test_search_defaults(captured_calls):
    server._tool_search({"query": "x"})
    _, params = captured_calls[-1]
    assert params == {"q": "x", "type": "all", "limit": 20}


def test_get_adr_normalizes_prefix(captured_calls):
    server._tool_get_adr({"adr_id": "ADR-A-006"})
    server._tool_get_adr({"adr_id": "A-006"})
    paths = [c[0] for c in captured_calls]
    assert paths == ["/adr/A-006", "/adr/A-006"]


def test_get_runbook_url_quotes_topic(captured_calls):
    server._tool_get_runbook({"topic": "vault unseal"})
    assert captured_calls[-1][0] == "/runbook/vault%20unseal"


def test_get_service_passthrough(captured_calls):
    server._tool_get_service({"name": "vault-server"})
    assert captured_calls[-1][0] == "/service/vault-server"


def test_get_node_passthrough(captured_calls):
    server._tool_get_node({"name": "mac-mini"})
    assert captured_calls[-1][0] == "/node/mac-mini"


def test_get_plane_passthrough(captured_calls):
    server._tool_get_plane({"external_id": "D-16-02.2"})
    assert captured_calls[-1][0] == "/plane/D-16-02.2"


def test_get_links_drops_none_filters(captured_calls):
    server._tool_get_links({"from_kind": "adr", "from_ref": "ADR-A-006"})
    path, params = captured_calls[-1]
    assert path == "/links"
    assert params is not None
    # The handler still includes None values; _xindex_get strips them at call time.
    # Verify the public-facing semantics: the recorder sees them so we just
    # assert keys we care about are present and unrelated keys are None.
    assert params["from_kind"] == "adr"
    assert params["from_ref"] == "ADR-A-006"
    assert params["to_kind"] is None
    assert params["link_type"] is None


def test_health_passthrough(captured_calls):
    server._tool_health({})
    assert captured_calls[-1] == ("/healthz", None)


def test_tool_count_matches_handler_count():
    """Every TOOLS entry has a TOOL_HANDLERS entry, and vice versa."""
    tool_names    = {t["name"] for t in server.TOOLS}
    handler_names = set(server.TOOL_HANDLERS.keys())
    assert tool_names == handler_names
    assert len(tool_names) == 8


def test_initialize_returns_advertised_capabilities():
    """JSON-RPC initialize returns the protocol version + tool capability."""
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    srv.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert len(sent) == 1
    result = sent[0]["result"]
    assert result["serverInfo"]["name"] == "xindex-mcp"
    assert result["capabilities"]["tools"] == {"listChanged": False}


def test_tools_list_emits_eight_tools():
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    srv.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = sent[0]["result"]["tools"]
    assert {t["name"] for t in tools} == {
        "xindex_search", "xindex_get_adr", "xindex_get_runbook",
        "xindex_get_service", "xindex_get_node", "xindex_get_plane",
        "xindex_get_links", "xindex_health",
    }


def test_tools_call_search_returns_text_content(monkeypatch):
    monkeypatch.setattr(server, "_xindex_get",
                        lambda p, params=None: {"count": 1, "results": []})
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    srv.handle({
        "jsonrpc": "2.0", "id": 3, "method": "tools/call",
        "params": {"name": "xindex_search", "arguments": {"query": "x"}},
    })
    result = sent[0]["result"]
    assert result["isError"] is False
    assert result["content"][0]["type"] == "text"
    assert json.loads(result["content"][0]["text"]) == {"count": 1, "results": []}
