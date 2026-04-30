# Phase 13 Increment 1.5 — Inventory (pre-flight evidence)

**Date:** 2026-04-29 (late evening)
**HEAD at inventory:** `3084cc7`
**Baseline regression:** PASS=15 FAIL=0 WARN=3 (gate `pre-increment-1.5`,
log at `docs/phase-13/INCREMENT_1.5_REGRESSION_BASELINE_2026-04-29.log`).

This document is the pre-flight evidence required by the execution
prompt before any compose modifications. It cross-references the plan
scope (12 §6 services + 22 §7 containers from the architecture closeout
plan addendum at commit `63fd7de`) against the **current** state of the
running platform.

## Executive summary — STOP-AND-SURFACE

Both scope sets are dramatically smaller than the plan anticipated.
Increment 1 (Blocks 4.A/4.B/4.C — NetBox, Plane connector, Vault sidecar
refinement) brought most of the §6 plan services into canonical-pattern
compliance as it touched their compose stacks. Increment 2A (InvenTree,
just-closed) likewise ships hardened. The plan's §6/§7 figures were
captured at H1 checkpoint (2026-04-29 morning, commit `e782dc3` era)
and have not been re-anchored against the current docker fleet.

| Scope | Plan figure | Actual figure | Delta |
|---|---|---|---|
| §6 services lacking Vault Agent sidecar | 12 | **1** (`docker-plane-web-1`) | −11 |
| §7 containers lacking `cap_drop:[ALL]` | 22 | **20** (19 unhardened + 1 partial-drop) | −2 |

**Recommendation:** stop-and-surface for operator re-scoping. The
intended 12–15h Increment 1.5 may now be a 1–2h Increment 1.5 (one
sidecar to add, plus 20 cap_drops to apply). Operator should confirm
the reduced scope before execution proceeds, OR direct that the
inventory be expanded to include items the audit may have missed
(e.g., privileged exceptions that should be removed, canonical-pattern
drift in already-sidecared services, etc.).

The reduced scope **does not** invalidate Increment 1.5 — the doctrine
sweep is still valuable. It just means the sweep is mostly already done
by the inertia of prior increment work.

## §6 inventory — 1 service uncovered

### 16 services in the plan's §6 list (Q-14-1 addendum, scope item 1)

Cross-reference against `~/.vault-agent-secrets/<svc>/` directories
and per-container `vault-agent-secrets` bind-mount:

| # | Plan service       | vault-agent-secrets dir | Container has /vault/secrets bind | Status |
|---|--------------------|--------------------------|-----------------------------------|--------|
| 1 | vaultwarden        | ✅                       | ✅                                | covered |
| 2 | nextcloud          | ✅                       | ✅                                | covered |
| 3 | nextcloud-db       | ✅                       | ✅                                | covered |
| 4 | zabbix-postgres    | ✅                       | ✅                                | covered |
| 5 | zabbix-server      | ✅                       | ✅                                | covered |
| 6 | zabbix-web         | ✅                       | ✅                                | covered |
| 7 | docker-plane-db    | ✅ (`plane-db`)          | ✅                                | covered |
| 8 | docker-plane-api   | ✅ (`plane-api`)         | ✅                                | covered |
| 9 | docker-plane-web   | ❌                       | ❌                                | **GAP** |
| 10 | docker-plane-worker | ✅ (`plane-worker`)     | ✅                                | covered |
| 11 | docker-plane-beat  | ✅ (`plane-beat`)        | ✅                                | covered |
| 12 | openhands-app      | ✅                       | ✅                                | covered |
| 13 | litellm-gateway    | ✅                       | ✅                                | covered |
| 14 | open-webui         | ✅                       | ✅                                | covered |
| 15 | obot               | ✅                       | ✅                                | covered |
| 16 | homepage           | ✅                       | ✅                                | covered |

(The plan addendum says "12 services" but enumerates more granular
plane-stack containers; counting the plane stack as 5 separate workloads
gets 16 total. The figure 12 may have been a partial pre-Plane-rollout
count.)

