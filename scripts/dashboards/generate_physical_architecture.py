#!/usr/bin/env python3
"""
D-17-18 — Physical architecture visualization generator.

Sister deliverable to D-17-17 (logical service architecture). Renders
hardware nodes, network paths (LAN / TB5 / VPN), and storage paths
as a static HTML dashboard. Visual style matches D-17-17 for demo
coherence.

Hardware facts are CLAUDE.md + architecture-facts/exo-cluster.md +
opnsense-dns-authority.md authoritative; network reachability is
probed at generation time. Where Mac Mini service registry data
exists (~/.platform-registry/inventory.json), per-node service
counts are linked to architecture.internal.

Run:
    python3 scripts/dashboards/generate_physical_architecture.py

Default output: docs/dashboards/physical-architecture.html
"""
import argparse
import datetime as dt
import html
import json
import os
import platform
import socket
import subprocess
import sys
from pathlib import Path

REGISTRY = Path.home() / ".platform-registry" / "inventory.json"
LAST_REFRESH = Path.home() / ".platform-registry" / "last-refresh.json"

NODES = [
    {
        "id": "mac-mini",
        "name": "Mac Mini",
        "hostname": "mac-mini.internal",
        "ip": "192.168.10.145",
        "role": "Control plane · orchestration · services",
        "spec": "Apple M4 Pro · 48 GB unified memory",
        "os": None,  # filled at runtime from sw_vers when self
        "status": "active",
        "services_link": "https://architecture.internal/",
        "self": True,
        "notes": [
            "Primary docker host (76 services / 84 containers per registry)",
            "Vault data + Restic source",
            "exo single-node coordinator (D-17-30 demo path)",
        ],
    },
    {
        "id": "mac-studio",
        "name": "Mac Studio",
        "hostname": "mac-studio.internal",
        "ip": "192.168.10.142",
        "role": "Compute node · exo single-node tonight",
        "spec": "Apple M3 Ultra · 96 GB unified memory",
        "os": "macOS (D-17-15 Day-1 baseline)",
        "status": "active",
        "services_link": None,
        "self": False,
        "notes": [
            "Multi-node exo upstream-blocked (D-17-25 Findings U+V)",
            "TB5 static link-local: 169.254.35.30",
            "JACCL coordinator: 192.168.10.142:52617",
        ],
    },
    {
        "id": "threadripper",
        "name": "Threadripper",
        "hostname": "(pending)",
        "ip": "(pending)",
        "role": "GPU compute · FUTURE",
        "spec": "AMD Threadripper + NVIDIA RTX 4070 · motherboard pending",
        "os": "Linux (planned)",
        "status": "pending",
        "services_link": None,
        "self": False,
        "notes": [
            "Portability target (CLAUDE.md heterogeneous-architecture rule)",
            "Per-host vault config exists: config/vault-configs/vault-config-linux.hcl",
        ],
    },
    {
        "id": "qnap",
        "name": "QNAP NAS",
        "hostname": "qnap.internal",
        "ip": "192.168.10.201",
        "role": "Backup target · media storage",
        "spec": "QNAP appliance",
        "os": "QTS",
        "status": "active",
        "services_link": None,
        "self": False,
        "notes": [
            "Restic nightly backup destination",
            "Vault audit log archive (30-day local → QNAP)",
            "MinIO + arr-stack media library",
        ],
    },
    {
        "id": "homeassistant",
        "name": "Home Assistant",
        "hostname": "homeassistant.internal",
        "ip": "192.168.10.141",
        "role": "Smart home (Phase 13 Block 3)",
        "spec": "Intel NUC",
        "os": "Home Assistant OS",
        "status": "active",
        "services_link": None,
        "self": False,
        "notes": [
            "Reverse-proxied via Caddy (LAN-direct upstream)",
            "Docker Desktop NAT requires X-Forwarded-* stripping",
        ],
    },
    {
        "id": "opnsense",
        "name": "OPNsense",
        "hostname": "opnsense.internal",
        "ip": "192.168.10.1",
        "role": "Router · firewall · DNS authority",
        "spec": "Network appliance",
        "os": "OPNsense 26.1.6",
        "status": "active",
        "services_link": None,
        "self": False,
        "notes": [
            "DNS authority for *.internal (Dnsmasq)",
            "KI-009 + D-17-21: DNS state audit pending",
        ],
    },
]

