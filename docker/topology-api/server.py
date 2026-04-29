"""Topology API — serves the service registry as nodes/edges for Grafana Node Graph.

Endpoints:
  GET /health                 → 200 {"ok": true}
  GET /api/topology/nodes     → JSON array of node objects
  GET /api/topology/edges     → JSON array of edge objects
  GET /api/topology           → {"nodes":[...], "edges":[...]}

Source of truth (Block 4.C C5.2b):
  CMDB_SOURCE=yaml   (default during transition) — read service-registry.yaml
  CMDB_SOURCE=netbox — read from NetBox (ipam.service objects)

Both backends produce byte-identical node/edge JSON for the same registry
data. See scripts/cmdb-equivalence.sh for the contract and proof.

The service list is re-read on every request — registry shape is small
(<50KB / 75 services), so the latency cost is negligible vs. the
operational benefit of always reflecting the current source without a
reload signal. NetBox mode adds ~2 HTTP calls (devices + services
pages) per request; still well under 100 ms on the loopback.
"""
from __future__ import annotations

import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Make the shared loader importable regardless of how the container
# is built. The Dockerfile copies cmdb_source.py next to server.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cmdb_source  # noqa: E402

REGISTRY_PATH = os.environ.get(
    "REGISTRY_PATH", "/config/service-registry.yaml"
)
LISTEN_HOST = os.environ.get("LISTEN_HOST", "0.0.0.0")
LISTEN_PORT = int(os.environ.get("LISTEN_PORT", "8300"))
CMDB_SOURCE = os.environ.get("CMDB_SOURCE", "yaml")


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


def load_services() -> list[dict]:
    """Return the canonical list of services from the configured source.

    cmdb_source.load_services() respects $CMDB_SOURCE; we set
    $CMDB_REGISTRY to topology-api's mounted path so the YAML backend
    finds it without env confusion.
    """
    # Yaml backend respects CMDB_REGISTRY; NetBox backend respects
    # NETBOX_URL / NETBOX_API_TOKEN.
    if CMDB_SOURCE == "yaml":
        os.environ["CMDB_REGISTRY"] = REGISTRY_PATH
    return cmdb_source.load_services()


def build_nodes_edges(services: list[dict]) -> tuple[list[dict], list[dict]]:
    # Sort by id so the byte-level output is stable regardless of the
    # source iteration order (NetBox returns services in a different
    # order than registry YAML). Without this, equivalence between
    # backends is not byte-identical even when the data is identical.
    services = sorted(services, key=lambda s: s.get("id") or "")
    ids = {svc["id"] for svc in services if "id" in svc}

    nodes = []
    for svc in services:
        sid = svc.get("id")
        if not sid:
            continue
        category = svc.get("category", "unknown")
        # Normalize null-or-missing into "" so the JSON shape is
        # stable regardless of whether the loader emits the field
        # as None, missing, or a value. Without this, str(None)
        # leaks "None" into mainStat for port-less services and
        # YAML→NetBox round-trip differs purely on field presence.
        port = svc.get("port")
        purpose = (svc.get("purpose") or "").rstrip()
        nodes.append(
            {
                "id": sid,
                "title": svc.get("name") or sid,
                "subtitle": category,
                "mainStat": str(port) if port is not None else "",
                "secondaryStat": svc.get("host") or "",
                "color": CATEGORY_COLOR.get(category, "#9ca3af"),
                "arc__primary": 1.0,
                "detail__purpose": purpose,
                "detail__container": svc.get("container") or "",
                "detail__image": svc.get("image") or "",
            }
        )

    edges = []
    for svc in services:
        sid = svc.get("id")
        for dep in sorted(svc.get("depends_on", []) or []):
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
            self._write(
                200,
                {"ok": True, "source": CMDB_SOURCE, "registry": REGISTRY_PATH},
            )
            return
        try:
            services = load_services()
        except FileNotFoundError:
            self._write(503, {"error": "registry-not-found", "path": REGISTRY_PATH})
            return
        except SystemExit as e:
            # cmdb_source raises SystemExit on loader failure (token
            # missing, NetBox unreachable, YAML parse error)
            self._write(500, {"error": "loader-failure", "detail": str(e)})
            return

        nodes, edges = build_nodes_edges(services)
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
        f"[topology-api] listening on {LISTEN_HOST}:{LISTEN_PORT} "
        f"source={CMDB_SOURCE} registry={REGISTRY_PATH}",
        file=sys.stderr,
        flush=True,
    )
    httpd = ThreadingHTTPServer((LISTEN_HOST, LISTEN_PORT), TopologyHandler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
