# Phase 13 Increment 2A — Closeout

**Date:** 2026-04-29
**Scope:** Block 4.D split: deploy-only.
**Sub-phases delivered:** 4.D.1 (pre-deploy) + 4.D.2 (deploy + bootstrap).
**Sub-phases deferred:** 4.D.3 (CSV import), 4.D.4 (Mouser), 4.D.5 (DigiKey),
4.D.6 (NetBox cross-reference) — all moved to Increment 2B pending external
prerequisites (Mouser key, DigiKey OAuth registration, 129-component CSV).

Doctrine applied: ADR-A-011 IV&V loop. ADR-A-012 (equivalence harness) and
ADR-A-013 (folded gates) intentionally NOT applied — no migration, no fold
in 2A.

## Sub-phase summaries

### 4.D.1 — Pre-deploy preparation (commit 3fe6439)

Audit doc: `docs/phase-13/INCREMENT_2A_PREDEPLOY_AUDIT_2026-04-29.md`.

Artifacts:

- `config/vault-policies/inventree-policy.hcl` — read-only on
  `secret/data/inventree/{postgres,redis,secret_key,admin,api_token}`,
  list+read on `secret/metadata/inventree/*`, explicit-deny on
  `sys/policies/acl/*` and `auth/approle/role/*`. Mouser/DigiKey paths
  intentionally excluded; they will be added in 2B alongside the AppRole
  rotation.
- `scripts/provision-inventree.sh` — idempotent Vault provisioning
  script, hash-only logging. Provisions postgres password, redis
  password, Django SECRET_KEY, admin (password+username+email),
  api_token placeholder. Verifies policy isolation: in-policy read
  succeeds, out-of-policy `secret/netbox/postgres` read denied, policy
  write denied.
- `docker/inventree/docker-compose.yml` — 7-container stack:
  inventree (gunicorn) + inventree-worker (django-q) + inventree-postgres
  + inventree-redis + 3× vault-agent sidecars (one per credential
  consumer). All containers `cap_drop:[ALL]` + `no-new-privileges:true`.
  Image-pinned to `docker.io/inventree/inventree:1.0.9`,
  `postgres:17-alpine`, `redis:7-alpine`.
- `docker/inventree/vault-agent-{inventree,inventree-postgres,inventree-redis}/`
  — agent.hcl + credentials.env.tmpl per sidecar. inventree (app+worker
  share) renders 6 vars; postgres renders POSTGRES_PASSWORD; redis
  renders REDIS_PASSWORD.
- Caddy `inventree.internal` reverse-proxy block targeting
  `host.docker.internal:8087`.

Port allocation: host port 8087 (8000 occupied by docker-plane-api-1;
8084-8086 reserved for SSH-tunnel cluster).

### 4.D.2 — Deploy + bootstrap (FULL IV&V)

**Vault provisioning** — `scripts/provision-inventree.sh` ran cleanly:
policy attached, AppRole created, secrets written, isolation verified
(✅ in-policy read, ✅ out-of-policy read denied, ✅ policy write
denied).

**Bootstrap** — `docker compose run --rm inventree invoke update`:
0 pending migrations applied (initial schema created), admin user
auto-created from `INVENTREE_ADMIN_*` env vars rendered by Vault Agent,
10 built-in plugins loaded, settings cleaned.

**Stack online** — `docker compose up -d` brought inventree +
inventree-worker to healthy. Caddy reloaded; `https://inventree.internal/api/`
returns 200 via Caddy local CA (TLS handshake 0.045s, ssl_verify=0).

**Plugin install (installed-not-configured)** —
`/home/inventree/data/plugins.txt` populated with
`inventree-supplier-panel` + `inventree-part-import`; `invoke plugins`
ran pip-install for both. `pip show` confirms:

- `inventree-supplier-panel 0.6.0` at `/usr/local/lib/python3.11/site-packages`
- `inventree-part-import 1.9.2` at `/usr/local/lib/python3.11/site-packages`

Neither plugin is enabled (no admin DB toggle flipped), per 2A doctrine
("installed but not configured"). Configuration lands in 2B once Mouser
and DigiKey credentials exist.

## Container roster (post-deploy steady state)