LINKS = [
    {
        "id": "lan-mini-studio",
        "from": "mac-mini",
        "to": "mac-studio",
        "kind": "lan",
        "label": "LAN · 192.168.10.0/24 · 1 GbE",
    },
    {
        "id": "tb5-mini-studio",
        "from": "mac-mini",
        "to": "mac-studio",
        "kind": "tb5",
        "label": "TB5 bridge · 169.254.0.0/16 · 80 Gbps",
    },
    {
        "id": "lan-mini-qnap",
        "from": "mac-mini",
        "to": "qnap",
        "kind": "lan",
        "label": "LAN · Restic backup",
    },
    {
        "id": "lan-mini-ha",
        "from": "mac-mini",
        "to": "homeassistant",
        "kind": "lan",
        "label": "LAN · Caddy reverse-proxy",
    },
    {
        "id": "lan-mini-opnsense",
        "from": "mac-mini",
        "to": "opnsense",
        "kind": "lan",
        "label": "LAN · default route + DNS",
    },
    {
        "id": "lan-studio-opnsense",
        "from": "mac-studio",
        "to": "opnsense",
        "kind": "lan",
        "label": "LAN · default route",
    },
    {
        "id": "vpn-headscale",
        "from": "mac-mini",
        "to": "threadripper",
        "kind": "vpn",
        "label": "Headscale overlay (when TR online)",
    },
]

STORAGE_PATHS = [
    {
        "name": "Vault data",
        "source": "Mac Mini /vault/data",
        "destination": "QNAP via Restic (nightly)",
        "auth": "backup AppRole",
        "retention": "Restic policy (offsite)",
    },
    {
        "name": "Vault audit log",
        "source": "Mac Mini /vault/logs/audit.log",
        "destination": "QNAP archive (cron, nightly)",
        "auth": "(file-level)",
        "retention": "30-day local · indefinite QNAP",
    },
    {
        "name": "Docker volumes",
        "source": "Mac Mini Docker Desktop VM",
        "destination": "QNAP via Restic (nightly)",
        "auth": "backup AppRole",
        "retention": "Restic policy",
    },
    {
        "name": "Media library",
        "source": "arr-stack (sonarr/radarr/prowlarr)",
        "destination": "QNAP NAS shares",
        "auth": "(SMB/NFS)",
        "retention": "indefinite",
    },
    {
        "name": "HF model cache",
        "source": "Mac Mini ~/.cache/huggingface",
        "destination": "(local-only — Mac Studio has separate cache)",
        "auth": "(file-level)",
        "retention": "indefinite",
    },
]


