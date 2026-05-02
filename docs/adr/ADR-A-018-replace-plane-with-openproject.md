# ADR-A-018 — Replace Plane CE with OpenProject CE as PM substrate

**Status:** Accepted
**Date:** 2026-05-02
**Phase:** 17
**Deliverable:** D-17-04
**Supersedes:** Plane CE as the PM substrate of record (ingestion target
for `xindex`, source-of-truth for D-* / WP-* / ADR-* records, target
for `scripts/openproject-sync-from-framework.py`'s predecessor
`scripts/plane-sync-from-framework.py`).

## Context

Plane CE was deployed earlier in the platform's lifecycle to be the
project-management substrate: a single canonical store for the PMP+ITIL
identifiers (D-NN-MM deliverables, ADR-A-NNN architecture decisions,
phase rollups) and the destination that `xindex` ingested for the
project-state side of the cross-index. Phase 17's planning surfaced
four structural problems that compounded as the framework matured:

1. **No work-package primitive.** Plane's data model has Issues,
   Modules, and Cycles. The PMP+ITIL framework records work as
   *work packages* with a defined lifecycle (NOT STARTED → IN
   PROGRESS → DONE) and a stable external identifier (`D-NN-MM`,
   `WP-NN-MM-XX`). Mapping work packages to Plane Issues required a
   convention (use the Issue title as the identifier) that broke
   when Plane's UI users edited titles, that couldn't carry the
   `phase` / `parent-deliverable` axes natively, and that left no
   place for change-record fields.

2. **No change-record / change-management workflow.** ITIL change
   records (the "C" side of PMP+ITIL) need approval state, risk
   classification, and an audit-stamped close. Plane has none of
   these built in. Approximating them with custom Issue properties
   was possible but every framework-side script had to encode the
   convention, and the convention couldn't be enforced in the UI
   for users editing records by hand.

3. **Constrained xindex schema.** `xindex` mirrored Plane state into
   `plane_issues` and `plane_modules` tables. Those names + their
   shapes leaked Plane's data model across the whole xindex schema
   and the FTS5 `kind` enum (`'plane_issue'`). Any future PM substrate
   change required a forced rewrite of xindex schema, ingestion code,
   `xindex-mcp` tool surface, and consumer code (the framework's
   `openproject-sync-*` scripts and the `xindex_get_plane()` MCP
   tool). The schema was actively coupling the platform to Plane.

4. **Rate limit + bulk-sync brittleness.** Plane CE's API rate limit
   triggered HTTP 429 on framework-side bulk syncs; the sync scripts
   had to implement back-off and retry to make a 31-record reconcile
   reliable. The same operation against OpenProject's HAL JSON API v3
   completes in one pass.

These issues were not individually fatal, but together they meant
that adding a single new framework field (e.g. risk classification
on a work package) would touch Plane's UI conventions, the framework
sync script, the xindex schema, the xindex ingestion code, the
xindex-mcp tool surface, and any read-side consumer. That coupling
made Phase 17's planned change-management work prohibitively
expensive on the Plane substrate.

## Decision

Replace Plane CE with OpenProject CE as the PM substrate of record.
OpenProject's data model directly fits the framework:

- **Work Package** primitive with native `external_id` custom field
  carrying `D-NN-MM` / `WP-NN-MM-XX` / `ADR-A-NNN` / `Phase-NN`.
- **Version** primitive carrying `Phase-NN` rollups (formerly Plane
  Modules, now native to the data model).
- **Status** is first-class with workflow per work-package type;
  PMP+ITIL states map directly without convention encoding.
- **HAL JSON API v3** is rate-limit-friendly for bulk sync.
- **Change records** addressable via a future custom WP type without
  schema churn — fields are per-type, not per-instance conventions.

xindex's read-only mirror was renamed `op_workpackages` /
`op_versions` (replacing `plane_issues` / `plane_modules`); the FTS5
`kind` enum gained `'workpackage'` and dropped `'plane_issue'`.
Ingestion uses the OpenProject HAL JSON API via a sidecar that reads
`secret/data/openproject/api` from Vault.

## Migration timeline (three phases)

The migration ran as `D-17-04` over a single sprint window in late
April / early May 2026:

- **WP-17-04-01 — OpenProject deployment** (commit `dd9e637`).
  OpenProject CE container, `roadmap` project provisioned, Caddy
  route `openproject.internal` added.
- **WP-17-04-01.5 — Identifier convention correction** (commit
  `c91a3a4`). Pre-flight: locked the `D-NN-MM` / `WP-NN-MM-XX`
  / `ADR-A-NNN` / `Phase-NN` external-id convention before any
  data was written.
- **WP-17-04-02 — Plane data export + DB snapshot** (commit
  `<see git log>`). pg_dump of Plane DB → `~/plane-final-snapshot/`
  + structured JSON export → `docs/_archive/`.
- **WP-17-04-03 — Data import + structure mapping** (commit
  `37f874c`). Plane snapshot transformed and imported into
  OpenProject; identifiers preserved on the External ID custom field.
- **WP-17-04-04 — Tooling rewrite** (commit `d283fa1`). Connector
  + mint scripts rewritten against OpenProject's HAL JSON API.
  `scripts/openproject-sync-from-framework.py` replaces the
  Plane-side equivalent. Old Plane-side scripts retained for
  one-cycle audit window (do not delete until cycle close).
- **WP-17-04-05 — Repo reference sweep** (commit `abbbba8`).
  266 file references swept Plane → OpenProject; `xindex_get_plane`
  preserved as deprecated MCP alias for one cycle.