```
inventree            Up 2 minutes (healthy)   127.0.0.1:8087->8000/tcp
inventree-worker     Up 2 minutes (healthy)   8000/tcp
inventree-postgres   Up 7 minutes (healthy)   5432/tcp
inventree-redis      Up 37 seconds (healthy)  6379/tcp
vault-agent-inventree            Exited (0)
vault-agent-inventree-postgres   Exited (0)
vault-agent-inventree-redis      Exited (0)
```

Sidecars exit 0 = correct (one-shot Vault Agent with `exit_after_auth`).

## Caddy + TLS confirmation

```
https://inventree.internal/api/  →  HTTP 200  (Caddy local CA, 45ms)
```

API root summary:

```
server: InvenTree | version: 1.0.9 | apiVersion: 391
worker_running: True | worker_count: 4
plugins_enabled: True | active_plugins (built-in): 10
```

## InvenTree object counts (empty-deploy verification)

```
parts 0    companies 0    stock items 0    users 1 (admin)
```

Confirms 2A scope: deploy is empty. CSV import and supplier setup
land in 2B.

## Vault hash-only verification table

| Path                              | Field    | sha256[12]    |
|-----------------------------------|----------|---------------|
| secret/inventree/postgres         | password | 261e2dc031b6  |
| secret/inventree/redis            | password | cad84bf3c617  |
| secret/inventree/secret_key       | value    | 5a345af8c9bd  |
| secret/inventree/admin            | password | deacd5cb6583  |
| secret/inventree/api_token        | token    | (empty)       |

api_token is an empty placeholder — populated in 2B once a Django
auth Token is minted for the admin user (or a service account is
provisioned with scoped permissions).

## Regression delta

Baseline (`INCREMENT_2_REGRESSION_BASELINE_2026-04-29.log`):
**PASS=15 FAIL=0 WARN=3**

Post-deploy (`INCREMENT_2A_REGRESSION_FINAL_2026-04-29.log`):
**PASS=15 FAIL=0 WARN=3**

**Delta: 0.** No regression introduced by InvenTree deployment.

WARN entries unchanged from baseline:
- `openhands.internal` not in macOS DNS cache (cosmetic; not actively used)
- `restic snapshot list inaccessible` (creds Vault-fetched only — not run interactively)
- gate-specific dependency probes for `increment-2a-final` not defined
  (no upstream cross-service deps for empty-deploy InvenTree)

## Discoveries (continuing from #17)

**#18 — `init.sh` shebang `/bin/ash` is broken in InvenTree image.**
The upstream `inventree/inventree:1.0.9` image's `init.sh` has shebang
`#!/bin/ash`, but the image is Debian-based and ships `/bin/bash` only
(no `/bin/ash`). Direct exec via `entrypoint: ["./init.sh", ...]` fails
with `cannot execute: required file not found`. Fix: invoke through
explicit `/bin/bash /home/inventree/init.sh` in our entrypoint wrapper
to bypass the broken shebang. Captured in compose comment.

**#19 — Redis cap_drop:[ALL] strips DAC_OVERRIDE; PID-1 root cannot
write redis-owned `/data` with default RDB snapshotting.** When we
override redis-alpine's entrypoint with `sh -c "exec redis-server ..."`,
we bypass docker-entrypoint.sh's `chown redis:redis /data` and `gosu`
demotion. PID-1 redis-server then runs as root and tries to write
RDB snapshots to `/data` (owned redis:redis 755), which fails because
cap_drop:[ALL] removed DAC_OVERRIDE. Surfaced as
`MISCONF Redis is configured to save RDB snapshots, but it's currently
unable to persist to disk` — InvenTree responses then fail with
HTTP 500 on cache writes. Fix: add `--save ''` to redis-server
invocation. Cache-only workload has no persistence requirement, so
this is doctrinally clean (vs. adding DAC_OVERRIDE which would be a
hardening regression). NetBox-redis avoids the issue via `--appendonly
yes` (different filename, succeeds), but pure cache here has no reason
to persist.

**#20 — InvenTree `init.sh` ends with `exec "$@"` — overriding
`entrypoint:` clears the inherited CMD-as-args path.** When compose
overrides `entrypoint:` for credential-sourcing, the image's default
`Cmd: ["sh","-c","exec gunicorn ..."]` is still inherited, but inside
the entrypoint wrapper, `"$@"` is empty unless we either (a) explicitly
set `command:` in compose, or (b) restructure the entrypoint to
not depend on `$@`. Chose (a) for explicitness and parity with the
upstream image's gunicorn invocation. Captured in compose comment.
Worker uses the same entrypoint wrapper but explicitly overrides
`command:` to `["invoke", "worker"]` — already correct.

