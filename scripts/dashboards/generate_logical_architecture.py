#!/usr/bin/env python3
# D-17-17 — Logical service architecture dashboard generator.
#
# Reads ~/.platform-registry/inventory.json (D-17-29 substrate) and
# emits a static, self-contained HTML page grouping services by stack
# (swim lanes), with dependency arrows, health colour, hover detail,
# and an embedded `docker stats` snapshot taken at generation time.
#
# Inputs:
#   - $REGISTRY_DIR/inventory.json          (default: ~/.platform-registry)
#   - `docker stats --no-stream` (best-effort; missing → snapshot null)
#
# Output:
#   - docs/dashboards/logical-service-architecture.html  (default)
#
# Doctrine:
#   - Credential VALUES are never emitted. Only paths + fingerprints
#     (Finding ZZ).
#   - Pure-stdlib renderer (json, html, subprocess, datetime, pathlib).

from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REGISTRY_DIR = Path(os.environ.get("REGISTRY_DIR", str(Path.home() / ".platform-registry")))
DEFAULT_OUT = Path(__file__).resolve().parents[2] / "docs" / "dashboards" / "logical-service-architecture.html"


# ---------- data load ----------

def load_inventory() -> dict[str, Any]:
    return json.loads((REGISTRY_DIR / "inventory.json").read_text())


def load_last_refresh() -> dict[str, Any]:
    p = REGISTRY_DIR / "last-refresh.json"
    return json.loads(p.read_text()) if p.exists() else {}


def docker_stats_snapshot() -> dict[str, dict[str, str]]:
    """name -> {cpu, mem_usage, mem_pct}. Empty dict if docker missing."""
    try:
        out = subprocess.run(
            ["docker", "stats", "--no-stream", "--format",
             "{{.Name}}|{{.CPUPerc}}|{{.MemUsage}}|{{.MemPerc}}"],
            capture_output=True, text=True, timeout=20, check=False,
        )
        if out.returncode != 0:
            return {}
        snap: dict[str, dict[str, str]] = {}
        for line in out.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) != 4:
                continue
            name, cpu, mem, mem_pct = parts
            snap[name] = {"cpu": cpu, "mem": mem, "mem_pct": mem_pct}
        return snap
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return {}


# ---------- classification ----------

def health_class(svc: dict[str, Any]) -> str:
    state = svc.get("state") or {}
    status = state.get("status")
    health = state.get("health")
    if status == "running" and health == "healthy":
        return "ok"
    if status == "running" and (health is None or health == "starting"):
        return "warn"
    if status == "running":
        return "warn"
    return "down"


HEALTH_LABEL = {
    "ok": "running / healthy",
    "warn": "running (no healthcheck or starting)",
    "down": "not running",
}


