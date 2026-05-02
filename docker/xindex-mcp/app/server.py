#!/usr/bin/env python3
"""xindex MCP server (D-16-02.3).

Read-only stdio MCP wrapper around the xindex HTTP API. Speaks JSON-RPC 2.0
on stdin/stdout — directly compatible with Claude Code, Claude.ai, and any
MCP-aware client. The container variant wraps this with `supergateway` to
project the same surface as streamableHttp.

Backend: XINDEX_BASE_URL (default http://xindex:8000 inside compose,
http://127.0.0.1:8095 for a host-side stdio invocation).

Tools (all read-only; xindex itself is canonical-repo-mirroring per ADR-A-006):

    xindex_search          FTS5 across adr/runbook/register/service/node/workpackage
    xindex_get_adr         full ADR detail by id (A-NNN or ADR-A-NNN)
    xindex_get_runbook     runbook content by topic
    xindex_get_service     NetBox service detail
    xindex_get_node        NetBox device detail
    xindex_get_workpackage OpenProject work package by external_id
    xindex_get_plane       DEPRECATED alias for xindex_get_workpackage
                           (one-cycle compatibility shim; D-17-04 WP-17-04-05.5,
                           remove after consumers migrate)
    xindex_get_links       filtered entity_links
    xindex_health          per-source freshness / status

The server NEVER writes to xindex (no /refresh tool exposed by design — a
periodic refresh is the platform's job, not the consumer agent's).
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

XINDEX_BASE_URL = os.environ.get("XINDEX_BASE_URL", "http://xindex:8000").rstrip("/")
HTTP_TIMEOUT_S  = float(os.environ.get("XINDEX_HTTP_TIMEOUT", "10"))


# ── HTTP helpers (stdlib only — no httpx/requests dep in container) ──────────

class XindexHTTPError(Exception):
    def __init__(self, status: int, message: str, url: str) -> None:
        super().__init__(f"xindex {status}: {message} ({url})")
        self.status = status
        self.message = message
        self.url = url


def _xindex_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """GET <base>/<path> with optional query params; return parsed JSON.

    Raises XindexHTTPError on non-2xx so the calling tool can surface a
    structured MCP error to the model.
    """
    url = f"{XINDEX_BASE_URL}{path}"
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            url = f"{url}?{urllib.parse.urlencode(clean, doseq=True)}"
    req = urllib.request.Request(url, method="GET",
                                  headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT_S) as resp:
            body = resp.read().decode("utf-8")
        return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        try:
            err_body = exc.read().decode("utf-8")
        except Exception:
            err_body = ""
        message = ""
        if err_body:
            try:
                message = (json.loads(err_body).get("detail")
                           or json.loads(err_body).get("error") or err_body)
            except Exception:
                message = err_body
        raise XindexHTTPError(exc.code, message or exc.reason, url) from exc
    except urllib.error.URLError as exc:
        raise XindexHTTPError(0, f"connection error: {exc.reason}", url) from exc


# ── Tool definitions (descriptions are what the model sees) ──────────────────

TOOLS: list[dict] = [
    {
        "name": "xindex_search",
        "description": (
            "Full-text search across all xindex sources. "
            "Returns ranked SearchResult rows ordered by FTS5 BM25. "
            "Use type='all' for cross-source discovery; narrow to a specific "
            "kind when you already know the artifact class. "
            "Example: xindex_search(query='vault unseal', type='runbook')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "FTS5 query string"},
                "type":  {"type": "string",
                          "description": "Result kind filter",
                          "enum": ["all", "adr", "runbook", "register",
                                   "service", "node", "workpackage"],
                          "default": "all"},
                "limit": {"type": "integer", "default": 20,
                          "minimum": 1, "maximum": 100},
            },
            "required": ["query"],
        },
    },
    {
        "name": "xindex_get_adr",
        "description": (
            "Fetch full ADR detail by id. Accepts 'A-NNN' or 'ADR-A-NNN'. "
            "Returns body, sections, register_entry, and workpackage_tracking "
            "when the ADR has an OpenProject work package. "
            "Use after xindex_search has identified the ADR you need to read in full. "
            "Example: xindex_get_adr(adr_id='A-006')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "adr_id": {"type": "string",
                           "description": "ADR id, e.g. 'A-006' or 'ADR-A-006'"},
            },
            "required": ["adr_id"],
        },
    },
    {
        "name": "xindex_get_runbook",
        "description": (
            "Fetch a runbook by topic name (filename without .md). "
            "Returns full markdown body plus any cross-referenced services/ADRs. "
            "Use when an operational task is in scope and the runbook covers it. "
            "Example: xindex_get_runbook(topic='vault-unseal')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string",
                          "description": "Runbook topic (filename stem)"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "xindex_get_service",
        "description": (
            "Fetch a NetBox service by name with its custom fields and "
            "entity_links (hosted_on node, depends_on services, governing_adrs). "
            "Use to answer 'what is service X, where does it run, what does it "
            "depend on'. "
            "Example: xindex_get_service(name='vault-server')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string",
                         "description": "NetBox service name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "xindex_get_node",
        "description": (
            "Fetch a NetBox device (node) by name with the services hosted on "
            "it. Use to answer 'what runs on host Y'. "
            "Example: xindex_get_node(name='mac-mini')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string",
                         "description": "NetBox device name"},
            },
            "required": ["name"],
        },
    },
    {
        "name": "xindex_get_workpackage",
        "description": (
            "Fetch an OpenProject work package by external_id (e.g. 'D-17-04', "
            "'ADR-A-006', 'Phase-17'). Returns status, version, description, "
            "and inbound tracked_in entity_links. "
            "Use to check operational status of work tracked in OpenProject. "
            "Example: xindex_get_workpackage(external_id='D-17-04')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "external_id": {"type": "string",
                                "description": "OpenProject WP external_id"},
            },
            "required": ["external_id"],
        },
    },
    {
        "name": "xindex_get_plane",
        "description": (
            "DEPRECATED — use xindex_get_workpackage. Forwards to the "
            "OpenProject work package endpoint for one-cycle compatibility "
            "after the D-17-04 WP-17-04-05.5 substrate flip. Will be "
            "removed in the next xindex-mcp release."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "external_id": {"type": "string",
                                "description": "external_id (forwards to /workpackage)"},
            },
            "required": ["external_id"],
        },
    },
    {
        "name": "xindex_get_links",
        "description": (
            "Filter the entity_links table. All filters optional — when none "
            "supplied returns the first 100 rows. Use to traverse cross-source "
            "relations: which ADRs govern service X, which work packages track "
            "deliverable D-17-04, etc. "
            "from_kind/to_kind ∈ {adr,runbook,deliverable,phase,service,node,"
            "workpackage}. link_type ∈ {hosted_on,depends_on,governs,tracked_in,...}. "
            "Example: xindex_get_links(from_kind='adr', from_ref='ADR-A-006')."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_kind": {"type": "string"},
                "from_ref":  {"type": "string"},
                "to_kind":   {"type": "string"},
                "to_ref":    {"type": "string"},
                "link_type": {"type": "string"},
                "source":    {"type": "string",
                              "description": "ingestion source filter"},
            },
        },
    },
    {
        "name": "xindex_health",
        "description": (
            "Return /healthz: per-source last_ingest_at + status, plus row "
            "counts. Use BEFORE relying on a query result to confirm the "
            "data is fresh — netbox or openproject may be in 'error' state "
            "if their last refresh failed. "
            "Example: xindex_health()."
        ),
        "inputSchema": {"type": "object", "properties": {}},
    },
]


# ── Tool handlers ────────────────────────────────────────────────────────────

def _normalize_adr_id(raw: str) -> str:
    """Accept either 'A-006' or 'ADR-A-006' on the way out to xindex."""
    raw = raw.strip()
    if raw.upper().startswith("ADR-"):
        raw = raw[4:]
    return raw


def _tool_search(args: dict) -> Any:
    return _xindex_get("/search", {
        "q":     args["query"],
        "type":  args.get("type", "all"),
        "limit": args.get("limit", 20),
    })


def _tool_get_adr(args: dict) -> Any:
    return _xindex_get(f"/adr/{_normalize_adr_id(args['adr_id'])}")


def _tool_get_runbook(args: dict) -> Any:
    return _xindex_get(f"/runbook/{urllib.parse.quote(args['topic'], safe='')}")


def _tool_get_service(args: dict) -> Any:
    return _xindex_get(f"/service/{urllib.parse.quote(args['name'], safe='')}")


def _tool_get_node(args: dict) -> Any:
    return _xindex_get(f"/node/{urllib.parse.quote(args['name'], safe='')}")


def _tool_get_workpackage(args: dict) -> Any:
    return _xindex_get(
        f"/workpackage/{urllib.parse.quote(args['external_id'], safe='')}"
    )


def _tool_get_plane(args: dict) -> Any:
    """Deprecated alias — forwards to xindex_get_workpackage.

    One-cycle compatibility shim per D-17-04 WP-17-04-05.5; remove
    after consumers migrate.
    """
    return _tool_get_workpackage(args)


def _tool_get_links(args: dict) -> Any:
    return _xindex_get("/links", {
        "from_kind": args.get("from_kind"),
        "from_ref":  args.get("from_ref"),
        "to_kind":   args.get("to_kind"),
        "to_ref":    args.get("to_ref"),
        "link_type": args.get("link_type"),
        "source":    args.get("source"),
    })


def _tool_health(_args: dict) -> Any:
    return _xindex_get("/healthz")


TOOL_HANDLERS = {
    "xindex_search":          _tool_search,
    "xindex_get_adr":         _tool_get_adr,
    "xindex_get_runbook":     _tool_get_runbook,
    "xindex_get_service":     _tool_get_service,
    "xindex_get_node":        _tool_get_node,
    "xindex_get_workpackage": _tool_get_workpackage,
    "xindex_get_plane":       _tool_get_plane,  # deprecated alias
    "xindex_get_links":       _tool_get_links,
    "xindex_health":          _tool_health,
}


# ── MCP JSON-RPC protocol ────────────────────────────────────────────────────

class MCPServer:
    def __init__(self) -> None:
        self._initialized = False

    def _send(self, obj: dict) -> None:
        sys.stdout.write(json.dumps(obj) + "\n")
        sys.stdout.flush()

    def _error(self, req_id: Any, code: int, message: str) -> None:
        self._send({"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": code, "message": message}})

    def _result(self, req_id: Any, result: Any) -> None:
        self._send({"jsonrpc": "2.0", "id": req_id, "result": result})

    def handle(self, msg: dict) -> None:
        method = msg.get("method", "")
        req_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            self._initialized = True
            self._result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "xindex-mcp", "version": "0.1.0"},
            })
            return

        if method in ("initialized", "notifications/initialized"):
            return  # notification

        if method == "tools/list":
            self._result(req_id, {"tools": TOOLS})
            return

        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {}) or {}
            handler   = TOOL_HANDLERS.get(tool_name)
            if not handler:
                self._error(req_id, -32601, f"Unknown tool: {tool_name}")
                return
            try:
                output = handler(tool_args)
                self._result(req_id, {
                    "content": [{"type": "text",
                                 "text": json.dumps(output, indent=2)}],
                    "isError": False,
                })
            except XindexHTTPError as exc:
                self._result(req_id, {
                    "content": [{"type": "text",
                                 "text": (f"xindex HTTP {exc.status}: "
                                          f"{exc.message} (url: {exc.url})")}],
                    "isError": True,
                })
            except Exception as exc:
                self._result(req_id, {
                    "content": [{"type": "text", "text": f"Error: {exc}"}],
                    "isError": True,
                })
            return

        if method == "ping":
            self._result(req_id, {})
            return

        if req_id is not None:
            self._error(req_id, -32601, f"Method not found: {method}")

    def run(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as exc:
                self._send({"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700,
                                      "message": f"Parse error: {exc}"}})
                continue
            try:
                self.handle(msg)
            except Exception as exc:
                req_id = msg.get("id")
                if req_id is not None:
                    self._error(req_id, -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    MCPServer().run()