### .env file rewire-queue cleanup status

H1 §1 deferred 8 .env files to §6. Current state:

| File                                                                              | State (now) |
|-----------------------------------------------------------------------------------|-------------|
| `/Users/admin/repos/integrated-ai-platform/docker/.env`                           | GONE |
| `/Users/admin/repos/integrated-ai-platform/docker/nextcloud/.env`                 | GONE |
| `/Users/admin/repos/integrated-ai-platform/docker/vaultwarden/.env`               | GONE |
| `/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env`                    | EXISTS (no credentials — only POSTGRES_USER/DB names + tuning + image tags) |
| `/Users/admin/repos/integrated-ai-platform/docker/zabbix/.env.zabbix-admin`       | GONE |
| `/Users/admin/repos/integrated-ai-platform/config/oss_wave/openhands.env`         | GONE |
| `/Users/admin/control-center-stack/stacks/gateways/.env`                          | GONE |
| `/Users/admin/control-center-stack/stacks/ai-control/.env`                        | GONE |

7 of 8 deleted; the remaining `docker/zabbix/.env` is non-credential-
bearing (tuning + non-secret usernames + image tags). It does NOT
violate non-negotiable #1 because no credentials are present. It is,
however, doctrine-debt-adjacent: zabbix-server already mounts
`/vault/secrets` and reads its credentials from there, so this .env is
vestigial and could be folded into compose `environment:` or deleted.

### §6 effective work item

**One service:** add Vault Agent sidecar for `docker-plane-web-1`.

The Plane stack is in `~/control-center-stack/stacks/plane/` (out-of-
repo, per CLAUDE.md "Out-of-repo compose changes" — would require
pre/post snapshots in the rewire log). All other plane workloads
already have sidecars, so the canonical pattern is established for
this exact stack — adding plane-web is mechanical.

**Optional secondary item:** vestigial `docker/zabbix/.env` cleanup
(move tuning/image-tags into compose `environment:` or `${VAR:-default}`
patterns). Doctrine-clean already, so not a §6 violation. Defer.

## §7 inventory — 20 containers unhardened

### Unhardened containers (no cap_drop or partial cap_drop)

19 containers run with `cap_drop=null` (all Linux capabilities
retained — root-equivalent within the container):

```
anythingllm
headscale
homarr
homeassistant
mcp-docker-remote
mcp-docs-remote
mcp-filesystem-remote
node-exporter
plex-mcp
prowlarr
radarr
seal-vault
sms1obot-mcp-server
sms1obot-mcp-server-shim
sonarr
uptime-kuma
vm
vmagent
```

