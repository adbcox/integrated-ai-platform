# OpenProject — canonical PM substrate

**Deployed:** 2026-05-01 (Phase 17 deliverable 17.D)
**Replaces:** Plane CE (retired 2026-05-01 in 17.D WP-06)
**ADR:** TBD (authored in 17.D WP-05)

---

## Why OpenProject

Plane CE's stack-level mismatch (documented in 17.A stack-audit and
17.D plan):

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

After first start:

1. Visit https://openproject.internal — log in as
   `admin@example.net` with the password from
   `secret/openproject/admin`.
2. Generate API token: My Account → Access tokens → Generate.
3. Store under `secret/openproject/api` as `{token: "<value>"}`.
4. Restart `openproject` so the Vault Agent re-renders
   `credentials.env` with `OPENPROJECT_API_TOKEN`.

---

## Connector authoring prerequisites (WP-17-D-04)

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
   (replacing the admin-scoped token populated in WP-01 T1.7).
4. **Reset the admin user's API key** (regenerate, do not store) so
   the broad-scope token from T1.7 stops being a long-lived
   high-privilege credential floating around.

Reasoning: WP-04 is the right time to switch because that's when
the connector's exact API surface is first known — scoping the
role to actual usage avoids both over-permissioning (security) and
under-permissioning (forced re-grants mid-development).

---

## Migration from Plane

See:

- `docs/_archive/plane-final-snapshot-2026-05-01.sql` — forensic
  Plane DB dump
- `framework/openproject_connector.py` — Plane connector replacement
  (17.D WP-04)
- `scripts/openproject-sync-from-framework.py` — sync replacement
  (17.D WP-04)
- `docker/_retired/plane/README.md` — Plane retirement record
  (17.D WP-06)

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
