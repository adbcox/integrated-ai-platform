# OpenProject — canonical PM substrate

**Deployed:** 2026-05-01 (Phase 17 deliverable D-17-04)
**Replaces:** Plane CE (retired 2026-05-01 in D-17-04 WP-17-04-06)
**ADR:** TBD (authored in D-17-04 WP-17-04-05)

---

## Why OpenProject

Plane CE's stack-level mismatch (documented in D-17-01 stack-audit and
D-17-04 plan):

- API rate limits — 60/min hit during D-16-02.A
- No work-package primitive — PMP+ITIL framework uses WP-NN-MM-XX
- No change-record workflow — framework uses CR-NN-NNN
- Constrained xindex schema mapping
- Plane was a Linear-clone marketed as Jira-replacement

OpenProject covers all gaps:

- Work packages first-class (matches WP-NN-MM-XX)
- Change management built-in (matches CR-NN-NNN)
- Phases/Versions concept (matches Phase-NN structure)
- Permissive API (~100 req/sec vs Plane's 60/min)
- PostgreSQL-backed (familiar substrate)
- Active OSS development; GPLv3

---

## Reachable at

- `openproject.internal` (via Caddy)
- `http://192.168.10.145:8086` (direct host port)

---

## Vault paths

```
secret/openproject/admin       — admin user creds (email, password)
secret/openproject/db          — PostgreSQL user creds (username, password)
secret/openproject/secret_key  — Rails SECRET_KEY_BASE
secret/openproject/api         — API token (created post-deploy)
```

AppRole: `openproject` (policy:
`config/vault-policies/openproject-policy.hcl`)

Credentials reach the container via `vault-agent-openproject` sidecar
writing to `/Users/admin/.vault-agent-secrets/openproject/credentials.env`,
which both `openproject` and `openproject-db` source on entrypoint.

---

## Lifecycle

```bash
cd docker/openproject
docker compose up -d         # start
docker compose ps            # status
docker compose logs -f openproject     # follow logs
docker compose down          # stop (volumes preserved)
```

---

## Initial admin + API token

The admin user is seeded from `secret/openproject/admin` on first
boot (Vault Agent renders `OPENPROJECT_ADMIN_*` env into the
container's credentials.env).

The admin API token is minted programmatically via:

```bash
./scripts/openproject-mint-admin-token.sh
```

This script:

1. Resolves an admin Vault token via `scripts/lib/vault-admin-token.sh`
2. Checks `secret/openproject/api#token` — if present and validates
   against `/api/v3/users/me`, exits 0 (idempotent).
3. Otherwise, mints a fresh token via `APITokens::CreateService`
   inside the `openproject` container (Rails runner), captures the
   plaintext `plain_value` (only available at creation time), and
   patches it into Vault.
4. Verifies the new token authenticates against `/api/v3/users/me`.
5. Hash-only logging throughout (sha256[12]); token never appears
   in argv, shell history, or stdout.

No operator UI interaction required. Safe to re-run after rebuilds.

**Token implementation surprise (recorded for WP-17-04-04 author):**

OpenProject 15 emits an `INFO -- : Increasing database pool size`
line directly to stdout during Rails boot — bypasses
`Rails.logger.level=FATAL` (the message is from OpenProject itself,
not Rails.logger). Rails-runner-based tooling that captures token
output via `STDOUT.write(plain)` will get a contaminated capture.
The mint script wraps the token in `__IAP_TOKEN_BEGIN__` /
`__IAP_TOKEN_END__` sentinels and extracts shell-side. Use the same
pattern in `openproject_connector.py` if it ever shells into the
container.

---

## Connector authoring prerequisites (WP-17-04-04)

**Read before writing `framework/openproject_connector.py`.**

OpenProject 15 has a single per-user API access key (no per-token
scopes — the `Reset` action regenerates the user's one key, and that
key acts with the user's full permissions). The only way to scope
down a connector's blast radius is at the **user-account** level,
not at the token level.

Before authoring the connector auth flow:

1. **Create a dedicated low-privilege user** `iap-sync` with a
   custom role granting only the minimum permissions the sync
   actually needs — work-package CRUD, version create, custom-field
   read/write. No admin, no user-management, no project-create.
2. **Reset that user's API key** and capture the value.
3. **Store at `secret/openproject/api`** under the `token` field
   (replacing the admin-scoped token populated in WP-17-04-01 T1.7).
4. **Reset the admin user's API key** (regenerate, do not store) so
   the broad-scope token from T1.7 stops being a long-lived
   high-privilege credential floating around.

Reasoning: WP-17-04-04 is the right time to switch because that's when
the connector's exact API surface is first known — scoping the
role to actual usage avoids both over-permissioning (security) and
under-permissioning (forced re-grants mid-development).

---

## Migration from Plane

See:

- `docs/_archive/plane-final-snapshot-2026-05-01.sql` — forensic
  Plane DB dump
- `framework/openproject_connector.py` — Plane connector replacement
  (D-17-04 WP-17-04-04)
- `scripts/openproject-sync-from-framework.py` — sync replacement
  (D-17-04 WP-17-04-04)
- `docker/_retired/plane/README.md` — Plane retirement record
  (D-17-04 WP-17-04-06)

---

## Ports & resource budget

| Service             | Port (host)  | Memory limit  |
|---------------------|--------------|---------------|
| openproject (web)   | 8086 → 8080  | 2 GB          |
| openproject-db      | (internal)   | 512 MB        |
| openproject-cache   | (internal)   | 96 MB         |
| **Total**           |              | **~2.6 GB**   |

(For comparison, retired Plane stack was ~1.5 GB across 7 containers.
Net cost of the substrate upgrade: ~1.1 GB RAM — covered easily on
the M4 Pro 48 GB.)
