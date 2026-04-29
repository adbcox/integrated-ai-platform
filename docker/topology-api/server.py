"""Topology API — serves service-registry.yaml as nodes/edges for Grafana Node Graph.

Endpoints:
  GET /health                 → 200 {"ok": true}
  GET /api/topology/nodes     → JSON array of node objects
  GET /api/topology/edges     → JSON array of edge objects
  GET /api/topology           → {"nodes":[...], "edges":[...]}

The service file is re-read on every request — service-registry.yaml is small
(~1k lines, <50KB), so the latency cost is negligible vs. the operational
benefit of always reflecting the current registry without a reload signal.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import yaml

REGISTRY_PATH = os.environ.get(
    "REGISTRY_PATH", "/config/service-registry.yaml"
)
LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8300"))


CATEGORY_COLOR = {
    "ai": "#7c3aed",
    "automation": "#0ea5e9",
    "control-center": "#22c55e",
    "data": "#a16207",
    "infrastructure": "#ef4444",
    "mcp": "#f97316",
    "mcp-shim": "#fb923c",
    "media": "#ec4899",
    "monitoring": "#0891b2",
    "network": "#64748b",
    "observability": "#0d9488",
    "platform": "#3b82f6",
    "visibility": "#8b5cf6",
}


def load_registry() -> dict:
    with open(REGISTRY_PATH, "r") as f:
        return yaml.safe_load(f)


def build_nodes_edges(registry: dict) -> tuple[list[dict], list[dict]]:
    services = registry.get("services", [])
    ids = {svc["id"] for svc in services if "id" in svc}

    nodes = []
    for svc in services:
        sid = svc.get("id")
        if not sid:
            continue
        category = svc.get("category", "unknown")
        nodes.append(
            {
                "id": sid,
                "title": svc.get("name", sid),
                "subtitle": category,
                "mainStat": str(svc.get("port", "")),
                "secondaryStat": svc.get("host", ""),
                "color": CATEGORY_COLOR.get(category, "#9ca3af"),
                "arc__primary": 1.0,
                "detail__purpose": svc.get("purpose", ""),
                "detail__container": svc.get("container", ""),
                "detail__image": svc.get("image", ""),
            }
        )

    edges = []
    for svc in services:
        sid = svc.get("id")
        for dep in svc.get("depends_on", []) or []:
            if dep in ids:
                edges.append(
                    {
                        "id": f"{sid}->{dep}",
                        "source": sid,
                        "target": dep,
                        "mainStat": "depends",
                    }
                )
    return nodes, edges


class TopologyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write(
            "[topology-api] "
            + (fmt % args)
            + " path=%s\n" % self.path
        )

    def _write(self, status: int, body: dict | list):
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            self._write(200, {"ok": True, "registry": REGISTRY_PATH})
            return
        try:
            registry = load_registry()
        except FileNotFoundError:
            self._write(503, {"error": "registry-not-found", "path": REGISTRY_PATH})
            return
        except yaml.YAMLError as e:
            self._write(500, {"error": "yaml-parse", "detail": str(e)})
            return

        nodes, edges = build_nodes_edges(registry)
        if path == "/api/topology/nodes":
            self._write(200, nodes)
        elif path == "/api/topology/edges":
            self._write(200, edges)
        elif path in ("/", "/api/topology"):
            self._write(
                200,
                {
                    "nodes": nodes,
                    "edges": edges,
                    "service_count": len(nodes),
                    "edge_count": len(edges),
                },
            )
        else:
            self._write(404, {"error": "not-found", "path": path})


def main() -> None:
    print(
        f"[topology-api] listening on {LISTEN_HOST}:{LISTEN_PORT} registry={REGISTRY_PATH}",
        file=sys.stderr,
        flush=True,
    )
    httpd = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), TopologyHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