- **WP-17-04-05.5 — xindex source flip** (commit `32b7ad0`).
  xindex schema renamed `plane_issues` / `plane_modules` →
  `op_workpackages` / `op_versions`; FTS5 kind enum updated; new
  Vault Agent template `openproject-credentials.env.tmpl`;
  `xindex-policy` Vault policy updated to read
  `secret/data/openproject/api` instead of `secret/data/plane/api`.
- **WP-17-04-06 — Plane retirement** (commit `2f6cc32`).
  Plane CE containers + 5 vault-agent sidecars stopped and removed.
  Compose / nginx / template tree parked under
  `docker/_retired/plane/`. `plane.internal` Caddy route removed,
  Caddy reloaded. Volumes + `docker_plane-net` retained for
  restoration safety. `secret/plane/*` Vault paths kept 30 days
  for forensic retention (deletion-after 2026-06-01).

## What was preserved (forensic retention)

- **SQL dump** at `~/plane-final-snapshot/plane-final-snapshot-2026-05-02.sql.gz`
  (654 KB). Contains live Plane API tokens + bcrypt password
  hashes; operator follow-up: encrypt-offline or delete on/after
  2026-06-01. Rationale captured in `docker/_retired/plane/README.md`.
- **Snapshot manifest** at `docs/_archive/plane-final-snapshot-2026-05-02.manifest`
  (table row counts, hashes).
- **Structured JSON export** at `docs/_archive/plane-export-2026-05-02.json`
  (1.0 MB). No credential material; safe to retain indefinitely.
- **Vault paths** `secret/plane/{api,db,minio}` kept 30 days
  (deletion-after 2026-06-01); audit-window safety net.
- **Docker volumes** `docker_plane-{db-data,logs,minio-data,redis-data}`
  retained — cheap to keep, expensive to recreate; restoration
  prerequisite.

## What was retired

- **7 Plane CE containers**: api, web, worker, beat, db (postgres),
  redis, minio.
- **5 Vault Agent sidecars**: `vault-agent-plane-{api,worker,beat,db,minio}`.
- **Compose definition** `docker-compose-plane.yml` (parked).
- **Reverse-proxy** nginx config (parked; the production path
  used Caddy, but the bundled nginx config remains for reference).
- **Caddy route** `plane.internal { reverse_proxy host.docker.internal:3001 }`
  (deleted from `docker/caddy/Caddyfile` in WP-17-04-06).
- **xindex Plane-side schema**: tables `plane_issues`, `plane_modules`
  dropped via idempotent `drop_legacy_plane_tables()`; FTS5
  `kind = 'plane_issue'` rows deleted.
- **Vault policy reference** to `secret/data/plane/api` in
  `xindex-policy.hcl` (replaced with `secret/data/openproject/api`
  in WP-17-04-05.5).

## Cost of migration

The full D-17-04 chain was eight sequenced commits over a single
working week. The largest single chunk (WP-17-04-05 reference
sweep) touched 266 files; mechanical and reviewable. The xindex
flip (WP-17-04-05.5) required guarded handling for an existing
test-fixture ordering bug (FTS5 DELETE before `init_schema`),
fixed in the same commit with a `sqlite_master` table-existence
check. Total operator interrupt time: well under the 90-minute
hard cap on the teardown + framework-flip combined window.

The retirement was zero-downtime for downstream consumers: xindex's
`/healthz` showed 5/5 sources OK with 668 op_workpackages
immediately before *and* after Plane container teardown, confirming
the WP-17-04-05.5 cutover had already moved the read path to
OpenProject before any Plane retirement work began.

## Restoration cost (high; documented gate)

If a regression in OpenProject forces a fallback to Plane CE, the
parked compose can be restored. Cost is high (re-bootstrapping the
stack, re-issuing AppRoles, re-syncing the framework, re-pointing
xindex) and is gated on a superseding ADR + integrity of the SQL
snapshot + the 30-day Vault retention window not having lapsed.
Procedure documented in `docker/_retired/plane/README.md`.

## Consequences

- **Single PM substrate of record**: OpenProject at `openproject.internal`
  (`http://192.168.10.145:8086`), project identifier `roadmap`. Read
  path is `secret/data/openproject/api` (xindex consumer);
  write path is the framework's `openproject-sync-from-framework.py`.
- **xindex schema is no longer Plane-shaped**. Adding a new PM
  substrate in the future is a per-source change, not a cross-cutting
  rewrite.
- **Read-only consumer doctrine preserved** (per ADR-A-006): xindex
  never writes to OpenProject. The framework writes to OpenProject;
  OpenProject writes to itself; xindex mirrors only.
- **One-cycle deprecation window** for the Plane-side scripts and the
  `xindex_get_plane` MCP alias. Both will be removed after the audit
  cycle closes (operator follow-up; not a blocker for D-17-04 close).
- **Forensic retention has a hard cutover date**: 2026-06-01. After
  that date the SQL snapshot and `secret/plane/*` paths must be
  deleted (or, in the snapshot's case, moved to encrypted offline
  storage). This ADR is the authority on that retention window.

## References

- `docker/_retired/plane/README.md` — retirement record (containers,
  volumes, network, retention dates, restoration procedure)
- `docs/runbooks/xindex.md` — ingestion runbook (now OpenProject-shaped)
- `docs/runbooks/xindex-mcp.md` — MCP tool reference (now exposes
  `xindex_get_workpackage`; `xindex_get_plane` deprecated alias)
- ADR-A-006 — xindex read-only mirror doctrine (still load-bearing)
- ADR-A-014 — NetBox CMDB authority (parallel pattern: external system
  is authority, xindex mirrors)
- D-17-04 (framework row in `docs/PROJECT_FRAMEWORK.md` §9)
