#!/usr/bin/env python3
"""MCP (Model Context Protocol) server for Plane roadmap access.

Speaks JSON-RPC 2.0 over stdio — compatible with Claude Code, Claude.ai,
and any MCP-capable AI agent.

Registration in ~/.claude.json (Claude Code):
    {
      "mcpServers": {
        "plane-roadmap": {
          "command": "python3",
          "args": ["/path/to/integrated-ai-platform/mcp/plane_mcp_server.py"],
          "env": {
            "PLANE_URL": "http://localhost:8000",
            "PLANE_API_TOKEN": "your-token-here",
            "PLANE_WORKSPACE": "iap",
            "PLANE_PROJECT_ID": "your-project-uuid"
          }
        }
      }
    }

Registration in Claude.ai (Settings → Integrations → MCP):
    Server name: plane-roadmap
    Command: python3 /path/to/mcp/plane_mcp_server.py
    Working directory: /path/to/integrated-ai-platform

Tools exposed:
    list_issues         — paginated issue list with filtering
    get_issue           — single issue by RM-* ID
    create_issue        — create new roadmap item
    update_status       — change issue status (with markdown sync)
    search_issues       — full-text search
    get_stats           — summary counts by state/category
    list_states         — available workflow states
    list_categories     — available category labels
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(os.environ.get("REPO_ROOT", Path(__file__).parent.parent))
sys.path.insert(0, str(_REPO_ROOT))

from framework.plane_connector import PlaneAPI


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS: list[dict] = [
    {
        "name": "list_issues",
        "description": (
            "List roadmap issues from Plane. "
            "Returns RM-* IDs, titles, statuses, categories, and priorities. "
            "Use status filter to focus on specific workflow states."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status: Backlog, In Progress, Done, Cancelled",
                    "enum": ["Backlog", "In Progress", "Done", "Cancelled"],
                },
                "category": {
                    "type": "string",
                    "description": "Filter by category label (e.g. API, CLI, MEDIA, TESTING)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max issues to return (default 50, max 200)",
                    "default": 50,
                },
                "offset": {
                    "type": "integer",
                    "description": "Skip this many issues (for pagination)",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_issue",
        "description": (
            "Get details for a single roadmap issue by its RM-* ID. "
            "Returns full description, current status, labels, and history."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "RM-* ID, e.g. RM-API-100 or RM-MEDIA-001",
                },
            },
            "required": ["id"],
        },
    },
    {
        "name": "create_issue",
        "description": (
            "Create a new roadmap item in Plane. "
            "The item will also need a matching markdown file in docs/roadmap/ITEMS/."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "RM-* ID for the new issue (e.g. RM-API-200)",
                },
                "title": {
                    "type": "string",
                    "description": "Short descriptive title",
                },
                "description": {
                    "type": "string",
                    "description": "What this issue involves",
                },
                "category": {
                    "type": "string",
                    "description": "Category label (e.g. API, CLI, MEDIA)",
                },
                "status": {
                    "type": "string",
                    "description": "Initial status (default: Accepted → Backlog)",
                    "default": "Accepted",
                },
                "priority": {
                    "type": "string",
                    "description": "Priority: Critical, High, Medium, Low",
                    "default": "Medium",
                },
            },
            "required": ["id", "title", "category"],
        },
    },
    {
        "name": "update_status",
        "description": (
            "Change the status of a roadmap issue. "
            "This updates Plane AND syncs the change back to the markdown file. "
            "Valid transitions: Accepted→In progress→Completed, or →Retired."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "string",
                    "description": "RM-* ID of the issue to update",
                },
                "status": {
                    "type": "string",
                    "description": "New status: Accepted, Planning, In progress, Completed, Retired",
                    "enum": ["Accepted", "Planning", "In progress", "Completed", "Retired"],
                },
                "sync_markdown": {
                    "type": "boolean",
                    "description": "Whether to also update the markdown file (default: true)",
                    "default": True,
                },
            },
            "required": ["id", "status"],
        },
    },
    {
        "name": "search_issues",
        "description": (
            "Full-text search across roadmap issue titles and descriptions. "
            "Useful for finding related work before creating new issues."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search terms",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 20)",
                    "default": 20,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stats",
        "description": (
            "Get summary statistics for the roadmap: total count, "
            "breakdown by state (Backlog/In Progress/Done/Cancelled) and top categories."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_states",
        "description": "List all available workflow states in the Plane project.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "list_categories",
        "description": "List all category labels defined in the Plane project.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def _fmt_issue(issue: dict, states: dict[str, str], labels: dict[str, str]) -> dict:
    """Format a Plane issue for MCP response."""
    name  = issue.get("name", "")
    state = states.get(issue.get("state", ""), "Unknown")
    lids  = issue.get("label_ids", [])
    cats  = [labels.get(lid, lid) for lid in lids]

    import re
    id_match = re.match(r"^\[(RM-[A-Z0-9/-]+)\]\s*(.*)", name)
    rm_id  = id_match.group(1) if id_match else ""
    title  = id_match.group(2) if id_match else name

    return {
        "id":          rm_id,
        "title":       title,
        "status":      state,
        "categories":  cats,
        "priority":    issue.get("priority", ""),
        "plane_id":    issue.get("id", ""),
        "created_at":  issue.get("created_at", ""),
        "updated_at":  issue.get("updated_at", ""),
    }


def tool_list_issues(api: PlaneAPI, args: dict) -> str:
    limit  = min(int(args.get("limit", 50)), 200)
    offset = int(args.get("offset", 0))
    status = args.get("status")
    cat    = args.get("category")

    issues = api.list_all_issues()
    states = {s["id"]: s["name"] for s in api.list_states()}
    labels = {lbl["id"]: lbl["name"] for lbl in api.list_labels()}

    formatted = [_fmt_issue(i, states, labels) for i in issues]

    if status:
        formatted = [i for i in formatted if i["status"].lower() == status.lower()]
    if cat:
        formatted = [i for i in formatted if cat.upper() in [c.upper() for c in i["categories"]]]

    page = formatted[offset:offset+limit]
    return json.dumps({
        "total":   len(formatted),
        "offset":  offset,
        "limit":   limit,
        "issues":  page,
    }, indent=2)


def tool_get_issue(api: PlaneAPI, args: dict) -> str:
    rm_id = args.get("id", "").strip()
    if not rm_id:
        return json.dumps({"error": "id is required"})

    issue = api.get_issue_by_external_id(rm_id)
    if not issue:
        return json.dumps({"error": f"Issue not found: {rm_id}"})

    states = {s["id"]: s["name"] for s in api.list_states()}
    labels = {lbl["id"]: lbl["name"] for lbl in api.list_labels()}

    result = _fmt_issue(issue, states, labels)
    result["description"] = issue.get("description_stripped", "")

    # Add markdown path if available
    md_path = _REPO_ROOT / "docs" / "roadmap" / "ITEMS" / f"{rm_id}.md"
    if md_path.exists():
        result["markdown_file"] = str(md_path.relative_to(_REPO_ROOT))

    return json.dumps(result, indent=2)


def tool_create_issue(api: PlaneAPI, args: dict) -> str:
    rm_id    = args.get("id", "").strip()
    title    = args.get("title", "").strip()
    category = args.get("category", "").strip()

    if not rm_id or not title:
        return json.dumps({"error": "id and title are required"})

    existing = api.get_issue_by_external_id(rm_id)
    if existing:
        return json.dumps({"error": f"{rm_id} already exists in Plane", "plane_id": existing["id"]})

    issue, _ = api.upsert_issue(
        external_id = rm_id,
        title       = title,
        description = args.get("description", ""),
        state_name  = args.get("status", "Accepted"),
        category    = category,
        priority    = args.get("priority", "Medium"),
    )
    return json.dumps({
        "created": True,
        "plane_id": issue.get("id"),
        "id":       rm_id,
        "title":    title,
        "note":     "Create the matching markdown file at docs/roadmap/ITEMS/{rm_id}.md",
    }, indent=2)


def tool_update_status(api: PlaneAPI, args: dict) -> str:
    rm_id   = args.get("id", "").strip()
    status  = args.get("status", "").strip()
    do_sync = args.get("sync_markdown", True)

    if not rm_id or not status:
        return json.dumps({"error": "id and status are required"})

    issue = api.get_issue_by_external_id(rm_id)
    if not issue:
        return json.dumps({"error": f"Issue not found: {rm_id}"})

    from framework.plane_connector import MARKDOWN_TO_PLANE_STATE
    plane_state = MARKDOWN_TO_PLANE_STATE.get(status, "Backlog")
    api.update_issue_state(issue["id"], plane_state)

    result: dict[str, Any] = {
        "updated":     True,
        "id":          rm_id,
        "new_status":  status,
        "plane_state": plane_state,
    }

    if do_sync:
        from bin.sync_plane_to_markdown import write_md_status, find_md_path
        md_path = find_md_path(rm_id)
        if md_path:
            changed = write_md_status(md_path, status)
            result["markdown_updated"] = changed
            result["markdown_file"]    = str(md_path.relative_to(_REPO_ROOT))
        else:
            result["markdown_updated"] = False
            result["note"] = f"No markdown file found for {rm_id}"

    return json.dumps(result, indent=2)


def tool_search_issues(api: PlaneAPI, args: dict) -> str:
    query  = args.get("query", "").strip()
    limit  = min(int(args.get("limit", 20)), 100)

    if not query:
        return json.dumps({"error": "query is required"})

    issues = api.search_issues(query, limit=limit)
    states = {s["id"]: s["name"] for s in api.list_states()}
    labels = {lbl["id"]: lbl["name"] for lbl in api.list_labels()}

    return json.dumps({
        "query":  query,
        "count":  len(issues),
        "issues": [_fmt_issue(i, states, labels) for i in issues],
    }, indent=2)


def tool_get_stats(api: PlaneAPI, _args: dict) -> str:
    stats  = api.get_stats()
    labels = {lbl["id"]: lbl["name"] for lbl in api.list_labels()}

    issues = api.list_all_issues()
    cat_counts: dict[str, int] = {}
    for issue in issues:
        for lid in issue.get("label_ids", []):
            cat = labels.get(lid, lid)
            cat_counts[cat] = cat_counts.get(cat, 0) + 1

    top_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:10]

    return json.dumps({
        "total":         stats["total"],
        "by_state":      stats["by_state"],
        "top_categories": dict(top_cats),
    }, indent=2)


def tool_list_states(api: PlaneAPI, _args: dict) -> str:
    states = api.list_states(use_cache=False)
    return json.dumps([{"id": s["id"], "name": s["name"], "group": s.get("group", "")}
                       for s in states], indent=2)


def tool_list_categories(api: PlaneAPI, _args: dict) -> str:
    labels = api.list_labels(use_cache=False)
    return json.dumps([{"id": l["id"], "name": l["name"], "color": l.get("color", "")}
                       for l in labels], indent=2)


TOOL_HANDLERS = {
    "list_issues":      tool_list_issues,
    "get_issue":        tool_get_issue,
    "create_issue":     tool_create_issue,
    "update_status":    tool_update_status,
    "search_issues":    tool_search_issues,
    "get_stats":        tool_get_stats,
    "list_states":      tool_list_states,
    "list_categories":  tool_list_categories,
}


# ── MCP JSON-RPC protocol ─────────────────────────────────────────────────────

class MCPServer:
    def __init__(self) -> None:
        self.api = PlaneAPI()
        self._initialized = False

    def _send(self, obj: dict) -> None:
        line = json.dumps(obj)
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def _error(self, req_id: Any, code: int, message: str) -> None:
        self._send({"jsonrpc": "2.0", "id": req_id,
                    "error": {"code": code, "message": message}})

    def _result(self, req_id: Any, result: Any) -> None:
        self._send({"jsonrpc": "2.0", "id": req_id, "result": result})

    def handle(self, msg: dict) -> None:
        method  = msg.get("method", "")
        req_id  = msg.get("id")
        params  = msg.get("params", {})

        if method == "initialize":
            self._initialized = True
            self._result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name":    "plane-roadmap",
                    "version": "1.0.0",
                },
            })
            return

        if method == "initialized":
            return  # notification, no response needed

        if method == "tools/list":
            self._result(req_id, {"tools": TOOLS})
            return

        if method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            handler   = TOOL_HANDLERS.get(tool_name)
            if not handler:
                self._error(req_id, -32601, f"Unknown tool: {tool_name}")
                return
            try:
                output = handler(self.api, tool_args)
                self._result(req_id, {
                    "content": [{"type": "text", "text": output}],
                    "isError": False,
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

        # Unknown method
        if req_id is not None:
            self._error(req_id, -32601, f"Method not found: {method}")

    def run(self) -> None:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError as e:
                self._send({"jsonrpc": "2.0", "id": None,
                            "error": {"code": -32700, "message": f"Parse error: {e}"}})
                continue
            try:
                self.handle(msg)
            except Exception as exc:
                req_id = msg.get("id")
                if req_id is not None:
                    self._error(req_id, -32603, f"Internal error: {exc}")


if __name__ == "__main__":
    MCPServer().run()
