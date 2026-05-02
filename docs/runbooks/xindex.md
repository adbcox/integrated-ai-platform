# xindex — Cross-Index Service Runbook

**Status:** Live (D-16-02 + D-16-02.0.5 + D-16-02.1 + D-16-02.2, opened 2026-05-01;
WP-17-04-05.5 flipped the project-tracker source from Plane to OpenProject 2026-05-02)
**Service location:** `docker/xindex/`
**Canonical URL:** `https://xindex.internal/` (Caddy reverse proxy + local-CA TLS)
**Loopback fallback:** `http://127.0.0.1:8095/` (preserved for local debugging)
**Container port:** 8000
**Host port:** `127.0.0.1:8095`
**Image:** `iap/xindex:0.4.0`
**Network:** `control-center-net`
**Vault dependency:** `vault-agent-xindex` sidecar renders NetBox + OpenProject
API tokens to `/run/secrets/netbox-credentials.env` and
`/run/secrets/openproject-credentials.env` via the `xindex` AppRole (policy:
`xindex-policy`, read-only on `secret/data/netbox/api_token` and
`secret/data/openproject/api`). xindex `depends_on: service_completed_successfully`
of the sidecar.
**NetBox CMDB entry:** `ipam.service` id 76 (`name=xindex`, `parent=mac-mini`)
**Ingestion sources:**
- **Repo-local (atomic rebuild):** `docs/adr/`, `docs/DECISION_REGISTER.md`,
  `docs/runbooks/`
- **External (per-source partial refresh):**
  - NetBox (`dcim.devices`, `ipam.services` + `service_dependencies`
    custom field links).
  - OpenProject (project versions + work packages; emits `tracked_in` links from
    local ADRs / deliverables / phases keyed by the WP `external_id` custom field).
  MCP wrapper is D-16-02.3.

## 1. Purpose

xindex is the structural enabler for autonomous coding. It serves as the
queryable view over the repo's authoritative documentation surface (ADRs,
the decision register, runbooks) so an automated coding loop can answer
"what does the platform say about X?" without re-walking markdown by hand.

The existing `scripts/cross-index-validate.py` (ADR ↔ OpenProject probe;
Plane-based predecessor retired in WP-17-04-05.5) is a different scope and
is not replaced by this service.

## 2. Architecture

```
                        Vault (vault-server :8200)
                              ▲
                              │  approle login
                              │
                  vault-agent-xindex (one-shot, exit_after_auth=true)
                              │  renders
                              ▼
              /Users/admin/.vault-agent-secrets/xindex/
                  netbox-credentials.env  (NETBOX_API_TOKEN)
                              │  bind-mounted ro at /run/secrets/
                              ▼
docs/  ──read-only mount──▶  xindex container  ──FTS5──▶  /data/xindex.db
                                  │   │
                                  │   └──pynetbox──▶ host.docker.internal:8084
                                  │
                                  └──FastAPI (uvicorn) on :8000
                                       ▲
                                       │  host.docker.internal:8095 (Caddy)
                                       │  127.0.0.1:8095 (loopback)
                                  Caddy ◀─── https://xindex.internal/
                                       ▲
                                  operator / MCP client
```

- Database: SQLite + FTS5 (porter unicode61 tokenizer)
- Persistence: named Docker volume `xindex_data`
- Ingest semantics:
  - Repo-local sources (adr/runbook/register) — atomic full rebuild
    via `db.reset_for_ingest()`. Small and fast.
  - External sources (netbox; openproject — was Plane in D-16-02.2,
    flipped to OpenProject in WP-17-04-05.5) — partial refresh per
    source via a snapshot-then-restore pattern (see §11). A failure in
    one external source NEVER wipes another's data.
- NetBox token: rendered by the `vault-agent-xindex` sidecar from
  `secret/data/netbox/api_token`. xindex reads it from
  `/run/secrets/netbox-credentials.env` at ingest time. The AppRole
  has read access to that one path only — adding new external
  sources extends `xindex-policy.hcl` with additional read paths,
  never broader capabilities.
- TLS: Caddy fronts xindex on `https://xindex.internal/` using its built-in
  local CA. Trust the CA on the client by extracting it once:
  `docker exec caddy cat /data/caddy/pki/authorities/local/root.crt > caddy-local-ca.crt`
  (header comment in `docker/caddy/Caddyfile`). The loopback URL stays
  available for local debugging without TLS.
