"""Caddy external-routing layer → attach caddy_routes to merged registry.

Per Service Registry MVP spec §4.3. Two sources, in order of preference:
  1. Caddy admin API at http://localhost:2019/config/  (live truth)
  2. Caddyfile at docker/caddy/Caddyfile               (intent fallback)

Each route resolves to:
  - external_host  (e.g. "vault.internal")
  - upstream_host  (e.g. "host.docker.internal" or "vault-server")
  - upstream_port  (int)
  - tls            ("internal" for Caddy local CA, else None)
  - header_transforms (list[str], best-effort)
  - source         ("admin_api" | "caddyfile")

Attachment:
  - upstream "host.docker.internal:N" → match against any merged service
    whose addresses.host_mapped contains host_port=N
  - upstream "<name>:N"               → match against container_name=<name>
  - unmatched routes are returned as caddy_orphans
"""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CADDY_ADMIN = "http://localhost:2019/config/apps/http/servers/srv0/routes"
CADDYFILE = Path("/Users/admin/repos/integrated-ai-platform/docker/caddy/Caddyfile")


@dataclass
class CaddyRoute:
    external_host: str
    upstream_host: str
    upstream_port: int
    tls: str | None = "internal"  # all .internal sites use Caddy local CA
    header_transforms: list[str] = field(default_factory=list)
    source: str = "admin_api"


def _curl(url: str, timeout: int = 5) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["curl", "-sS", "--max-time", str(timeout), url],
            capture_output=True,
            text=True,
            timeout=timeout + 2,
            check=False,
        )
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return -1, ""
    except FileNotFoundError:
        return -2, ""


def _split_upstream(dial: str) -> tuple[str, int] | None:
    if ":" not in dial:
        return None
    host, _, port = dial.rpartition(":")
    try:
        return host, int(port)
    except ValueError:
        return None


def _walk_handles(handles: list[dict]) -> tuple[list[str], list[str]]:
    """Return (upstream_dials, header_transforms) found anywhere in handle tree."""
    dials: list[str] = []
    headers: list[str] = []
    for h in handles or []:
        if not isinstance(h, dict):
            continue
        if h.get("handler") == "subroute":
            for sub in h.get("routes", []) or []:
                d, hh = _walk_handles(sub.get("handle") or [])
                dials.extend(d)
                headers.extend(hh)
        elif h.get("handler") == "reverse_proxy":
            for up in h.get("upstreams", []) or []:
                if isinstance(up, dict) and up.get("dial"):
                    dials.append(up["dial"])
            # header transforms
            hdrs = h.get("headers") or {}
            req = (hdrs.get("request") or {})
            for key in ("set", "add", "delete"):
                v = req.get(key)
                if isinstance(v, dict):
                    for hk in v.keys():
                        headers.append(f"req.{key}:{hk}")
                elif isinstance(v, list):
                    for hk in v:
                        headers.append(f"req.{key}:{hk}")
    return dials, headers


def read_admin_api() -> list[CaddyRoute]:
    rc, out = _curl(CADDY_ADMIN)
    if rc != 0 or not out.strip():
        return []
    try:
        routes = json.loads(out)
    except json.JSONDecodeError:
        return []
    parsed: list[CaddyRoute] = []
    for r in routes or []:
        hosts: list[str] = []
        for m in r.get("match") or []:
            for h in m.get("host") or []:
                hosts.append(h)
        if not hosts:
            continue
        dials, headers = _walk_handles(r.get("handle") or [])
        for dial in dials:
            up = _split_upstream(dial)
            if not up:
                continue
            up_host, up_port = up
            for h in hosts:
                parsed.append(
                    CaddyRoute(
                        external_host=h,
                        upstream_host=up_host,
                        upstream_port=up_port,
                        header_transforms=list(headers),
                        source="admin_api",
                    )
                )
    return parsed


_SITE_OPEN = re.compile(r"^([a-z0-9.-]+\.internal)\s*\{")
_REVERSE_PROXY = re.compile(r"^\s*reverse_proxy\s+(\S+)")
_HEADER_UP = re.compile(r"^\s*header_up\s+(\S+)")


