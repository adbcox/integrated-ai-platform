# D-17-18 — Physical Architecture dashboard smoke test

**Date:** 2026-05-03
**Sister deliverable:** D-17-17 (logical service architecture at `architecture.internal`)
**Artifact:** `docs/dashboards/physical-architecture.html` (13,483 bytes)

## Verified end-to-end

```
$ curl -s -o /dev/null -w "HTTP %{http_code}\n" \
    -H "Host: physical-architecture.internal" http://localhost/
HTTP 308

$ curl -skL --resolve physical-architecture.internal:443:127.0.0.1 \
    -o /tmp/phys-test.html \
    -w "HTTPS %{http_code} | size=%{size_download} | url=%{url_effective}\n" \
    https://physical-architecture.internal/
HTTPS 200 | size=13483 | url=https://physical-architecture.internal/physical-architecture.html

$ head -5 /tmp/phys-test.html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Physical Architecture · Integrated AI Platform</title>
```

Path: client → Caddy :443 (auto-TLS via internal CA) → root redirect to
`/physical-architecture.html` → `host.docker.internal:8765` (host-side
`python3 -m http.server` reading `docs/dashboards/`, shared with D-17-17).

## Generator output

```
$ python3 scripts/dashboards/generate_physical_architecture.py
wrote .../docs/dashboards/physical-architecture.html (13483 bytes)
  nodes=6 active=5 reachable=5 pending=1
  links=7 storage_paths=5
```

## Inventory rendered

- **6 nodes:** Mac Mini (.145, M4 Pro 48 GB, control plane, 76 services link),
  Mac Studio (.142, M3 Ultra 96 GB, exo single-node), Threadripper (pending
  hardware — no IP/specs invented), QNAP NAS (.201, Restic target),
  Home Assistant (.141, Intel NUC), OPNsense (.1, OPNsense 26.1.6).
- **5/5 active reachable** (ping at render time; self-host treated reachable).
- **7 network links:** LAN (5), TB5 bridge (1), VPN overlay placeholder (1, Threadripper future).
- **5 storage paths:** Vault data, Vault audit log, Docker volumes, Media library, HF model cache.

## Hardware-fact source map

- CLAUDE.md hardware block (Mac Mini M4 Pro 48 GB / .145; Mac Studio M3 Ultra 96 GB; QNAP backup target).
- `docs/architecture-facts/exo-cluster.md` (Mac Studio LAN IP `.142` confirmed via JACCL coordinator
  `MLX_JACCL_COORDINATOR: 192.168.10.142:52617`; TB5 link-locals; Studio static `169.254.35.30`).
- `docs/architecture-facts/opnsense-dns-authority.md` (OPNsense at `.1` running 26.1.6).
- `docker/caddy/Caddyfile` `homeassistant.internal` block (HA at `.141`, Intel NUC).
- Ping reachability probed at generation time (render-fresh).
- Mac Mini self-detected: `sw_vers` for OS, `ifconfig` for TB5 bridge IPs.

## CLAUDE.md drift surfaced

CLAUDE.md hardware block (line 6, post-D-17-24 rewrite) says
`Mac Studio M3 Ultra 96 GB at 192.168.10.146`. Actual is `.142`,
confirmed by:
- `arp -a` shows `192.168.10.142 at 1c:1d:d3:e1:40:cd`
- `ping 192.168.10.142` → 1.1 ms response; `.146` → no response
- `exo-cluster.md` references `192.168.10.142:52617` for JACCL coordinator

D-17-24 (CLAUDE.md staleness sweep) updated the hardware block but reused
the original `.146` value. **Recommend correcting CLAUDE.md to `.142`** as
a follow-up (one-line edit; not blocking D-17-18 close).

## Operational notes

- **Refresh:** re-run `python3 scripts/dashboards/generate_physical_architecture.py`
  whenever hardware inventory or service registry changes. The generator
  re-probes reachability + re-reads `~/.platform-registry/last-refresh.json`
  on every run, so output is current at render time.
- **Static server:** reuses the same `python3 -m http.server 8765` from
  D-17-17 (PID 33623 at smoke time).
- **Caddyfile site:** `physical-architecture.internal` block at lines
  256-266. `docker restart caddy` required after edit (same Docker
  Desktop VirtioFS bind-mount cache stall observed in D-17-17;
  documented pattern).
- **DNS parity:** new site is missing from Dnsmasq (same gap as the other
  31 sites — structurally rolled up into D-17-21 / KI-009).

## Sister-view linkage

The Mac Mini node card on this dashboard contains a `→ logical services`
link pointing to `https://architecture.internal/`, giving demo audiences
a one-click path between the two views.

## Screenshot deferral

Same constraint as D-17-17: Mac Mini control session has no GUI display
(Chrome `--headless` blocked by keychain/encryption errors,
`screencapture` returns `-10810`). HTML artifact is canonical; demo-day
operator screen capture is the appropriate next step.

## Structurizr disposition

Existing workspace at `docker/structurizr/workspace/workspace.dsl` is
stale ("Phase 13/14 baseline", calls Mac Mini "M5", contains only
logical containers — no physical hardware). Does NOT conflict with the
HTML approach. The framework note "original Structurizr-only framing
now T1 of this deliverable" is satisfied by retaining the workspace for
future structured-DSL work (related to D-16-09's spirit, deferred).
HTML approach was the chosen sister-style for D-17-17/D-17-18 demo coherence.