# ---------- rendering ----------

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
.legend .down { background: #f85149; }
.summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px; margin-bottom: 24px;
}
.summary .card {
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    padding: 12px 14px;
}
.summary .num { font-size: 22px; font-weight: 600; }
.summary .lbl { font-size: 11px; color: #8b949e; text-transform: uppercase; letter-spacing: 0.06em; }
.stack {
    margin-bottom: 18px;
    background: #161b22; border: 1px solid #30363d; border-radius: 6px;
    padding: 12px 14px;
}
.stack-title {
    font-size: 13px; font-weight: 600; color: #58a6ff;
    text-transform: lowercase; margin-bottom: 8px;
    display: flex; align-items: baseline; gap: 8px;
}
.stack-title .count { color: #8b949e; font-size: 11px; font-weight: normal; }
.svc-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 6px;
}
.svc {
    background: #0d1117; border: 1px solid #30363d; border-radius: 4px;
    padding: 8px 10px; cursor: pointer; transition: border-color 120ms;
    font-size: 12px;
}
.svc:hover { border-color: #58a6ff; }
.svc.ok { border-left: 3px solid #2ea043; }
.svc.warn { border-left: 3px solid #d29922; }
.svc.down { border-left: 3px solid #f85149; }
.svc-name { font-weight: 600; color: #e6edf3; word-break: break-word; }
.svc-meta { color: #8b949e; font-size: 10px; margin-top: 3px; line-height: 1.4; }
.svc-stats { color: #79c0ff; font-size: 10px; margin-top: 2px; font-family: ui-monospace, monospace; }
#detail {
    position: fixed; right: 24px; top: 24px; width: 380px; max-height: 80vh;
    overflow-y: auto;
    background: #161b22; border: 1px solid #58a6ff; border-radius: 6px;
    padding: 16px; box-shadow: 0 8px 32px rgba(0,0,0,0.5);
    display: none; font-size: 12px; z-index: 100;
}
#detail.show { display: block; }
#detail h2 { margin: 0 0 8px 0; font-size: 14px; }
#detail .close { float: right; cursor: pointer; color: #8b949e; }
#detail h3 { margin: 12px 0 4px 0; font-size: 11px; text-transform: uppercase; color: #8b949e; letter-spacing: 0.06em; }
#detail ul { margin: 4px 0; padding-left: 16px; }
#detail code { background: #0d1117; padding: 1px 4px; border-radius: 2px; font-size: 11px; word-break: break-all; }
.dep-arrow { color: #58a6ff; font-size: 10px; margin-top: 2px; }
section.orphans .stack { border-color: #d29922; }
section.orphans .stack-title { color: #d29922; }
.footer { margin-top: 32px; padding-top: 16px; border-top: 1px solid #30363d; font-size: 11px; color: #8b949e; }
"""

JS = r"""
const SVC = window.__SVC__ || {};
function showDetail(id) {
    const s = SVC[id];
    if (!s) return;
    const box = document.getElementById('detail');
    let html = '<span class="close" onclick="hideDetail()">&times;</span>';
    html += '<h2>' + escapeHtml(s.service_id) + '</h2>';
    html += '<div style="color:#8b949e;font-size:11px;margin-bottom:6px;">stack: <code>' + escapeHtml(s.stack || '-') + '</code></div>';
    html += '<div>image: <code>' + escapeHtml(s.image || '-') + '</code></div>';
    html += '<h3>State</h3>';
    html += '<div>status: <code>' + escapeHtml(s.state.status || '-') + '</code></div>';
    html += '<div>health: <code>' + escapeHtml(String(s.state.health || 'none')) + '</code></div>';
    html += '<div>restarts: <code>' + (s.state.restart_count || 0) + '</code></div>';
    if (s.stats) {
        html += '<h3>Live (snapshot)</h3>';
        html += '<div>CPU: <code>' + escapeHtml(s.stats.cpu) + '</code></div>';
        html += '<div>MEM: <code>' + escapeHtml(s.stats.mem) + '</code> (<code>' + escapeHtml(s.stats.mem_pct) + '</code>)</div>';
    }
    if (s.internal && s.internal.length) {
        html += '<h3>Internal addresses</h3><ul>';
        for (const a of s.internal) {
            html += '<li><code>' + escapeHtml(a.ip || '?') + ':' + (a.port_listen || '?') + '</code> on <code>' + escapeHtml(a.network) + '</code></li>';
        }
        html += '</ul>';
    }
    if (s.host_mapped && s.host_mapped.length) {
        html += '<h3>Host ports</h3><ul>';
        for (const h of s.host_mapped) {
            html += '<li><code>' + (h.host_port || '?') + '→' + (h.container_port || '?') + '/' + escapeHtml(h.protocol) + '</code></li>';
        }
        html += '</ul>';
    }
    if (s.caddy_routes && s.caddy_routes.length) {
        html += '<h3>Caddy routes</h3><ul>';
        for (const r of s.caddy_routes) {
            html += '<li><code>' + escapeHtml(r.external_host) + '</code> → <code>' + escapeHtml(r.upstream_host) + ':' + r.upstream_port + '</code></li>';
        }
        html += '</ul>';
    }
    if (s.depends_on && s.depends_on.length) {
        html += '<h3>Depends on</h3><ul>';
        for (const d of s.depends_on) html += '<li><code>' + escapeHtml(d) + '</code></li>';
        html += '</ul>';
    }
    if (s.depended_on_by && s.depended_on_by.length) {
        html += '<h3>Depended on by</h3><ul>';
        for (const d of s.depended_on_by) html += '<li><code>' + escapeHtml(d) + '</code></li>';
        html += '</ul>';
    }
    if (s.credentials_meta && s.credentials_meta.length) {
        html += '<h3>Credentials (paths only — Finding ZZ doctrine)</h3><ul>';
        for (const c of s.credentials_meta) {
            html += '<li><code>' + escapeHtml(c.basename) + '</code> mode=<code>' + escapeHtml(c.mode) + '</code> fp=<code>' + escapeHtml(c.fingerprint || '?') + '</code></li>';
        }
        html += '</ul>';
    }
    box.innerHTML = html;
    box.classList.add('show');
}
function hideDetail() { document.getElementById('detail').classList.remove('show'); }
function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
document.addEventListener('keydown', (e) => { if (e.key === 'Escape') hideDetail(); });
"""


def render_service_card(svc: dict[str, Any], stats: dict[str, dict[str, str]]) -> str:
    cls = health_class(svc)
    sid = svc["service_id"]
    image = (svc.get("image") or "?").rsplit("/", 1)[-1].split(":")[0]
    cname = svc.get("container_name") or sid
    stat = stats.get(cname)

    stat_line = ""
    if stat:
        stat_line = (
            f'<div class="svc-stats">cpu {html.escape(stat["cpu"])}'
            f' · mem {html.escape(stat["mem_pct"])}</div>'
        )

    deps = svc.get("depends_on") or []
    dep_line = ""
    if deps:
        n = len(deps)
        dep_line = f'<div class="dep-arrow">→ {n} dep{"s" if n != 1 else ""}</div>'

    return (
        f'<div class="svc {cls}" onclick="showDetail({json.dumps(sid)})">'
        f'  <div class="svc-name">{html.escape(sid)}</div>'
        f'  <div class="svc-meta">{html.escape(image)}</div>'
        f'{stat_line}{dep_line}'
        f'</div>'
    )


def render_stack(name: str, svcs: list[dict[str, Any]], stats: dict[str, dict[str, str]]) -> str:
    cards = "\n".join(render_service_card(s, stats) for s in sorted(svcs, key=lambda x: x["service_id"]))
    return (
        f'<div class="stack">'
        f'  <div class="stack-title">{html.escape(name)} <span class="count">({len(svcs)})</span></div>'
        f'  <div class="svc-grid">{cards}</div>'
        f'</div>'
    )


def build_svc_index(inv: dict[str, Any], stats: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    """JS-side lookup keyed by service_id; only the fields the panel renders."""
    idx: dict[str, dict[str, Any]] = {}
    for svc in inv["services"] + inv.get("runtime_orphans", []):
        sid = svc["service_id"]
        cname = svc.get("container_name") or sid
        addrs = svc.get("addresses") or {}
        idx[sid] = {
            "service_id": sid,
            "stack": svc.get("stack"),
            "image": svc.get("image"),
            "state": svc.get("state") or {},
            "internal": addrs.get("internal") or [],
            "host_mapped": addrs.get("host_mapped") or [],
            "caddy_routes": addrs.get("caddy_routes") or [],
            "depends_on": svc.get("depends_on") or [],
            "depended_on_by": svc.get("depended_on_by") or [],
            "stats": stats.get(cname),
            "credentials_meta": [
                {"basename": c.get("basename"), "mode": c.get("mode"), "fingerprint": c.get("fingerprint")}
                for c in (svc.get("credentials") or {}).get("files", [])
            ],
        }
    return idx


def render(inv: dict[str, Any], refresh_meta: dict[str, Any], stats: dict[str, dict[str, str]]) -> str:
    services = inv["services"]
    orphans = inv.get("runtime_orphans", [])
    caddy_orphans = inv.get("caddy_orphans", [])

    by_stack: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for s in services:
        by_stack[s.get("stack") or "<unknown>"].append(s)

    health_counts = {"ok": 0, "warn": 0, "down": 0}
    for s in services:
        health_counts[health_class(s)] += 1

    stack_blocks = "\n".join(render_stack(name, svcs, stats) for name, svcs in sorted(by_stack.items()))

    orphan_block = ""
    if orphans:
        orphan_block = (
            '<section class="orphans"><h2 style="font-size:14px;color:#d29922;">Runtime orphans '
            f'<span style="color:#8b949e;font-weight:normal;font-size:12px;">'
            f'(running but not in any compose intent file — {len(orphans)})</span></h2>'
            + render_stack("orphans", orphans, stats) + "</section>"
        )

    caddy_orphan_block = ""
    if caddy_orphans:
        items = "".join(
            f'<li><code>{html.escape(r["external_host"])}</code> → <code>{html.escape(r["upstream_host"])}:{r["upstream_port"]}</code></li>'
            for r in caddy_orphans
        )
        caddy_orphan_block = (
            f'<section><h2 style="font-size:14px;color:#d29922;">Caddy orphans '
            f'<span style="color:#8b949e;font-weight:normal;font-size:12px;">'
            f'({len(caddy_orphans)} routes pointing at unknown upstreams)</span></h2>'
            f'<ul style="font-size:12px;">{items}</ul></section>'
        )

    counts = refresh_meta.get("counts", {})
    summary = "".join(
        f'<div class="card"><div class="num">{v}</div><div class="lbl">{k.replace("_", " ")}</div></div>'
        for k, v in counts.items()
    )

    generated_at = refresh_meta.get("generated_at", "?")
    elapsed = refresh_meta.get("elapsed_seconds", "?")
    rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    svc_index = build_svc_index(inv, stats)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Logical Service Architecture · Integrated AI Platform</title>
<style>{CSS}</style>
</head>
<body>
<header>
  <h1>Logical Service Architecture</h1>
  <div class="meta">
    Source: <code>~/.platform-registry/inventory.json</code> (D-17-29 substrate) ·
    Registry refreshed: <code>{html.escape(generated_at)}</code> ({elapsed}s) ·
    Page rendered: <code>{rendered_at}</code> ·
    <code>docker stats</code> snapshot: {"embedded" if stats else "<em>unavailable</em>"}
  </div>
  <div class="legend">
    <span><span class="swatch ok"></span>{health_counts["ok"]} running / healthy</span>
    <span><span class="swatch warn"></span>{health_counts["warn"]} running (no/starting healthcheck)</span>
    <span><span class="swatch down"></span>{health_counts["down"]} not running (exited / restarting / absent)</span>
  </div>
</header>

<div class="summary">{summary}</div>

<section><h2 style="font-size:14px;">Services by stack</h2>
{stack_blocks}
</section>

{orphan_block}
{caddy_orphan_block}

<div class="footer">
  Click any service for full detail. Esc to dismiss. Doctrine: credential
  values never emitted (Finding ZZ); paths + fingerprints only. Generator:
  <code>scripts/dashboards/generate_logical_architecture.py</code>.
</div>

<div id="detail"></div>

<script>window.__SVC__ = {json.dumps(svc_index)};</script>
<script>{JS}</script>
</body>
</html>
"""
    return page


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="Output HTML path")
    ap.add_argument("--no-stats", action="store_true", help="Skip docker stats snapshot")
    args = ap.parse_args()

    inv = load_inventory()
    refresh_meta = load_last_refresh()
    stats = {} if args.no_stats else docker_stats_snapshot()

    html_doc = render(inv, refresh_meta, stats)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html_doc)
    print(f"wrote {args.out} ({len(html_doc):,} bytes)")
    print(f"  services={len(inv['services'])} orphans={len(inv.get('runtime_orphans', []))} stats={'yes' if stats else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
