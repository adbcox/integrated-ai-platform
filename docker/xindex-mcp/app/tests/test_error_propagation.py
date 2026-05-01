"""HTTP errors from xindex surface as MCP tool errors with detail preserved."""
from __future__ import annotations

import io

import pytest

import server


class _FakeURLOpen:
    def __init__(self, status: int, body: bytes, reason: str = "Error"):
        self.status = status
        self.body = body
        self.reason = reason

    def __call__(self, req, timeout):
        import urllib.error
        if self.status >= 400:
            err = urllib.error.HTTPError(req.full_url, self.status,
                                         self.reason, hdrs=None,
                                         fp=io.BytesIO(self.body))
            raise err
        # 2xx path: build a minimal context-manager-compatible response
        class R:
            def __init__(self, body): self._b = body
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def read(self): return self._b
        return R(self.body)


def test_http_404_becomes_isError_true(monkeypatch):
    fake = _FakeURLOpen(404, b'{"detail":"ADR not found"}', "Not Found")
    monkeypatch.setattr(server.urllib.request, "urlopen", fake)
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    srv.handle({
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "xindex_get_adr", "arguments": {"adr_id": "A-999"}},
    })
    result = sent[0]["result"]
    assert result["isError"] is True
    text = result["content"][0]["text"]
    assert "404" in text
    assert "ADR not found" in text


def test_http_500_surfaces_status(monkeypatch):
    fake = _FakeURLOpen(500, b'internal boom', "Server Error")
    monkeypatch.setattr(server.urllib.request, "urlopen", fake)
    with pytest.raises(server.XindexHTTPError) as exc:
        server._xindex_get("/healthz")
    assert exc.value.status == 500
    assert "internal boom" in str(exc.value)


def test_connection_error_becomes_status_zero(monkeypatch):
    import urllib.error

    def boom(req, timeout):
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr(server.urllib.request, "urlopen", boom)
    with pytest.raises(server.XindexHTTPError) as exc:
        server._xindex_get("/healthz")
    assert exc.value.status == 0
    assert "Connection refused" in str(exc.value)


def test_unknown_tool_returns_jsonrpc_error():
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    srv.handle({
        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
        "params": {"name": "xindex_does_not_exist", "arguments": {}},
    })
    assert sent[0].get("error", {}).get("code") == -32601


def test_parse_error_emits_jsonrpc_parse_error(monkeypatch):
    """Malformed line on stdin produces a -32700 reply but does not crash."""
    srv = server.MCPServer()
    sent: list[dict] = []
    srv._send = sent.append  # type: ignore[method-assign]
    monkeypatch.setattr("sys.stdin", io.StringIO("{not json}\n"))
    srv.run()
    assert sent[0]["error"]["code"] == -32700