- DNS: `xindex.internal` is provisioned in OPNsense Unbound (same place as
  every other `*.internal` hostname). If a host can resolve `grafana.internal`
  but not `xindex.internal`, the Unbound A-record is missing — add it under
  Services → Unbound DNS → Overrides pointing at `192.168.10.145`.

## 3. Endpoints

Canonical URL is `https://xindex.internal/`. The loopback URL
`http://127.0.0.1:8095/` is preserved as a debug fallback (no TLS, no
Caddy in the path).

```bash
# liveness + counts + last_ingest_at + per-source health (sources[])
curl -ksS https://xindex.internal/healthz | jq
# fallback: curl -s http://127.0.0.1:8095/healthz | jq

# Full ADR detail (accepts both A-014 and ADR-A-014 forms)
curl -ksS https://xindex.internal/adr/A-014 | jq
curl -ksS https://xindex.internal/adr/ADR-A-014 | jq

# Runbook detail (filename without .md)
curl -ksS https://xindex.internal/runbook/vault-recovery-from-shamir | jq

# Service / node detail (D-16-02.1 — sourced from NetBox)
curl -ksS https://xindex.internal/service/xindex     | jq
curl -ksS https://xindex.internal/node/mac-mini      | jq

# OpenProject work-package / version detail (was D-16-02.2 Plane endpoints;
# flipped in WP-17-04-05.5 — READ-ONLY per ADR-A-006).
# external_id is the human-stable key on the WP (e.g. ADR-A-006, D-17-04, Phase-17)
curl -ksS https://xindex.internal/workpackage/ADR-A-006      | jq
curl -ksS https://xindex.internal/version/Phase-17           | jq

# Entity-link query (D-16-02.1+) — any subset of the filters is optional
curl -ksS "https://xindex.internal/links?from_kind=service&link_type=depends_on"   | jq
curl -ksS "https://xindex.internal/links?to_kind=node&to_ref=mac-mini"             | jq
curl -ksS "https://xindex.internal/links?link_type=tracked_in&source=openproject"  | jq

# Search (FTS5 ranked); type ∈ {all, adr, runbook, register, service, node, workpackage}
curl -ksS "https://xindex.internal/search?q=NetBox&type=adr&limit=5"   | jq
curl -ksS "https://xindex.internal/search?q=caddy&type=service"        | jq
curl -ksS "https://xindex.internal/search?q=OpenProject&type=workpackage" | jq

# Trigger background re-ingest. Poll /healthz to see updated last_ingest_at
# (and per-source status flips if NetBox was unreachable).
curl -ksS -X POST https://xindex.internal/refresh | jq
```

The `-k` flag bypasses validation of the Caddy local CA certificate.
Once the CA is added to the client trust store (see §2 Architecture),
drop `-k` and use `curl -sS`.

## 4. Refresh cadence

There is no scheduled refresh in this deliverable. Re-ingest happens:
- on container start when the DB is empty,
- on explicit `POST /refresh`.

Adding a periodic refresh (e.g. cron sidecar, or filesystem watcher) is a
follow-up if the manual cadence proves operationally insufficient.

## 5. Common queries

```bash
# What does ADR-A-014 actually decide?
curl -ksS https://xindex.internal/adr/A-014 | jq -r '.sections.Decision'

# Which runbook covers Shamir recovery?
curl -ksS "https://xindex.internal/search?q=shamir&type=runbook" | jq

# Which ADRs touch the vault?
curl -ksS "https://xindex.internal/search?q=vault&type=adr" | jq '.results[].ref'
```

(Loopback equivalents — `http://127.0.0.1:8095/...` — work the same way
when the Caddy / DNS path is unavailable.)

## 6. Adding a new source ingester

There are two patterns depending on whether the source is repo-local
or external. The split is doctrine — see §11 for the partial-refresh
contract that external sources MUST honour.

### Repo-local source (mirrors `app/ingest/runbook.py`)

1. Add a module under `docker/xindex/app/ingest/<source>.py` that
   exposes `ingest(conn, root) -> int`. Upsert into a content table
   and insert the searchable text into `xindex_fts`.
2. Add the content table to `app/db.py`'s `SCHEMA` constant if needed;
   keep the schema additive.