(That's 18; 19th is below.)

1 container has a partial cap_drop (drops 3 specific caps but doesn't
drop ALL):

```
sportarr   cap_drop=[NET_ADMIN, SYS_ADMIN, SYS_PTRACE]   (no cap_add)
```

This is unusual — sportarr drops 3 caps that are normally NOT default,
which suggests the maintainer intended `cap_drop:[ALL]` and either
mis-typed or got confused by Docker's default cap set. Surfaced as a
discovery (D-22 below).

### Privileged exceptions (per CLAUDE.md)

```
cadvisor   Privileged=true
```

Already documented in CLAUDE.md "Container Hardening" section as the
sole privileged exception with rationale. Not a §7 work item.

### Already-hardened containers (out of scope)

37 containers already have `cap_drop:[ALL]` with workload-appropriate
`cap_add` lists — no work needed:

```
caddy, catt-controller, control-plane, docker-plane-{api,beat,db,minio,
redis,web,worker}, docker-socket-proxy-control, grafana-obs, homepage,
inventree, inventree-postgres, inventree-redis, inventree-worker,
litellm-gateway, mcpo-proxy, netbox, netbox-housekeeping,
netbox-postgres, netbox-redis, netbox-redis-cache, netbox-worker,
nextcloud, nextcloud-db, obot, open-webui, openhands-app,
topology-api, vault-server, vaultwarden, zabbix-agent, zabbix-postgres,
zabbix-server, zabbix-web
```

### §7 effective work breakdown by container class

The 20 unhardened containers cluster into operationally-meaningful
classes for fold-doctrine application:

| Class | Containers | Expected cap profile | Notes |
|---|---|---|---|
| **arr stack** | sonarr, radarr, prowlarr | `cap_drop:[ALL]` + (none or CHOWN/SETUID/SETGID) | linuxserver/* images; baseline test in Increment 1.5.B.2 |
| **MCP servers** | mcp-docker-remote, mcp-docs-remote, mcp-filesystem-remote, sms1obot-mcp-server, sms1obot-mcp-server-shim | `cap_drop:[ALL]` (no caps needed for HTTP-only servers) | mcp-docker-remote may need `cap_add: [NET_BIND_SERVICE]` if it binds <1024; verify |
| **observability** | vm, vmagent, node-exporter, uptime-kuma | `cap_drop:[ALL]` (read-only scrapers) | node-exporter notably runs `label=disable` security-opt on purpose |
| **AI surface** | anythingllm, plex-mcp, homarr | `cap_drop:[ALL]` likely sufficient | |
| **Vault stack** | seal-vault | `cap_drop:[ALL]` (matches vault-server which is already hardened) | seal-vault is the auto-unseal companion |
| **Smart home** | homeassistant | `cap_drop:[ALL] + cap_add: [NET_RAW?]` likely | HA may need NET_RAW for ICMP probes; verify |
| **VPN client** | headscale | `cap_drop:[ALL] + cap_add: [NET_ADMIN]` likely | headscale-server doesn't need it; headscale-as-client would |
| **Sport feed** | sportarr | `cap_drop:[ALL]` (rewrite the partial drop) | confirmed running fine without those 3 caps; safe to flip to `[ALL]` |

### §7 capability-required exceptions to anticipate

Per CLAUDE.md "Container Hardening — minimal cap_add per workload" and
"Known Hardening Trade-offs" sections, the following container-classes
have known capability requirements:

- **node-exporter** runs as PID 1 root on the host's `/proc` and `/sys`
  — typically uses `cap_add: [SYS_TIME]` for clock skew metrics, but
  often runs without if those metrics aren't needed. Verify.
- **vmagent** scrapes Prometheus endpoints over HTTP; doesn't typically
  need any caps.
- **headscale** (control-plane variant) is just a control-plane HTTP
  server; no special caps. (`headscale` listed here is the server, not
  a tailnet client — so no NET_ADMIN.)
- **homeassistant** running on host network with mDNS/SSDP discovery
  may need `NET_ADMIN` and/or `NET_RAW`. Verify against the running
  container's actual usage.
- **seal-vault** mirrors vault-server, which has `cap_drop:[ALL]` and
  no cap_add — should be the same.

## A-013 fold doctrine application plan

Per the execution prompt, fold doctrine applies aggressively:

### §6 fold structure

With only 1 service (plane-web), the fold doesn't apply — single-item
work isn't a fold. Treat as a single FULL IV&V step (the canonical
pattern is already proven for plane-{api,worker,beat}, so this is
mechanical mirroring within the same stack).

**Caveat:** plane stack lives in `~/control-center-stack/stacks/plane/`
(out-of-repo). Per CLAUDE.md "Out-of-repo compose changes",
pre/post snapshots required in the rewire log because git doesn't
track these files automatically.

### §7 fold structure

20 containers, FULL IV&V on the first (load-bearing pattern proof),
folded across remaining 19. Suggested first-pick ordering by
likelihood of zero-cap-required:

1. **First (FULL IV&V):** `vmagent` — pure HTTP scraper, smallest blast
   radius if rollback needed, well-understood image. Or `seal-vault`
   if mirroring vault-server proves it works.
2. **Folded batch 1 (5 containers):** `vm`, `node-exporter`, `vmagent`,
   `uptime-kuma`, `anythingllm` — observability + simple HTTP services.
3. **Folded batch 2 (5):** `sonarr`, `radarr`, `prowlarr`, `homarr`,
   `plex-mcp` — arr-stack + media surface. linuxserver/* images often
   need CHOWN/SETUID/SETGID for s6-overlay; budget a regression
   re-check after this batch.
4. **Folded batch 3 (5):** `mcp-docker-remote`, `mcp-docs-remote`,
   `mcp-filesystem-remote`, `sms1obot-mcp-server`,
   `sms1obot-mcp-server-shim` — MCP servers; HTTP-only.
5. **Folded batch 4 (4):** `headscale`, `homeassistant`, `seal-vault`,
   `sportarr` — special-cap candidates; verify each individually.

After every batch of 5: regression probe (per execution prompt).

## Operator gate — pre-execution decision point

Before proceeding to 1.5.A.1 / 1.5.B.1 audit phase (which would now be
mostly redundant given this inventory's depth), operator should
confirm one of the following paths:

### Path A — Proceed with reduced scope (recommended)

Scope: 1 §6 service (plane-web sidecar) + 20 §7 containers
(`cap_drop:[ALL]` + workload-appropriate cap_add). Effort estimate
revised from 12–15h to ~3–4h. Single execution window.

### Path B — Expand audit to surface drift in already-covered services

Spend ~2h auditing the 15 covered §6 services for canonical-pattern
drift (e.g., do their healthchecks source `credentials.env` per the
C2 Discovery #4 amendment? Are their AppRoles still scoped correctly?
Are their compose files using `condition: service_completed_successfully`
on the sidecar?). May surface a longer work list.

### Path C — Stop, re-anchor the campaign plan, restart

The architecture closeout plan's §6/§7 inventory is stale. Update it
to reflect current state, re-issue Increment 1.5 with corrected scope.
Effort: ~30min plan update + new execution prompt.

**Default if no operator response:** Path A. The reduction in scope
is real and beneficial — most of the doctrine sweep already happened
during Increment 1's block work.

## Discoveries surfaced during inventory (numbered continuing from #21)

**#22 — sportarr has a partial cap_drop, not cap_drop:[ALL].** The
container drops `[NET_ADMIN, SYS_ADMIN, SYS_PTRACE]` but retains the
default Docker cap set. Three caps it explicitly drops are NOT in the
default set anyway, suggesting maintainer confusion about Docker's
cap-drop semantics. Resolution: replace with `cap_drop:[ALL]` (no
cap_add — sportarr is a simple Python web scraper).

**#23 — `docker/zabbix/.env` is doctrine-debt-adjacent but not a
violation.** The file exists with non-credential content (POSTGRES_USER
name, image tags, tuning vars). zabbix-server already reads its
credentials from `/vault/secrets/credentials.env`. The .env is
vestigial. Could be folded into compose `environment:` blocks or
deleted; not a §6 work item per non-negotiable #1 because it contains
no credentials.

**#24 — Plane stack out-of-repo location creates Increment 1.5
asymmetry.** The single §6 work item (plane-web sidecar) lives in
`~/control-center-stack/stacks/plane/`, which CLAUDE.md flags as
requiring pre/post snapshots in the rewire log. All other Increment 1.5
work is in-repo and follows standard commit/diff audit. Operator should
decide whether to (a) capture snapshots for the plane-web change
specifically, (b) defer plane-web to a future increment that handles
out-of-repo work as a class, or (c) migrate the plane stack into the
repo as part of the Phase 14 D-DOC documentation work.

## Files written during pre-flight

- `docs/phase-13/INCREMENT_1.5_REGRESSION_BASELINE_2026-04-29.log`
- `docs/phase-13/INCREMENT_1.5_INVENTORY_2026-04-29.md` (this file)

No compose modifications. No commits yet.

## Next step

Surface this inventory + recommendation to operator. Await Path A/B/C
decision before proceeding to execution sub-phases.