def run(cmd: list[str], timeout: float = 5.0) -> tuple[int, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, (r.stdout or r.stderr).strip()
    except Exception as e:
        return -1, str(e)


def ping(ip: str) -> dict:
    if ip.startswith("(pending"):
        return {"reachable": False, "ms": None, "note": "pending hardware"}
    # Self IP: ping doesn't always work on macOS for own bound IP. Treat as reachable.
    rc_addr, addrs = run(["ifconfig"], timeout=2.0)
    if rc_addr == 0 and f"inet {ip} " in addrs:
        return {"reachable": True, "ms": 0.0, "note": "self"}
    rc, out = run(["ping", "-c", "1", "-W", "500", "-t", "1", ip], timeout=2.0)
    if rc == 0:
        # Parse "time=X.X ms"
        for tok in out.split():
            if tok.startswith("time="):
                try:
                    return {
                        "reachable": True,
                        "ms": float(tok.split("=", 1)[1]),
                        "note": None,
                    }
                except ValueError:
                    pass
        return {"reachable": True, "ms": None, "note": None}
    return {"reachable": False, "ms": None, "note": "no icmp response"}


def detect_self_os() -> str:
    rc, out = run(["sw_vers"], timeout=2.0)
    if rc != 0:
        return platform.platform()
    name, ver, build = "macOS", "?", "?"
    for line in out.splitlines():
        if line.startswith("ProductName:"):
            name = line.split(":", 1)[1].strip()
        elif line.startswith("ProductVersion:"):
            ver = line.split(":", 1)[1].strip()
        elif line.startswith("BuildVersion:"):
            build = line.split(":", 1)[1].strip()
    return f"{name} {ver} (build {build})"


def detect_self_tb5_ips() -> list[str]:
    rc, out = run(["ifconfig"], timeout=2.0)
    if rc != 0:
        return []
    ips = []
    for line in out.splitlines():
        line = line.strip()
        if line.startswith("inet 169.254."):
            ip = line.split()[1]
            ips.append(ip)
    return ips


def load_registry() -> dict:
    if REGISTRY.exists():
        return json.loads(REGISTRY.read_text())
    return {}


def load_last_refresh() -> dict:
    if LAST_REFRESH.exists():
        return json.loads(LAST_REFRESH.read_text())
    return {}


def render_node_card(node: dict, probe: dict) -> str:
    status_class = {
        "active": "ok" if probe["reachable"] else "warn",
        "pending": "pending",
    }.get(node["status"], "warn")
    badge = ""
    if node["status"] == "pending":
        badge = '<span class="badge pending">pending hardware</span>'
    elif probe["reachable"]:
        ms_str = f'{probe["ms"]:.1f} ms' if probe["ms"] is not None else "ok"
        badge = f'<span class="badge ok">{html.escape(ms_str)}</span>'
    else:
        badge = '<span class="badge warn">unreachable</span>'

    services_html = ""
    if node.get("services_link"):
        services_html = (
            f'<a class="srv-link" href="{html.escape(node["services_link"])}" '
            'target="_blank" rel="noopener">→ logical services</a>'
        )

    notes_html = ""
    if node.get("notes"):
        items = "".join(f"<li>{html.escape(n)}</li>" for n in node["notes"])
        notes_html = f"<ul class='notes'>{items}</ul>"

    return f"""
<div class="node {status_class}" id="node-{html.escape(node['id'])}">
  <div class="node-head">
    <div class="node-name">{html.escape(node['name'])}</div>
    {badge}
  </div>
  <div class="node-role">{html.escape(node['role'])}</div>
  <div class="node-meta">
    <code>{html.escape(node['hostname'])}</code> · <code>{html.escape(node['ip'])}</code>
  </div>
  <div class="node-spec">{html.escape(node['spec'])}</div>
  <div class="node-os">{html.escape(node['os'] or 'unknown')}</div>
  {services_html}
  {notes_html}
</div>"""


def render_link_row(link: dict, by_id: dict) -> str:
    a = by_id[link["from"]]
    b = by_id[link["to"]]
    kind_label = {
        "lan": "LAN",
        "tb5": "TB5",
        "vpn": "VPN",
    }.get(link["kind"], link["kind"])
    return (
        f'<tr class="link-{link["kind"]}">'
        f'<td><span class="kind-badge {link["kind"]}">{kind_label}</span></td>'
        f'<td><code>{html.escape(a["name"])}</code></td>'
        f'<td>↔</td>'
        f'<td><code>{html.escape(b["name"])}</code></td>'
        f'<td>{html.escape(link["label"])}</td>'
        "</tr>"
    )


def render_storage_row(s: dict) -> str:
    return (
        "<tr>"
        f'<td><strong>{html.escape(s["name"])}</strong></td>'
        f'<td>{html.escape(s["source"])}</td>'
        f'<td>→</td>'
        f'<td>{html.escape(s["destination"])}</td>'
        f'<td><code>{html.escape(s["auth"])}</code></td>'
        f'<td>{html.escape(s["retention"])}</td>'
        "</tr>"
    )


CSS = """
* { box-sizing: border-box; }
body {
    background: #0e1117;
    color: #e6edf3;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", system-ui, sans-serif;
    margin: 0;
    padding: 24px;
}
header {
    border-bottom: 1px solid #30363d;
    padding-bottom: 16px;
    margin-bottom: 24px;
}
h1 { margin: 0 0 8px 0; font-size: 22px; font-weight: 600; }
h2 { font-size: 14px; margin: 24px 0 10px 0; color: #c9d1d9; }
.meta { font-size: 12px; color: #8b949e; }
.meta code { background: #161b22; padding: 2px 6px; border-radius: 3px; }
.legend {
    display: flex; gap: 16px; margin: 12px 0; font-size: 12px; color: #8b949e;
    flex-wrap: wrap;
}
.legend .swatch {
    display: inline-block; width: 10px; height: 10px; margin-right: 4px;
    border-radius: 50%; vertical-align: middle;
}
.legend .ok { background: #2ea043; }
.legend .warn { background: #d29922; }
.legend .pending { background: #6e7681; }
.legend .lan { display: inline-block; width: 18px; height: 2px; background: #58a6ff; margin-right: 4px; vertical-align: middle; }
.legend .tb5 { display: inline-block; width: 18px; height: 2px; background: #d2a8ff; margin-right: 4px; vertical-align: middle; border-top: 1px dashed #d2a8ff; background: transparent; }
.legend .vpn { display: inline-block; width: 18px; height: 2px; background: transparent; border-top: 2px dotted #f0883e; margin-right: 4px; vertical-align: middle; }

.summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px; margin-bottom: 24px;
}
.summary .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    padding: 12px 14px;
}
.summary .num { font-size: 22px; font-weight: 600; }
.summary .lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; }

.nodes-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 14px;
    margin-bottom: 28px;
}
.node {
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    padding: 14px 16px;
}
.node.ok { border-left: 3px solid #2ea043; }
.node.warn { border-left: 3px solid #d29922; }
.node.pending { border-left: 3px solid #6e7681; opacity: 0.78; }
.node-head {
    display: flex; align-items: baseline; justify-content: space-between;
    margin-bottom: 4px;
}
.node-name { font-size: 14px; font-weight: 600; color: #e6edf3; }
.node-role { font-size: 11px; color: #58a6ff; margin-bottom: 8px; text-transform: lowercase; }
.node-meta { font-size: 11px; color: #8b949e; margin-bottom: 6px; }
.node-meta code { background: #0d1117; padding: 1px 5px; border-radius: 2px; font-size: 10px; }
.node-spec { font-size: 11px; color: #c9d1d9; margin-bottom: 2px; }
.node-os { font-size: 10px; color: #8b949e; font-family: ui-monospace, monospace; margin-bottom: 8px; }
.srv-link {
    display: inline-block; font-size: 11px; color: #79c0ff;
    text-decoration: none; margin-bottom: 6px;
}
.srv-link:hover { text-decoration: underline; }
.notes {
    margin: 6px 0 0 0; padding-left: 16px;
    font-size: 11px; color: #8b949e; line-height: 1.5;
}
.badge {
    font-size: 10px; padding: 2px 7px; border-radius: 10px;
    font-family: ui-monospace, monospace;
}
.badge.ok { background: rgba(46,160,67,0.15); color: #56d364; }
.badge.warn { background: rgba(210,153,34,0.15); color: #e3b341; }
.badge.pending { background: rgba(110,118,129,0.15); color: #8b949e; }

table.links, table.storage {
    width: 100%; border-collapse: collapse; margin-bottom: 24px;
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    overflow: hidden;
}
table.links th, table.storage th {
    text-align: left; padding: 8px 12px; background: #0d1117;
    font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em;
    font-weight: 600; border-bottom: 1px solid #30363d;
}
table.links td, table.storage td {
    padding: 8px 12px; font-size: 12px; border-bottom: 1px solid #21262d;
    color: #c9d1d9;
}
table.links tr:last-child td, table.storage tr:last-child td { border-bottom: none; }
table.links code, table.storage code {
    background: #0d1117; padding: 1px 5px; border-radius: 2px;
    font-size: 11px; color: #e6edf3;
}
.kind-badge {
    display: inline-block; padding: 2px 7px; border-radius: 3px;
    font-size: 10px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kind-badge.lan { background: rgba(88,166,255,0.15); color: #79c0ff; }
.kind-badge.tb5 { background: rgba(210,168,255,0.15); color: #d2a8ff; }
.kind-badge.vpn { background: rgba(240,136,62,0.15); color: #f0883e; }

.footer {
    margin-top: 32px; padding-top: 16px; border-top: 1px solid #30363d;
    font-size: 11px; color: #8b949e; line-height: 1.6;
}
.footer code { background: #161b22; padding: 1px 5px; border-radius: 2px; }
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--output",
        default=str(
            Path(__file__).resolve().parent.parent.parent
            / "docs"
            / "dashboards"
            / "physical-architecture.html"
        ),
    )
    args = ap.parse_args()

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Probe each node
    probes = {n["id"]: ping(n["ip"]) for n in NODES}

    # Self-detect Mac Mini OS
    self_os = detect_self_os()
    self_tb5 = detect_self_tb5_ips()
    for n in NODES:
        if n.get("self"):
            n["os"] = self_os
            if self_tb5:
                n["notes"] = list(n.get("notes", [])) + [
                    f"TB5 bridge link-local: {', '.join(self_tb5)} (drifts across reboots)"
                ]

    registry = load_registry()
    last_refresh = load_last_refresh()
    counts = last_refresh.get("counts", {})

    by_id = {n["id"]: n for n in NODES}

    active = sum(1 for n in NODES if n["status"] == "active")
    pending = sum(1 for n in NODES if n["status"] == "pending")
    reachable = sum(1 for p in probes.values() if p["reachable"])

    nodes_html = "\n".join(render_node_card(n, probes[n["id"]]) for n in NODES)
    links_html = "\n".join(render_link_row(l, by_id) for l in LINKS)
    storage_html = "\n".join(render_storage_row(s) for s in STORAGE_PATHS)

    rendered_at = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    refreshed_at = last_refresh.get("generated_at", "(unknown)")
    refresh_elapsed = last_refresh.get("elapsed_seconds", "?")

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Physical Architecture · Integrated AI Platform</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Physical Architecture</h1>
  <div class="meta">
    Hardware nodes from <code>CLAUDE.md</code> + <code>docs/architecture-facts/</code> ·
    Reachability probed: <code>{rendered_at}</code> ·
    Service registry refresh: <code>{html.escape(str(refreshed_at))}</code> ({refresh_elapsed}s) ·
    Sister view: <a href="https://architecture.internal/" style="color:#79c0ff;">logical services</a>
  </div>
  <div class="legend">
    <span><span class="swatch ok"></span>{reachable} reachable</span>
    <span><span class="swatch warn"></span>{active - reachable} active but unreachable</span>
    <span><span class="swatch pending"></span>{pending} pending hardware</span>
    <span><span class="lan"></span>LAN</span>
    <span><span class="tb5"></span>TB5 bridge</span>
    <span><span class="vpn"></span>VPN overlay</span>
  </div>
</header>

<div class="summary">
  <div class="card"><div class="num">{len(NODES)}</div><div class="lbl">physical nodes</div></div>
  <div class="card"><div class="num">{active}</div><div class="lbl">active</div></div>
  <div class="card"><div class="num">{reachable}</div><div class="lbl">reachable now</div></div>
  <div class="card"><div class="num">{pending}</div><div class="lbl">pending hardware</div></div>
  <div class="card"><div class="num">{counts.get('merged_services', '–')}</div><div class="lbl">services on Mac Mini</div></div>
  <div class="card"><div class="num">{len(LINKS)}</div><div class="lbl">network links</div></div>
  <div class="card"><div class="num">{len(STORAGE_PATHS)}</div><div class="lbl">storage paths</div></div>
</div>

<h2>Nodes</h2>
<div class="nodes-grid">
{nodes_html}
</div>

<h2>Network paths</h2>
<table class="links">
  <thead>
    <tr><th>kind</th><th>from</th><th></th><th>to</th><th>detail</th></tr>
  </thead>
  <tbody>
{links_html}
  </tbody>
</table>

<h2>Storage paths</h2>
<table class="storage">
  <thead>
    <tr><th>name</th><th>source</th><th></th><th>destination</th><th>auth</th><th>retention</th></tr>
  </thead>
  <tbody>
{storage_html}
  </tbody>
</table>

<div class="footer">
Generated by <code>scripts/dashboards/generate_physical_architecture.py</code> ·
Hardware facts: <code>CLAUDE.md</code> hardware block + <code>docs/architecture-facts/exo-cluster.md</code>
+ <code>docs/architecture-facts/opnsense-dns-authority.md</code> ·
Reachability via <code>ping -c1 -W500 -t1</code> at render time ·
Service-count cross-link is to <code>architecture.internal</code> (D-17-17 sister deliverable) ·
D-17-18 close · Phase 17.
</div>
</body>
</html>
"""
    out_path.write_text(page)
    size = out_path.stat().st_size
    print(f"wrote {out_path} ({size} bytes)")
    print(f"  nodes={len(NODES)} active={active} reachable={reachable} pending={pending}")
    print(f"  links={len(LINKS)} storage_paths={len(STORAGE_PATHS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