def read_caddyfile(path: Path = CADDYFILE) -> list[CaddyRoute]:
    """Tolerant Caddyfile parser — sufficient for our flat .internal layout."""
    if not path.exists():
        return []
    try:
        text = path.read_text()
    except OSError:
        return []
    out: list[CaddyRoute] = []
    current_host: str | None = None
    current_headers: list[str] = []
    pending_upstream: str | None = None
    depth = 0
    for raw in text.splitlines():
        line = raw.split("#", 1)[0]  # strip line-end comments
        stripped = line.strip()
        if not stripped:
            continue
        m = _SITE_OPEN.match(stripped)
        if m and depth == 0:
            current_host = m.group(1)
            current_headers = []
            pending_upstream = None
            depth = 1
            continue
        if current_host is None:
            continue
        # naive brace counting — sufficient for this flat file
        depth += stripped.count("{") - stripped.count("}")
        rp = _REVERSE_PROXY.match(line)
        if rp:
            pending_upstream = rp.group(1)
        hu = _HEADER_UP.match(line)
        if hu:
            current_headers.append(f"header_up:{hu.group(1)}")
        if depth <= 0:
            if pending_upstream:
                up = _split_upstream(pending_upstream)
                if up:
                    out.append(
                        CaddyRoute(
                            external_host=current_host,
                            upstream_host=up[0],
                            upstream_port=up[1],
                            header_transforms=list(current_headers),
                            source="caddyfile",
                        )
                    )
            current_host = None
            current_headers = []
            pending_upstream = None
            depth = 0
    return out


def read_routes() -> tuple[list[CaddyRoute], str]:
    """Prefer admin API; fall back to Caddyfile. Return (routes, source-used)."""
    api = read_admin_api()
    if api:
        return api, "admin_api"
    return read_caddyfile(), "caddyfile"


def attach_to_merged(
    merged: list[dict],
    routes: list[CaddyRoute],
    runtime_orphans: list[dict] | None = None,
) -> tuple[list[dict], list[dict]]:
    """Attach caddy_routes to merged service records.

    Match strategy (per spec §4.3):
      - "host.docker.internal:N" → service (merged or runtime-orphan) whose
        addresses.host_mapped contains host_port=N
      - "<container_name>:N"     → service (merged or runtime-orphan) whose
        container_name matches
      - else: caddy-route orphan (upstream is non-containerized or
        offline, e.g. ollama running natively on the host)

    runtime_orphans: containers running but not declared in compose
    (the orphans list returned by docker_inspector.merge_with_compose).
    Including them lets Caddy routes attach to e.g. grafana-obs, obot,
    uptime-kuma which have no compose intent record but ARE proxied.
    """
    candidates: list[dict] = list(merged) + list(runtime_orphans or [])

    by_host_port: dict[int, dict] = {}
    by_container: dict[str, dict] = {}
    for r in candidates:
        by_container[r["container_name"]] = r
        for hm in r.get("addresses", {}).get("host_mapped", []) or []:
            hp = hm.get("host_port")
            if hp is not None and hp not in by_host_port:
                by_host_port[hp] = r

    orphans: list[dict] = []
    for route in routes:
        target: dict | None = None
        if route.upstream_host == "host.docker.internal":
            target = by_host_port.get(route.upstream_port)
        else:
            target = by_container.get(route.upstream_host)
        route_dict = {
            "external_host": route.external_host,
            "upstream_host": route.upstream_host,
            "upstream_port": route.upstream_port,
            "tls": route.tls,
            "header_transforms": route.header_transforms,
            "source": route.source,
        }
        if target is None:
            orphans.append(route_dict)
            continue
        target.setdefault("addresses", {}).setdefault("caddy_routes", []).append(
            route_dict
        )
    return merged, orphans


if __name__ == "__main__":
    routes, src = read_routes()
    print(f"caddy routes: {len(routes)}  source: {src}")
    for r in routes[:5]:
        print(
            f"  {r.external_host:35s} → {r.upstream_host}:{r.upstream_port}  "
            f"hdrs={len(r.header_transforms)}"
        )