**#21 — `docker exec` does NOT inherit PID-1 env from compose
entrypoint wrapper.** Diagnostics that need credentials (e.g.,
`manage.py shell` against the DB) must source `/vault/secrets/credentials.env`
themselves: `docker exec inventree bash -c 'set -a && . /vault/secrets/credentials.env && set +a && python manage.py ...'`.
This is the established netbox-redis healthcheck pattern.

## C6 follow-ups (added)

1. **InvenTree API token minting (2B prereq):** when 2B begins, mint a
   Django auth Token for the admin user (or provision a dedicated
   service account); populate `secret/inventree/api_token#token`;
   verify the entrypoint sources it into `INVENTREE_API_TOKEN` env
   for plugin use. The credentials.env.tmpl already guards on
   `if .Data.data.token`, so empty placeholder renders to empty
   string, which is safe.

2. **Plugin enablement (2B):** `inventree-supplier-panel` and
   `inventree-part-import` are pip-installed but disabled. Enabling
   requires admin login → System Settings → Plugins → toggle, OR
   programmatic enable via `manage.py` shell after 2B configures
   their settings (Mouser/DigiKey API keys read from
   `secret/inventree/{mouser,digikey}/*`).

3. **Caddy host.docker.internal port 8087 added but Caddyfile
   formatting hint surfaced on reload:** "Caddyfile input is not
   formatted; run `caddy fmt --overwrite` to fix inconsistencies"
   (line 5). Pre-existing, not introduced by 2A. Defer to a routine
   Caddyfile sweep.

4. **InvenTree healthcheck currently `curl /api/`** — works but
   exercises Redis cache and DB on each probe (every 15s). Consider
   moving to a lighter `/api/health/` endpoint if InvenTree exposes
   one in a future version. Not urgent.

## Increment 2B readiness

External prerequisites still required before 2B can begin:

| Prereq                | Status | Source                                  |
|-----------------------|--------|-----------------------------------------|
| Mouser API key        | ❌     | mouser.com → Account → API Keys         |
| DigiKey OAuth client  | ❌     | developer.digikey.com → Apps → register |
| 129-component CSV     | ❌     | user-supplied (preferred path or paste) |

### 2B kickoff trigger

Increment 2B opens when ALL three operator-side prereqs land:

1. Mouser API key in Vault at `secret/mouser/api#key`
2. DigiKey OAuth credentials in Vault at `secret/digikey/api`
   (`client_id` + `client_secret`)
3. 129-component CSV at `docs/inventory/components-2026-04.csv`

When all three are present, operator drafts Increment 2B execution
prompt against Block 4.D.3–4.D.6 scope. **No auto-resumption.**

When all three land:

1. Add Mouser/DigiKey paths to `inventree-policy.hcl` (read-only on
   `secret/data/inventree/{mouser,digikey}/*`).
2. Re-apply policy via `vault policy write inventree ...`.
3. Run a small extension to `provision-inventree.sh` to write the
   supplier credentials with hash-only logging.
4. Mint API token (C6 follow-up #1).
5. Enable plugins (C6 follow-up #2).
6. Run CSV import via `inventree-part-import` (4.D.3, A-012-bound).
7. Add NetBox cross-reference custom field on the InvenTree Part model
   (or the inverse: NetBox custom field referencing InvenTree IPN)
   per 4.D.6 design.

Increment 2B doctrine: A-012 (equivalence harness) MUST apply to 4.D.3
because CSV → InvenTree is a source-of-truth migration. A-013 (folded
gates) MAY apply to 4.D.5 if 4.D.4 (Mouser) is mechanically isomorphic.

## Commit plan

Two commits (split by concern):

1. `Phase 13 Increment 2A 4.D.2: InvenTree deploy + bootstrap`
   — `docker/inventree/docker-compose.yml` (Discovery #18-20 fixes)
   — `docs/phase-13/INCREMENT_2A_REGRESSION_FINAL_2026-04-29.log`

2. `docs(phase-13): Increment 2A closeout` — this document.
