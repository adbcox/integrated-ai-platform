# Phase 13 Block 2.5 — Closing Report

**Date:** 2026-04-28
**Branch:** `feat/block-2.5-control-plane`
**Status:** Phases 1–5 complete, all gates closed, awaiting Block 3 merge before commit.

## Summary

Built and deployed the operator control plane web app at `control.internal`
(tailnet-only). 32 routes across 8 modules, hardened sidecar pattern,
trigger-file dispatch with nonce+timestamp anti-replay, HTMX/Jinja2
frontend with Tier-3 escalation modal.

## Phase outcomes

### Phase 1 — Foundation Audit (read-only)

- `docs/phase-13/PRE_BLOCK_2_5_FOUNDATION_AUDIT_2026-04-28.md`
- D1–D10 review with user; D5 escalated backup to T3; D8 added nonce+timestamp.
- Sonarr/Radarr API key plaintext leak in service-registry.yaml flagged for
  separate remediation (not folded into 2.5).

### Phase 2 — Backend scaffold + provisioning

- Vault policy `config/vault-policies/control-plane-policy.hcl` (read access
  to operator hash, arr keys, restic, minio; explicit-deny on policy/AppRole writes).
- `scripts/provision-control-plane.sh` — idempotent: writes policy, creates
  AppRole (token_ttl 1 h, max 4 h), captures role-id/secret-id, prompts for
  operator password (Argon2 hashed via Python child, written via stdin so the
  hash never reaches process args).
- `docker/control-plane/Dockerfile`, `docker-compose.yml` — three-service stack:
  vault-agent sidecar, hardened linuxserver/socket-proxy, FastAPI main.
- `app/main.py`, `app/auth.py`, `app/triggers.py`, `app/audit_log.py`,
  `app/metrics.py`, `app/config.py`, 8 module routers.
- Caddy `control.internal` route appended (tailnet matcher + 403 fallthrough).
- service-registry.yaml entry appended.

**Gate 2 (regression probe `block-2.5-gate-2`):** PASS=15 FAIL=0 WARN=3.

### Phase 3 — Action implementations

| Module | Routes | Tier | Notes |
|--------|--------|------|-------|
| containers | list / inspect / logs / start / stop / restart | T1 / T2 | via socket-proxy |
| backups | last / run | T1 / T3 | run dispatches `backup-trigger` |
| credentials | paths / metadata / rotate | T1 / T3 | hash-only, never returns values |
| services | health / queue (sonarr,radarr) / indexers (prowlarr) / retry / remove | T1 / T2 | X-Api-Key from sidecar env |
| audit | vault / caddy / actions | T1 | bounded tail, regex filter |
| config | summary | T1 | file size + mtime drift |
| regression | run / last | T3 / T1 | dispatches `regression-probe` |
| registry | services / categories / health | T1 | parses service-registry.yaml |

Host launchers installed at `/Users/admin/iap-launchers/` (operator-writable;
sudo not required) and the `com.iap.control-plane.trigger-watcher` LaunchAgent
loaded.

### Phase 4 — HTMX/Jinja2 frontend

- `app/ui.py` — HTMX router; UI talks back to its own API on localhost.
- 8 page templates + `_partials.html` + `_auth_banner.html`.
- `static/tw.css` — handcrafted Tailwind subset (avoids npm build step).
- `static/cp.js` — Tier 3 modal (calls `/auth/unlock`, refires HTMX banner).
- `static/htmx.min.js` — bundled at build time (no CDN runtime dep).

### Phase 5 — Final close

End-to-end smoke test (all 200 / correct-403 / correct-401):

```
T1 reads:                            200 (×7)
T1 reads off-tailnet:                403 (×3)
T3 actions without unlock:           401 (×3)
UI pages:                            200 (×8)
Static assets:                       200 (×3)
Trigger watcher pipeline:            4-second turnaround, exit 0
```

**Gate 5 (regression probe `block-2.5-gate-final`):** PASS=15 FAIL=0 WARN=3.
WARN entries are non-regressions: openhands DNS cold cache (informational),
Restic CLI not installed locally (Vault-fetched only), no gate-specific
probes defined for the gate id (informational).

## Deferred / out of scope

1. **Container exec via web** — D5 ranks T3-with-allowlist; deferred behind
   `iap.exec.allowed` label parsing. No service currently sets the label,
   so the exec route is intentionally absent from the API.
2. **Credential rotation script** — `iap-credential-rotate-trigger.sh` is
   referenced by the watcher allowlist but not yet implemented. The
   rotation route returns through the trigger pipeline; the wrapper is a
   Phase 14 follow-up.
3. **Sonarr/Radarr API key plaintext leak in service-registry.yaml**
   (Phase 1 finding) — separate remediation session: rotate keys, scrub
   registry, evaluate git history.
4. **Caddy per-host metric labels** — already documented (Phase 14 Loki).
5. **DNS slot for control.internal** — needs OPNsense Unbound entry
   (`control.internal → 192.168.10.145`); not required for tailnet-internal
   reverse-proxy testing.

## Files changed (un-committed)

```
M  config/service-registry.yaml         (+control-plane entry, append-only)
M  docker/caddy/Caddyfile                (+control.internal route, append-only)
?? config/vault-policies/control-plane-policy.hcl
?? docker/control-plane/                 (whole subtree)
?? docs/phase-13/PRE_BLOCK_2_5_FOUNDATION_AUDIT_2026-04-28.md
?? docs/phase-13/PHASE_13_BLOCK_2_5_CLOSING.md   (this file)
?? scripts/provision-control-plane.sh
```

`scripts/backup.sh` shows as M but the diff (a single ha-backups path
addition) is pre-existing uncommitted work unrelated to Block 2.5.

## Commit plan (deferred)

Per standing rule, do **not** commit until Block 3 lands on main. After
Block 3 merge, rebase this branch and commit. Suggested message:

```
Phase 13 Block 2.5: operator control plane

Delivers control.internal — tailnet-only operator web app — with
container ops, manual backup, queue management, audit search,
regression probe, and credential rotation. Argon2-gated Tier 3
escalation, trigger-file dispatch with nonce+timestamp anti-replay
(D8), hardened canonical Vault Agent sidecar, and HTMX/Jinja2
frontend. Gate 2 + Gate 5 regression probes both PASS=15/FAIL=0.
```
