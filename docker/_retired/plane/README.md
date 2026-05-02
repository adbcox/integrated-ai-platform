# Plane CE — Retired (D-17-04 / WP-17-04-06)

**Retirement date:** 2026-05-02
**Replaced by:** OpenProject CE (`docker/openproject/`,
`https://openproject.internal/`, project identifier `roadmap`)
**Deliverable:** D-17-04 — Plane → OpenProject migration
**Migration ADR:** `docs/adr/ADR-A-018-replace-plane-with-openproject.md`

## What was retired

Containers (all stopped + removed at retirement):

- `docker-plane-api-1`     (makeplane/plane-backend:stable)
- `docker-plane-web-1`     (makeplane/plane-frontend:stable)
- `docker-plane-worker-1`  (makeplane/plane-backend:stable)
- `docker-plane-beat-1`    (makeplane/plane-backend:stable)
- `docker-plane-db-1`      (postgres:15-alpine)
- `docker-plane-redis-1`   (redis:7.2-alpine)
- `docker-plane-minio-1`   (minio/minio:latest)
- `vault-agent-plane-{api,worker,beat,db,minio}` (sidecars)

Compose definition:        `docker-compose-plane.yml` (parked here)
Vault Agent configs:       `vault-agent-plane-{api,worker,beat,db,minio}/`
                            (parked here)
Reverse-proxy nginx:       `plane-nginx/` (parked here; the production
                            path used Caddy directly, but the bundled
                            nginx config remains for reference)
Caddy route removed:       `plane.internal { reverse_proxy
                            host.docker.internal:3001 }` deleted from
                            `docker/caddy/Caddyfile`; Caddy reloaded
                            2026-05-02

Docker volumes left **in place** for restoration safety (cheap to
retain, expensive to recreate):

- `docker_plane-db-data`    (PostgreSQL dataset)
- `docker_plane-logs`
- `docker_plane-minio-data`
- `docker_plane-redis-data`

The `docker_plane-net` Docker network remains attached to three Obot
containers (`obot`, `sms1obot-mcp-server`, `sms1obot-mcp-server-shim`)
that joined it at some prior point. Obot is a managed-lifecycle
service per CLAUDE.md (D#30); detaching the network is out of scope
for this retirement and would require Obot reconfiguration. Cost of
keeping the network is zero.

## Forensic snapshot locations

Authoritative copies of Plane state at the moment of cutover, taken
in WP-17-04-02 (2026-05-02):

| Artifact          | Path                                                         | Size   | Notes                                |
|-------------------|--------------------------------------------------------------|--------|--------------------------------------|
| SQL dump (gzip)   | `~/plane-final-snapshot/plane-final-snapshot-2026-05-02.sql.gz` | 654 KB | `pg_dump` of `docker-plane-db-1`     |
| Snapshot manifest | `docs/_archive/plane-final-snapshot-2026-05-02.manifest`     | small  | Hash + checksum + table row counts   |
| Structured JSON   | `docs/_archive/plane-export-2026-05-02.json`                 | 1.0 MB | Workspaces, projects, modules, issues, states, members |

**WARNING — sensitive content in the SQL dump.** The SQL snapshot
contains:

- Live Plane API tokens (worth nothing post-retirement, but token
  half-life is short rather than zero)
- bcrypt password hashes for any Plane user accounts created at the
  instance

This file should be either:

1. Moved to encrypted offline storage (recommended), OR
2. Deleted on or after **2026-06-01** (30-day forensic retention
   window — see operator follow-up note in WP-17-04-06 commit body)

The structured JSON does not contain credential material.

## Vault path retention

The `secret/plane/*` KV paths are **kept in Vault for 30 days** as a
forensic safety net. Schedule for deletion: **on or after 2026-06-01**.

Paths to delete at end of retention:
- `secret/plane/api`
- `secret/plane/db`
- `secret/plane/minio`
- (any other `secret/plane/*` paths discoverable via
  `vault kv list secret/plane/` at deletion time)

The `xindex-policy` and `vault-agent-xindex` template no longer reference
any `secret/data/plane/*` path (cut over in WP-17-04-05.5, commit
`32b7ad0`); deletion will not affect any running consumer.

## Restoration procedure (high cost — re-evaluate before invoking)

If a regression in OpenProject forces a fallback to Plane CE, the
parked compose can be restored. Cost of restoration is high
(re-bootstrapping the stack, re-issuing AppRoles, re-syncing the
framework, re-pointing xindex) and should NOT be done without:

1. A documented decision (new ADR superseding ADR-A-018), AND
2. Confirmation that the SQL snapshot has not been deleted, AND
3. The 30-day Vault retention window for `secret/plane/*` paths has
   not lapsed.

If those conditions hold:

```bash
# 1. Restore the parked compose to its working location
git mv docker/_retired/plane/docker-compose-plane.yml \
       docker/docker-compose-plane.yml
git mv docker/_retired/plane/vault-agent-plane-* docker/
git mv docker/_retired/plane/plane-nginx docker/

# 2. Bring the stack up (volumes are still in place)
cd docker && docker compose -f docker-compose-plane.yml up -d

# 3. Restore SQL state if volumes were also wiped
gunzip -c ~/plane-final-snapshot/plane-final-snapshot-2026-05-02.sql.gz \
  | docker exec -i docker-plane-db-1 psql -U plane -d plane

# 4. Restore the Caddy route — re-add the plane.internal block to
#    docker/caddy/Caddyfile (see git history of that file at the
#    WP-17-04-06 commit) and reload caddy.

# 5. Re-enable any consumers that were flipped off Plane in
#    WP-17-04-05.5 (xindex source registry, scripts/openproject-* tooling).
```

## Why Plane was retired

Captured fully in `docs/adr/ADR-A-018-replace-plane-with-openproject.md`.
One-line: Plane CE's data model lacks the work-package / change-record
primitive needed for the platform's PMP+ITIL workflow, the rate limit
made bulk sync brittle, and the ingestion schema constrained xindex.
OpenProject offered direct fits for all three. See the ADR for the
full migration timeline and what was preserved vs. retired.