3. Wire the new ingester into `_ingest_local()` in
   `app/ingest/__init__.py`.
4. Extend `app/db.py:counts()` and the `/healthz` response.
5. Add a fixture and a `test_ingest_<source>.py`.

### External source (mirrors `app/ingest/netbox.py` — D-16-02.1)

External sources are credentialed and may be unreachable; they MUST
NOT raise on failure and MUST NOT wipe other sources' data on
failure.

1. Add the consumer's secret path (read-only) to
   `config/vault-policies/xindex-policy.hcl`. NEVER broaden
   capabilities; NEVER add policy/AppRole modify paths.
2. Add a `<source>-credentials.env.tmpl` template under
   `docker/vault-agent-xindex/` and append a `template { ... }`
   block to `agent.hcl`. Token is rendered to
   `/run/secrets/<source>-credentials.env`.
3. Add a module `app/ingest/<source>.py` exposing
   `ingest(conn, *, fetcher=None) -> <Result>`. The function MUST:
   - read the token from the rendered env file (not argv);
   - return a result object on failure rather than raising;
   - never log token values;
   - inject all I/O via `fetcher` so unit tests don't hit the network.
4. Add `_ingest_<source>()` to `app/ingest/__init__.py` using the
   snapshot-then-restore pattern (see `_snapshot_netbox` /
   `_restore_netbox`). On failure: restore the snapshot, set
   `set_source_status('<source>', 'error', error=...)`, return.
5. Extend `db.LOCAL_SOURCES` / `EXTERNAL_SOURCES`, `reset_source()`,
   and `db.counts()` with any new tables.
6. Add `test_ingest_<source>.py` and (critically) extend
   `test_partial_refresh.py` with a "<source> failure preserves
   prior rows + does not affect other sources" case.

## 7. Debugging ingest failures

```bash
# container logs (uvicorn prints stack traces from the lifespan ingest)
docker logs xindex --tail 100

# inspect the live DB inline
docker exec -it xindex sh -lc 'python -c "
import sqlite3, json
c = sqlite3.connect(\"/data/xindex.db\")
c.row_factory = sqlite3.Row
print(\"adrs:\",  c.execute(\"SELECT COUNT(*) FROM adrs\").fetchone()[0])
print(\"runbooks:\", c.execute(\"SELECT COUNT(*) FROM runbooks\").fetchone()[0])
print(\"meta:\", dict(c.execute(\"SELECT key,value FROM meta\").fetchall()))
"'

# force a clean rebuild
curl -s -X POST http://127.0.0.1:8095/refresh
sleep 2
curl -s http://127.0.0.1:8095/healthz | jq '.last_ingest_at, .counts'
```

If the ADR ingester reports a count lower than the number of files, the
likeliest cause is a header-format outlier — both the bolded-field and
the section-style ("## Status") forms are supported, anything else needs
parser extension.

## 8. Recovery

The DB is rebuildable from the repo. To recover from corruption:

```bash
docker compose -f docker/xindex/docker-compose.yml down
docker volume rm xindex_data
docker compose -f docker/xindex/docker-compose.yml up -d
# lifespan ingest runs automatically on first request to /healthz
```

Backups are not required: source of truth is git.

## 9. Tests

```bash
cd docker/xindex
python3.12 -m venv .venv
.venv/bin/pip install -r app/requirements.txt
.venv/bin/python -m pytest app/tests/ -v
```

41 tests cover:
- ADR parsing (both header styles), runbook ingest, decision-register
  parsing
- The HTTP endpoints (healthz, adr, runbook, search, refresh) on
  repo-local data
- NetBox ingester (`test_ingest_netbox.py` — pynetbox stubbed via the
  `fetcher=` injection point)
- OpenProject ingester (`test_ingest_openproject.py` — OpenProject
  HAL JSON stubbed via the `fetcher=` injection point; covers
  external_id mapping, missing-credentials skip, no-link path)
- The partial-refresh doctrine (`test_partial_refresh.py` — proves a
  NetBox or OpenProject failure on a re-ingest preserves prior rows
  AND does not affect any other source, including the ADR / runbook /
  register triple)
- The `/service`, `/node`, `/links` endpoints + per-source health
  on `/healthz`
