# Phase 13 Block 4.D — Closeout (Retroactive)

**Date:** 2026-05-01
**Status:** Closed.
**Doctrine:** D-16-01 — retroactive block-scope closeout. The
substantive deploy + bootstrap work shipped on 2026-04-29 in
**Increment 2A** (commits `3fe6439` + `e54800f`); the increment-level
closeout exists at
`docs/phase-13/PHASE_13_INCREMENT_2A_CLOSEOUT_2026-04-29.md`.
This document is the **block-level** closeout that ties off
Block 4.D's scope, separates what shipped from what is
intentionally deferred, and records that nothing further is owed
at the Block 4.D scope.

## Why a separate Block 4.D closeout

Block 4.D was scoped before the Increment 2A/2B split was decided
(see `INCREMENT_2A_PREDEPLOY_AUDIT_2026-04-29.md`, "Scope
ratification"). When the split landed, Increment 2A took the
deploy/bootstrap work and Increment 2B took the supplier-integration
+ CSV-import work. The 2A closeout documented 2A. Block 4.D's own
"is this block done?" question was answered implicitly but never
written up as a block-scope artifact, which left D-16-01 open in
the Phase 16 cleanup register. This document closes D-16-01.

## Scope reconciliation

| Original Block 4.D sub-phase | Delivered in | Status |
|---|---|---|
| 4.D.1 — Pre-deploy artifacts (compose, Vault policy, AppRole, Caddy site) | Increment 2A, commit `3fe6439` | DONE |
| 4.D.2 — Deploy + bootstrap (stack online, admin user, plugins pip-installed not enabled) | Increment 2A, commit `e54800f` | DONE |
| 4.D.3 — CSV import of 129-component inventory | Increment 2B (gated on operator CSV) | DEFERRED — out of Block 4.D scope per 2A/2B split |
| 4.D.4 — Mouser supplier integration | Increment 2B (gated on Mouser API key) | DEFERRED — out of Block 4.D scope per 2A/2B split |
| 4.D.5 — DigiKey supplier integration | Increment 2B (gated on DigiKey OAuth registration) | DEFERRED — out of Block 4.D scope per 2A/2B split |
| 4.D.6 — NetBox ↔ InvenTree cross-reference | Increment 2B (gated on 4.D.3 land) | DEFERRED — out of Block 4.D scope per 2A/2B split |

**Block 4.D scope after the 2A/2B split** = 4.D.1 + 4.D.2 only.
4.D.3–4.D.6 were re-parented to Increment 2B and tracked under that
deliverable, not under Block 4.D. The Phase Roadmap state
("Phase 13 Increments 2B–7 still gated on Mouser+DigiKey+CSV" in
`CLAUDE.md`) is the canonical handle for those.

## Verification — current steady state (2026-05-01)

Re-verified at closeout time, ~22 hours after deploy.

### Container roster

```
inventree            Up 22 hours (healthy)   inventree/inventree:1.0.9
inventree-worker     Up 21 hours (healthy)   inventree/inventree:1.0.9
inventree-postgres   Up 22 hours (healthy)   postgres:17-alpine
inventree-redis      Up 22 hours (healthy)   redis:7-alpine
```

All 4 long-running containers healthy. Vault Agent sidecars
(`vault-agent-inventree`, `vault-agent-inventree-postgres`,
`vault-agent-inventree-redis`) ran to `Exited (0)` per
`exit_after_auth: true` doctrine and are not present in the running
roster — this is the correct steady state for one-shot Vault Agent.

### Caddy + TLS reachability

```
GET https://inventree.internal/api/   →   HTTP 200
```

API root summary (live, 2026-05-01):

```
server: InvenTree | version: 1.0.9 | apiVersion: 391
worker_running: True | worker_count: 4
plugins_enabled: True | active_plugins: 10
```

Identical to 2A post-deploy snapshot — no drift.

### Vault provisioning

AppRole present at `~/.vault-approle/inventree/{role-id,secret-id}`.
Vault Agent secret directories present at
`~/.vault-agent-secrets/{inventree,inventree-postgres,inventree-redis}/`
with rendered `credentials.env` files.

Hash-only verification of Vault paths is recorded in the 2A closeout
(§"Vault hash-only verification table"); not re-run here because
the 2A table was captured against the same secrets that the live
sidecars rendered into `credentials.env`, and the containers have
been continuously healthy since (no restart, no re-render). Re-running
the table at closeout time would require a working root-token probe
and would only re-confirm what the 21+-hour healthy window already
proves: the values authenticate successfully against postgres,
redis, and Django at every healthcheck interval.

### NetBox service registration

InvenTree registered in NetBox CMDB as part of the deploy work.
Authoritative service inventory is NetBox per Block 4.C closeout
(see `PHASE_13_BLOCK_4C_CLOSEOUT_2026-04-29.md` §"NetBox object/
custom-field/relationship counts" — 75 services). InvenTree was
not in the original 75 (Block 4.C's count is pre-Block-4.D);
post-Block-4.D the service count is `75 + 1 = 76` reflecting the
InvenTree app entry.

## What is intentionally NOT in this block

The following items are **out of Block 4.D scope** and belong to
Increment 2B or later:

- **CSV import of 129-component inventory** — needs the operator-
  supplied CSV at `docs/inventory/components-2026-04.csv`. Until
  the CSV exists, 4.D.3 cannot start. Will use the
  `inventree-part-import 1.9.2` plugin (already pip-installed,
  not enabled).
- **Mouser supplier integration** — needs Mouser API key at
  `secret/mouser/api#key`. Will use the
  `inventree-supplier-panel 0.6.0` plugin (already pip-installed,
  not enabled).
- **DigiKey supplier integration** — needs DigiKey OAuth client
  registration at `developer.digikey.com → Apps`, then
  `client_id`+`client_secret` at `secret/digikey/api`.
- **NetBox ↔ InvenTree cross-reference** — depends on 4.D.3
  populating real Part records before a cross-reference custom
  field has anything to point at.
- **InvenTree API token minting** — `secret/inventree/api_token#token`
  is an empty placeholder; populated in 2B once a Django auth
  Token is minted for the admin user (or a service account is
  provisioned).
- **Plugin enablement** — both supplier plugins are pip-installed
  but the admin DB toggles are not flipped, per 2A doctrine
  ("installed but not configured"). Enablement happens in 2B
  alongside their configuration.

These are tracked under the **Increment 2B kickoff trigger** in
the 2A closeout (§"Increment 2B readiness"). Increment 2B opens
when ALL three operator-side prereqs land (Mouser key, DigiKey
client, CSV file). **No auto-resumption** — operator drafts the
2B execution prompt when prereqs land.

## Discoveries surfaced during Block 4.D

Discoveries #18, #19, #20, #21 were registered during Increment
2A. Full text in `PHASE_13_INCREMENT_2A_CLOSEOUT_2026-04-29.md`
§"Discoveries (continuing from #17)". Recap:

| # | Topic | Resolution |
|---|---|---|
| 18 | `init.sh` shebang `/bin/ash` broken in Debian-based InvenTree image | Invoke via explicit `/bin/bash` in entrypoint wrapper |
| 19 | Redis `cap_drop:[ALL]` strips `DAC_OVERRIDE`; default RDB snapshotting fails | `--save ''` (cache-only workload, no persistence) |
| 20 | Overriding `entrypoint:` clears CMD-as-args path | Explicit `command:` in compose mirrors upstream gunicorn invocation |
| 21 | `docker exec` does NOT inherit PID-1 env from compose entrypoint wrapper | Diagnostics must source `/vault/secrets/credentials.env` themselves |

These are deploy-time hardening discoveries (cap_drop interactions,
upstream-image quirks). All four resolved in `docker/inventree/
docker-compose.yml`. No outstanding doctrine work at the Block 4.D
scope.

## Block 4.D follow-ups

None at the Block 4.D scope. All 2A C6 follow-ups (4 items) are
either Increment 2B prereqs (#1, #2) or routine cosmetic notes
(#3 Caddyfile formatting hint, #4 lighter healthcheck endpoint).
Tracked in 2A closeout §"C6 follow-ups (added)".

## Block 4.D close criteria

| Criterion | Status |
|---|---|
| Stack containers healthy and continuously up since deploy | ✅ — 21–22h uptime, healthy |
| Caddy site live with valid TLS | ✅ — HTTP 200 via `https://inventree.internal/api/` |
| Vault AppRole + 4 secret paths provisioned with hash-only verification | ✅ — recorded in 2A closeout table |
| Service registered in NetBox CMDB | ✅ — service count 75 → 76 |
| Hardening doctrine applied (`cap_drop:[ALL]` + `no-new-privileges:true` on every container) | ✅ — all 4 long-running containers + 3 sidecars |
| Image pinning enforced | ✅ — `inventree:1.0.9`, `postgres:17-alpine`, `redis:7-alpine` |
| Regression delta from baseline | ✅ — PASS=15 FAIL=0 WARN=3 (delta 0) |
| Out-of-block work re-parented (no in-flight Block 4.D items) | ✅ — 4.D.3–4.D.6 owned by Increment 2B |
| Block-scope closeout document landed (this file) | ✅ — D-16-01 |

**Block 4.D officially closed.** No work remaining at the Block 4.D
scope. Operator-side prereqs (Mouser, DigiKey, CSV) are tracked
under Increment 2B; when they land, a new execution prompt opens
2B and Block 4.D plays no further role.
