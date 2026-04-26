"""Multi-server orchestrator for the Integrated AI Platform.

Routes workloads across nodes (Mac Mini dashboard, Mac Studio compute, etc.)
using plain HTTP — no MCP filesystem dependency, no shared mount required.

Usage
-----
    from framework.orchestrator import Orchestrator

    orch = Orchestrator()
    status = orch.health_all()
    result = orch.route_task("train", {"model": "qwen2.5-coder:14b"})
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any


# ── Node definitions ──────────────────────────────────────────────────────────

@dataclass
class Node:
    name: str
    url: str                       # e.g. "http://mac-mini.local:8080"
    roles: list[str]               # e.g. ["dashboard", "media"]
    timeout: int = 10
    healthy: bool = False
    last_check: float = 0.0
    latency_ms: float = 0.0


# Default topology — override via ORCHESTRATOR_NODES env var (JSON list)
_DEFAULT_NODES = [
    Node(
        name="mac-mini",
        url=os.environ.get("MAC_MINI_URL", "http://localhost:8080"),
        roles=["dashboard", "media", "roadmap", "training"],
    ),
    Node(
        name="mac-studio",
        url=os.environ.get("MAC_STUDIO_URL", "http://mac-studio.local:8080"),
        roles=["compute", "training", "inference"],
    ),
]


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _http(method: str, url: str, body: dict | None = None,
          timeout: int = 10) -> tuple[dict, int]:
    """Return (response_dict, status_code). Raises on network error."""
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else {}, resp.status


def _get(url: str, timeout: int = 10) -> tuple[dict, int]:
    return _http("GET", url, timeout=timeout)


def _post(url: str, body: dict, timeout: int = 30) -> tuple[dict, int]:
    return _http("POST", url, body=body, timeout=timeout)


# ── Orchestrator ──────────────────────────────────────────────────────────────

class Orchestrator:
    """Route tasks across platform nodes via HTTP API."""

    def __init__(self, nodes: list[Node] | None = None):
        env_nodes = os.environ.get("ORCHESTRATOR_NODES")
        if env_nodes:
            raw = json.loads(env_nodes)
            self.nodes = [Node(**n) for n in raw]
        else:
            self.nodes = nodes or _DEFAULT_NODES

    # ── Health ────────────────────────────────────────────────────────────────

    def check_node(self, node: Node) -> bool:
        """Ping a single node's /api/health endpoint."""
        t0 = time.monotonic()
        try:
            d, status = _get(f"{node.url}/api/health", timeout=node.timeout)
            node.healthy    = status == 200
            node.latency_ms = (time.monotonic() - t0) * 1000
            node.last_check = time.time()
            return node.healthy
        except Exception:
            node.healthy    = False
            node.latency_ms = (time.monotonic() - t0) * 1000
            node.last_check = time.time()
            return False

    def health_all(self) -> dict:
        """Check all nodes and return summary dict."""
        results = {}
        for node in self.nodes:
            ok = self.check_node(node)
            results[node.name] = {
                "url":        node.url,
                "healthy":    ok,
                "latency_ms": round(node.latency_ms, 1),
                "roles":      node.roles,
                "checked_at": node.last_check,
            }
        return results

    def healthy_nodes(self, role: str | None = None) -> list[Node]:
        """Return nodes that are healthy (and optionally have the given role)."""
        nodes = [n for n in self.nodes if n.healthy]
        if role:
            nodes = [n for n in nodes if role in n.roles]
        return nodes

    # ── Task routing ──────────────────────────────────────────────────────────

    def route_task(self, task_type: str, payload: dict,
                   preferred_node: str | None = None) -> dict:
        """Route a task to the best available node.

        task_type → API endpoint mapping:
          "scan"    → POST /api/roadmap/scan
          "import"  → POST /api/roadmap/import
          "train"   → POST /api/train
          "generate"→ POST /api/development/generate
          "ai_item" → POST /api/roadmap/ai-generate
          "status"  → GET  /api/status
        """
        endpoint_map: dict[str, tuple[str, str]] = {
            "scan":     ("roadmap",   "POST /api/roadmap/scan"),
            "import":   ("roadmap",   "POST /api/roadmap/import"),
            "train":    ("training",  "POST /api/train"),
            "generate": ("compute",   "POST /api/development/generate"),
            "ai_item":  ("roadmap",   "POST /api/roadmap/ai-generate"),
            "status":   ("dashboard", "GET /api/status"),
        }

        if task_type not in endpoint_map:
            return {"error": f"Unknown task type: {task_type!r}"}

        role, path_spec = endpoint_map[task_type]
        method, path = path_spec.split(" ", 1)

        # Refresh health if stale (> 60s)
        for node in self.nodes:
            if time.time() - node.last_check > 60:
                self.check_node(node)

        # Pick node: preferred > role-matched healthy > any healthy
        target = None
        if preferred_node:
            target = next((n for n in self.nodes
                           if n.name == preferred_node and n.healthy), None)
        if target is None:
            # Prefer role-matched, fall back to any healthy node
            candidates = self.healthy_nodes(role) or self.healthy_nodes()
            # Sort by latency
            candidates.sort(key=lambda n: n.latency_ms)
            target = candidates[0] if candidates else None

        if target is None:
            return {"error": "No healthy nodes available", "task": task_type}

        url = f"{target.url}{path}"
        try:
            if method == "GET":
                result, status = _get(url, timeout=target.timeout)
            else:
                result, status = _post(url, payload, timeout=120)
            result["_node"]   = target.name
            result["_status"] = status
            return result
        except urllib.error.HTTPError as exc:
            return {"error": f"HTTP {exc.code}: {exc.reason}", "_node": target.name}
        except Exception as exc:
            return {"error": str(exc), "_node": target.name}

    # ── Convenience methods ───────────────────────────────────────────────────

    def scan_roadmap(self, node: str | None = None) -> dict:
        return self.route_task("scan", {}, preferred_node=node)

    def import_roadmap(self, items: list[dict], node: str | None = None) -> dict:
        return self.route_task("import", {"items": items}, preferred_node=node)

    def start_training(self, node: str | None = None) -> dict:
        return self.route_task("train", {}, preferred_node=node)

    def generate_code(self, prompt: str, engine: str = "claude",
                      node: str | None = None) -> dict:
        return self.route_task("generate", {
            "prompt": prompt, "engine": engine,
            "create_tests": True, "add_docs": False,
        }, preferred_node=node)

    def ai_roadmap_item(self, description: str, node: str | None = None) -> dict:
        return self.route_task("ai_item", {"description": description},
                               preferred_node=node)

    def status(self, node: str | None = None) -> dict:
        return self.route_task("status", {}, preferred_node=node)

    # ── Topology info ─────────────────────────────────────────────────────────

    def topology(self) -> dict:
        return {
            "nodes": [
                {
                    "name":       n.name,
                    "url":        n.url,
                    "roles":      n.roles,
                    "healthy":    n.healthy,
                    "latency_ms": round(n.latency_ms, 1),
                }
                for n in self.nodes
            ],
            "total":   len(self.nodes),
            "healthy": sum(1 for n in self.nodes if n.healthy),
        }