- The `/workpackage/{external_id}` and `/version/{name}` endpoints
  plus ADR `workpackage_tracking` populated from the `tracked_in`
  entity_link.

Tests build a synthetic `/docs` tree and never touch the real repo
content or NetBox.

## 10. Why repo-files-only was the foundation

D-16-02 shipped the foundation. The autonomous-coding meta-goal needs
the *structural* piece — a queryable index that exists, persists, and
serves JSON — before extending it to remote sources. Each external
source needs its own credential plumbing and rate-limit story;
bundling them into the foundation would force three un-hardened paths
into the same review. They are deferred to:

- **D-16-02.1 — DONE 2026-05-01.** NetBox ingestion: `dcim.devices`
  + `ipam.services` + entity_links derived from the
  `service_dependencies` custom field. Vault AppRole `xindex` reads
  `secret/data/netbox/api_token` only.
- **D-16-02.2 — DONE 2026-05-01; substrate flipped 2026-05-02 in
  WP-17-04-05.5.** OpenProject ingestion (versions + work packages,
  read-only per ADR-A-006). Emits `tracked_in` entity_links from
  local ADRs / deliverables / phases to OpenProject work packages,
  keyed by the WP `external_id` custom field. `xindex-policy`
  extended with `secret/data/openproject/api` read; rendered to
  `/run/secrets/openproject-credentials.env`. Plane was the original
  substrate (D-16-02.2); see WP-17-04-05.5 + ADR-A-006 for the flip
  rationale.
- **D-16-02.3** — MCP tool wrapper so Claude Code agents can query
  xindex.

**D-16-02.0.5 — DONE 2026-05-01.** Caddy site block at
`docker/caddy/Caddyfile` reverse-proxies `https://xindex.internal/` to
`host.docker.internal:8095`. xindex registered in NetBox CMDB as
`ipam.service` id 76 on the `mac-mini` device.

## 11. Partial-refresh doctrine

External sources refresh independently. Each external ingester runs
under a snapshot-then-restore wrapper in `_ingest_netbox()` /
`_ingest_<source>()` — the prior rows are captured, the source rows
are wiped, and the ingester runs. On any failure (network outage,
auth error, schema mismatch, mid-run exception) the snapshot is
restored verbatim and `set_source_status('<source>', 'error', ...)`
records the failure for `/healthz`.

Three guarantees follow:

1. **No external source ever wipes another's data.** Two external
   sources never share a snapshot.
2. **A failed external never wipes its own healthy data.** Stale rows
   survive the failure and are visible to consumers, with the staleness
   surfaced through `/healthz`'s `sources[].status` field.
3. **An external failure never breaks repo-local ingest.** Local
   sources are atomic and run before any external; their ingest is
   independent of any external outcome.

This is the inverse of D-16-02's foundation, which used a single
`reset_for_ingest()` wipe across all sources. That model was correct
for the foundation (only repo files; rebuilds are cheap and atomic)
and incorrect once externals enter — a NetBox outage during a refresh
would otherwise drop the ADR index too. D-16-02.1 separated the two
concerns explicitly.

`/healthz` returns:
```jsonc
{
  "status": "ok",
  "last_ingest_at": "2026-05-01T12:34:56Z",
  "counts": {"adrs": 14, "runbooks": 32, ..., "services": 17, "nodes": 4},
  "sources": [
    {"source": "adr",     "last_ingest_at": "...", "status": "ok",    "error": ""},
    {"source": "netbox",  "last_ingest_at": "...", "status": "error", "error": "netbox unreachable or auth failed"}
  ]
}
```

A `status` of `error` means the most recent re-ingest of that source
failed; the rows shown are from the previous successful run.

## 12. Vault-agent dependency

The xindex container `depends_on: vault-agent-xindex` with
`condition: service_completed_successfully`, so xindex starts only
after the sidecar has authenticated and rendered both
`/Users/admin/.vault-agent-secrets/xindex/netbox-credentials.env` and
`/Users/admin/.vault-agent-secrets/xindex/openproject-credentials.env`.
The sidecar is `restart: "no"` and exits cleanly after rendering.

If the sidecar fails (Vault sealed, AppRole revoked, template error)
xindex never starts. To diagnose:

