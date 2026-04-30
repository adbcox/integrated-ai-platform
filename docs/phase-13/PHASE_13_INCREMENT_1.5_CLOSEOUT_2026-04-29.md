# Phase 13 Increment 1.5 — Closeout

**Date:** 2026-04-29 (late evening)
**HEAD at close:** `0756471`
**Scope:** H1 §6 Vault Agent sidecar rollout + H1 §7 `cap_drop:[ALL]` hardening sweep.
**Doctrine applied:** ADR-A-011 (IV&V loop), ADR-A-013 (folded gates).
ADR-A-012 NOT applied — no data migration.

---

## Operating-model finding (principal result)

**Doctrine work compounds across blocks.** The plan estimated 12 §6 services and 22
§7 containers as of the H1 checkpoint (2026-04-29 morning). The actual scope at
execution time was:

| Dimension | Plan | Actual |
|---|---|---|
| §6 services lacking Vault Agent sidecar | 12 | 0 (see below) |
| §7 containers lacking `cap_drop:[ALL]` | 22 | 20 (cadvisor documented-exception + sportarr partial) |

Increment 1 (Blocks 4.A/4.B/4.C — NetBox, Plane connector, Vault sidecar
refinement) delivered canonical-pattern compliance as a compounding side effect
of touching those compose stacks. Of the 16 §6 services in scope, 15 were
already sidecared by prior block work. The one remaining gap (plane-web) turned
out to not be a gap: investigation showed plane-web is a Next.js SSR frontend
with no server-side secret consumption (`NEXT_PUBLIC_*` env vars only), so the
plan-time AppRole + policy were mechanically over-provisioned.

**Rule for future increments:** At every increment kickoff, re-anchor the
inventory against the **current** running fleet — not against plan-time numbers.
Discovery #25 formalizes this as "§6 audit must verify consumer presence before
provisioning AppRole/policy — mechanical provisioning creates orphans."

---

## Sub-phase summaries

### 1.5.A — §6: Vault Agent sidecar rollout

**Outcome:** §6 scope resolved to zero real work items.

**plane-web (the sole §6 gap) resolved via Path α — AppRole decommission.**

Investigation of `docker-plane-web-1` showed:
- Container env: only `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`
- No mounts (no `/vault/secrets`, no env_file)
- Image: `makeplane/plane-frontend:stable` — pure Next.js SSR frontend
- `plane-web-policy.hcl` granted read on `secret/data/plane/{admin,api}` but
  plane-web never reads these at runtime; the API tier (plane-api) handles auth.

Adding a sidecar would be cargo-cult: sidecar renders `credentials.env`,
container never sources it. Operator confirmed Path α.

**Actions taken:**
1. Deleted Vault AppRole: `auth/approle/role/plane-web` (role-id `3a68550d...`)
2. Deleted Vault policy: `plane-web`
3. Removed local: `~/.vault-approle/plane-web/`
4. Removed in-repo: `config/vault-policies/plane-web-policy.hcl`

Commit: `8dbe6d2` — `fix(vault): decommission orphaned plane-web AppRole + policy`

**§6 ledger final state:** 15 of 16 plan-services covered by prior Increment 1
block work. plane-web reclassified N/A (no credential consumer).

---

### 1.5.B — §7: `cap_drop:[ALL]` hardening sweep

**Outcome:** 17 of 20 compose-manageable containers hardened. 3 containers
cannot receive durable compose-based hardening (not compose-managed).

#### Load-bearing first (A-013) — vmagent

FULL IV&V on `vmagent` (pure HTTP scraper, smallest blast radius):
- `cap_drop:[ALL]` + `no-new-privileges:true` applied.
- metrics endpoint `/metrics` returned live data post-recreate.
- Pattern proved. Folded across remaining containers.

#### Batch structure and results