```bash
docker logs vault-agent-xindex --tail 50
ls -la /Users/admin/.vault-agent-secrets/xindex/
# Expect: .vault-token (sink) + netbox-credentials.env +
#         openproject-credentials.env (templates).
# Token values never appear in logs or stdout.
```

Restart sequence (when re-rendering credentials after a Vault rotation):
```bash
docker compose -f docker/xindex/docker-compose.yml down
docker compose -f docker/xindex/docker-compose.yml up -d
# Sidecar runs, exits 0, then xindex starts.
```

The AppRole role-id and secret-id live at
`/Users/admin/.vault-approle/xindex/{role-id,secret-id}` (mode 0600).
If they are lost, re-issue via the Vault root token:
```bash
vault read -field=role_id auth/approle/role/xindex/role-id
vault write -f -field=secret_id auth/approle/role/xindex/secret-id
```
and re-write the files at the same paths.

## 13. OpenProject source (D-16-02.2; substrate flipped in WP-17-04-05.5)

xindex consumes OpenProject state but never writes back. ADR-A-006
fixes the project framework markdown (`docs/PROJECT_FRAMEWORK.md`) as
the sole source of truth for deliverable rollup; OpenProject is the
operational overlay populated by
`scripts/openproject-sync-from-framework.py`. xindex is a third reader
downstream of both. (Plane was the original operational substrate —
D-16-02.2 — and was retired together with this flip; see
WP-17-04-05.5 and ADR-A-006 for the migration rationale.)

### What gets ingested

- **Versions** (`op_versions` table) — every version in the project,
  keyed by `name` with the OpenProject id carried over. Versions
  replace the Plane Modules surface; the WP↔version association is
  parsed from `_links.version.href`.
- **Work packages** (`op_workpackages` table) — every WP whose
  `external_id` custom field is non-empty. WPs without an
  `external_id` are skipped (they are operational-only and have no
  canonical local artifact). The status link is denormalized to its
  name; the version link is denormalized to `version_name`.
- **Tracked-in links** (`entity_links` rows with
  `link_type='tracked_in'`, `source='openproject'`) for WPs whose
  `external_id` matches one of:
  - `ADR-A-NNN`     → `from_kind='adr'`
  - `D-NN-MM[.x]`   → `from_kind='deliverable'`
  - `Phase-NN`      → `from_kind='phase'`

  Other prefixes are ingested into `op_workpackages` but emit no link.

### Failure isolation

The OpenProject ingester walks the project's `/versions`, system-wide
`/statuses`, and the project-filtered `/work_packages` (paged at
100/page) sequentially, no parallelism. Network errors, auth
failures, schema mismatches, or any uncaught exception inside
`_default_fetcher` are caught: the ingester never raises, the
`_ingest_openproject()` snapshot/restore wrapper rewrites the prior
data, and `set_source_status('openproject', 'error', ...)` is
recorded for `/healthz`. Other sources (ADRs, runbooks, register,
NetBox) are unaffected. On the next `/refresh` cycle, if the call
succeeds, the status flips back to `ok` and rows refresh.

### Why no `deliverables` table

A natural temptation is to give xindex its own deliverables table
populated from OpenProject. We deliberately don't:
`docs/PROJECT_FRAMEWORK.md` is the canonical record for deliverable
scope and status (ADR-A-006). Adding a second authoritative
deliverable list inside xindex would make OpenProject drift visible
but ambiguous about which side is correct. Instead, xindex parses the
framework markdown for nothing (yet) and emits `tracked_in` links so
consumers can look up "for ADR-A-006, which OpenProject WP, in which
state?" without ever calling OpenProject directly.

If a future deliverable-aware view is needed, the right shape is
parsing `PROJECT_FRAMEWORK.md` directly (a fourth repo-local source),
NOT mirroring OpenProject's rollup. That would preserve
repo-canonical truth and reduce OpenProject to what it already is —
an operational layer.

### Health output

`/healthz` reports `openproject` alongside the other sources:

```jsonc
{
  "sources": [
    {"source": "openproject", "status": "ok",      "last_ingest_at": "2026-05-02T..."},
    {"source": "openproject", "status": "error",   "error": "openproject /work_packages: HTTP 502"},
    {"source": "openproject", "status": "unknown", "error": "no OpenProject credentials available"}
  ]
}
```

`unknown` means the credential file was not rendered (sidecar issue
or policy mismatch) — see §12.