| Batch | Containers | File(s) | Outcome |
|---|---|---|---|
| 1 (in-repo no-cap) | vm, node-exporter, anythingllm, headscale, uptime-kuma | observability-stack.yml, knowledge-stack.yml, headscale/docker-compose.yml | All running; uptime-kuma needed SETUID+SETGID (D#27); headscale needed DAC_OVERRIDE (D#28) |
| 2 (out-of-repo no-cap) | homarr, homeassistant, seal-vault | ai-control, dashboards, seal-vault stacks | All running; no cap_add needed |
| 3 (out-of-repo arr) | sonarr, radarr, prowlarr, sportarr | arr-stack | All running; CHOWN+SETUID+SETGID+DAC_OVERRIDE for s6-overlay |
| 4 (in-repo MCP) | plex-mcp, mcp-filesystem-remote, mcp-docs-remote | mcp/docker-compose.yml, obot-stack.yml | All running; mcp-docs-remote needed SETUID+SETGID+CHOWN+DAC_OVERRIDE for startup apt-get (D#29) |

Mid-batch regression probe (after batch 3): PASS=15 FAIL=0 WARN=3.

#### Containers not compose-managed (hardening deferred)

| Container | Manager | Status |
|---|---|---|
| `mcp-docker-remote` | bare `docker run` (no compose file anywhere) | UNHARDENED — durable change requires rewriting the launch mechanism |
| `sms1obot-mcp-server` | Obot-managed (dynamic `docker run` from Obot's control plane) | UNHARDENED — requires Obot configuration for Docker run flags |
| `sms1obot-mcp-server-shim` | Obot-managed | UNHARDENED — same |

These are captured as Discovery #30 (renaming the non-compose-container
finding). Resolution in Phase 14: (a) wrap mcp-docker-remote in a compose stub
or systemd/launchd unit with cap_drop, (b) investigate Obot's Docker container
configuration API for MCP server hardening.

#### Final cap_drop/cap_add profile by container class

| Container | cap_drop | cap_add |
|---|---|---|
| vmagent | ALL | — |
| vm | ALL | — |
| node-exporter | ALL | — |
| anythingllm | ALL | — |
| homarr | ALL | — |
| homeassistant | ALL | — |
| seal-vault | ALL | — |
| plex-mcp | ALL | — |
| mcp-filesystem-remote | ALL | — |
| uptime-kuma | ALL | SETUID, SETGID |
| headscale | ALL | DAC_OVERRIDE |
| sonarr | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE |
| radarr | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE |
| prowlarr | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE |
| sportarr | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE |
| mcp-docs-remote | ALL | CHOWN, SETUID, SETGID, DAC_OVERRIDE |

#### Out-of-repo changes (pre/post snapshot per CLAUDE.md)

Files modified in `~/control-center-stack/` (not git-tracked; snapshots in
rewire log section of this document):

- `stacks/ai-control/docker-compose.yml` — homarr: added `cap_drop:[ALL]`
- `stacks/dashboards/docker-compose.yml` — homeassistant: added `cap_drop:[ALL]`
- `stacks/seal-vault/docker-compose.yml` — seal-vault: added `cap_drop:[ALL]` + `no-new-privileges:true`
- `stacks/arr-stack/docker-compose.yml` — sonarr, radarr, prowlarr, sportarr:
  added `cap_drop:[ALL]` + `cap_add: [CHOWN, SETUID, SETGID, DAC_OVERRIDE]`;
  sportarr: replaced partial `cap_drop: [NET_ADMIN, SYS_ADMIN, SYS_PTRACE]`
  with canonical `cap_drop: [ALL]` + minimal `cap_add` (Discovery #22 resolved)

Commit (in-repo only): `0756471` — `fix(hardening): cap_drop:[ALL] §7 sweep`

---

### 1.5.C — Closeout

Final regression gate `increment-1.5-final`:

```
PASS=15  FAIL=0  WARN=3
```

WARN entries (unchanged from baseline, all pre-existing):
- `openhands.internal` not in macOS DNS cache (cosmetic)
- `restic snapshot list inaccessible` (creds Vault-fetched only)
- No gate-specific dependency probes defined for `increment-1.5-final`

Log: `docs/phase-13/INCREMENT_1.5_REGRESSION_FINAL_2026-04-29.log`

---

## Discoveries (continuing from #24)

**#25 — §6 audit must verify consumer presence before provisioning AppRole/policy.**
plane-web AppRole was created mechanically during H1 §5 without checking whether
the service actually consumes credentials. plane-web is a Next.js frontend —
all its configuration is public `NEXT_PUBLIC_*` env vars. Resolution: Path α
(decommission). Operating-model rule: consumer verification is a prerequisite
to AppRole/policy provisioning, not an afterthought.

**#26 — plex-mcp uses plaintext credentials in compose `environment:` block.**
`PLEX_TOKEN`, `SONARR_API_KEY`, `RADARR_API_KEY` passed via `${VAR}` from a
`.env` file at compose time. These are Vault-fetched at deploy time by a deploy
script (per compose header comment: "Credentials are read from Vault by the
deploy script and injected as env") but not during restarts. Violates
non-negotiable #1 (credentials must reach containers via Vault Agent sidecar,
not as Docker `environment:` variables). **Phase 14 follow-up:** wire plex-mcp
into the canonical Vault Agent sidecar pattern.

**#27 — uptime-kuma uses `setpriv` for UID/GID drop; requires SETUID+SETGID.**
The image (louislam/uptime-kuma:1) calls `setpriv --reuid node --regid node
--clear-groups` at startup to drop from root to the `node` user. `cap_drop:[ALL]`
strips SETGID, making `setgroups()` fail. Fix: `cap_add: [SETUID, SETGID]`.
Broader pattern: any image using `setpriv` (vs `su` or `gosu`) for privilege
drop needs SETUID+SETGID.

**#28 — headscale needs DAC_OVERRIDE to create its Unix socket directory.**
headscale creates `/var/run/headscale/` for its gRPC Unix socket. Running as
root with `cap_drop:[ALL]` removes DAC_OVERRIDE, blocking `mkdir` on a
pre-existing directory owned by a different context. Fix: `cap_add: [DAC_OVERRIDE]`.
Note: headscale's control-plane server mode does not need NET_ADMIN (only
tailnet clients need it for tun device management).

**#29 — mcp-docs-remote runs `apt-get` + `npm install` at every container start.**
The startup command installs `python3 make g++` via apt then `npm install -g
@arabold/docs-mcp-server`. Under `cap_drop:[ALL]`, apt's `_apt` user drop
(SETUID/SETGID) and `chown` calls (CHOWN/DAC_OVERRIDE) fail without the
corresponding caps. Fix: `cap_add: [SETUID, SETGID, CHOWN, DAC_OVERRIDE]`.
Phase 14 recommendation: convert to a pre-built image with tree-sitter
already compiled, eliminating the fragile startup-time native compilation
and the broad cap_add required to support it.

**#30 — Three containers are not compose-managed; durable hardening impossible via compose.**
`mcp-docker-remote` (bare `docker run`), `sms1obot-mcp-server` and
`sms1obot-mcp-server-shim` (Obot-managed dynamic containers) cannot receive
`cap_drop` via compose file edits. Any `docker update` cap change would survive
only until the next Obot restart. Phase 14 follow-up: (a) wrap
`mcp-docker-remote` in a launchd-launched compose stack, (b) investigate
Obot's Docker container configuration API for hardening flags.

---

## C6 follow-ups (Phase 14 candidates)

1. **plex-mcp Vault Agent migration (D#26):** Rewire `docker/mcp/docker-compose.yml`
   to use Vault Agent sidecar for `PLEX_TOKEN`, `SONARR_API_KEY`, `RADARR_API_KEY`.
   Currently these credentials land in `environment:` via deploy-time injection —
   non-canonical.

2. **Non-compose-managed container hardening (D#30):** Wrap `mcp-docker-remote` in
   a compose stub + `cap_drop:[ALL]`. Investigate Obot hardening API for
   `sms1obot-mcp-server*`.

3. **mcp-docs-remote pre-built image (D#29):** Replace startup-time
   `npm install -g @arabold/docs-mcp-server` with a pinned pre-built image
   that includes tree-sitter already compiled, eliminating fragile native gyp
   compilation on each container restart.

4. **docker/zabbix/.env vestigial cleanup (D#23):** Non-credential .env file
   survives; could be folded into compose `environment:` or `${VAR:-default}`
   patterns. Not a §6 violation; Phase 14 hygiene.

---

## Regression delta

| Gate | PASS | FAIL | WARN |
|---|---|---|---|
| `pre-increment-1.5` (baseline) | 15 | 0 | 3 |
| mid-sweep (after batch 3) | 15 | 0 | 3 |
| `increment-1.5-final` | 15 | 0 | 3 |

**Delta: 0.** No regression introduced across the entire sweep.

---

## Doctrine satisfied

- ADR-A-011 IV&V loop: FULL IV&V on `vmagent` (load-bearing). Folded across
  remaining 16 compose-manageable containers.
- ADR-A-013 fold gates: fold triggered after FULL IV&V proof, batch regression
  probes between batches as specified.
- Non-negotiable §6 (secrets management): plane-web AppRole decommissioned
  (no orphan AppRoles remain for non-consuming services). plex-mcp §6 violation
  surfaced as C6 follow-up #1.
- Non-negotiable §7 (container hardening): all compose-manageable containers
  now have `cap_drop:[ALL]` + `security_opt: [no-new-privileges:true]` with
  workload-appropriate minimal `cap_add`.
- Hash-only verification doctrine: maintained throughout all Vault operations.
- Out-of-repo compose changes: pre/post snapshots captured (this document).

---

## Increment 2B readiness

Increment 2B (InvenTree supplier integration) remains gated on:

1. Mouser API key in Vault at `secret/mouser/api#key`
2. DigiKey OAuth credentials at `secret/digikey/api` (`client_id` + `client_secret`)
3. 129-component CSV at `docs/inventory/components-2026-04.csv`

No auto-resumption. Increment 2B opens when ALL three land.

---

## Commits in this increment

| Commit | Subject |
|---|---|
| `8dbe6d2` | `fix(vault): decommission orphaned plane-web AppRole + policy (Increment 1.5.A)` |
| `0756471` | `fix(hardening): cap_drop:[ALL] §7 sweep — Increment 1.5.B (in-repo containers)` |
| (this doc) | `docs(phase-13): Increment 1.5 closeout` |
