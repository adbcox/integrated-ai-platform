# Phase 13 Block 4.C C5.2 — Consumer Migration Evidence

**Date:** 2026-04-29
**Scope:** Migrate the three consumers of `config/service-registry.yaml`
to read from NetBox via the shared `scripts/cmdb_source.py` loader.
**Outcome:** All three consumers now dispatch on `$CMDB_SOURCE` with
byte-identical equivalence proven between YAML and NetBox sources for
the consumed payload.

## C5.2 prereq — schema fix (committed `c959760`)

C3 migration was lossy on three dimensions; C5.2a equivalence surfaced
two of them and C5.2 was paused to fix before any consumer migration.
See Discovery #17 in `PHASE_13_BLOCK_4C_C2_DISCOVERIES_2026-04-29.md`
for the full lossy-dimension write-up. Resolution:

- Added two NetBox custom fields:
  - `health_expect_extra` (longtext) — comma-separated list of additional
    expected codes when registry health_expect is multi-valued (e.g.,
    `[200, 302]` → primary `200`, extra `302`).
  - `port_is_internal` (boolean) — re-emit `port=null` when the
    registry expressed an internal-only port (`port: null,
    internal_port: <N>`).
- Backfilled 6 services with `health_expect_extra` and 29 services
  with `port_is_internal`; counts verified post-update.
- Updated `scripts/migrate-registry-to-netbox.py` to compute both
  fields from registry input.

## C5.2a — `scripts/validate-cmdb.sh` (committed `e9fe1f9`)

- Loader: `python3 scripts/cmdb_source.py`, dispatched on `$CMDB_SOURCE`
  or `--source` flag.
- Output: byte-identical (header-stripped) between YAML and NetBox
  sources. SHA256 prefix `2d4a8fd21589de80`.
- Same exit code (1), same 35 health-check passes / 3 fails, same 3
  DRIFT findings.

## C5.2b — `docker/topology-api/server.py` (committed `33bd70a`)

- Refactored to import `cmdb_source` from `/app/cmdb_source.py`
  (Dockerfile copies `scripts/cmdb_source.py` alongside `server.py`).
- Build context bumped to repo root (`../..`); image tag
  `iap/topology-api:1.0.0` → `1.1.0`.
- `build_nodes_edges()` now sorts services by id and depends_on
  by name so output is byte-stable regardless of source order.
- Field normalization: `port` (None → ""), `purpose` (rstrip),
  `container`/`image`/`host` (None → "").

**Equivalence evidence** (same image, `CMDB_SOURCE=yaml` vs
`CMDB_SOURCE=netbox`):

| endpoint | sha256 prefix | bytes |
|---|---|---|
| `GET /api/topology` | `e6ea700556d304ac` | 35264 |
| `GET /api/topology/nodes` | `33720e0962c4faea` | 27299 |
| `GET /api/topology/edges` | `7a55ffc22c79251c` |  7904 |

All three byte-identical between sources.

## C5.2c — `docker/control-plane/app/modules/registry.py` (committed `d05d3bd`)

- Refactored from `yaml.safe_load()` to `cmdb_source.load_services()`.
- Build context bumped to repo root (`../..`); image tag
  `iap/control-plane:1.0.0` → `1.1.0`.
- Added `cmdb_source` setting (default `yaml`) — staged toggle keeps
  YAML as default during transition window.
- Routes sort services by id and depends_on, normalize empty
  fields ("" / []), and sort `/categories` keys+values for stable
  serialization across sources.

**Equivalence evidence** (same image, `CMDB_SOURCE=yaml` vs
`CMDB_SOURCE=netbox`, `X-Forwarded-For: 100.64.0.5`):

| endpoint | sha256 prefix | bytes | notes |
|---|---|---|---|
| `GET /api/registry/services` (services array only) | `f0f5cf7274668c8b` | 11754 | byte-identical (75 entries) |
| `GET /api/registry/categories` | `f4918fd085e67ab8` |  1474 | byte-identical |
| `GET /api/registry/health`     | `d1cfe56472c6385c` |  3506 | byte-identical |

The full `/services` response top-level `metadata` block differs
intentionally: YAML returns the registry metadata (`version`,
`platform`, `primary_host`, `primary_ip`); NetBox returns `{}`.
NetBox has no equivalent registry metadata section. The consumed
services array is byte-identical.

## Documentation updates

- `docs/PLATFORM_OVERVIEW.md` — Key File Locations table now lists
  NetBox as authoritative CMDB; YAML demoted to fallback.
- `docs/runbooks/add-new-service.md` — Step 2 rewritten for NetBox
  custom-field workflow; explicit reference to equivalence harness.
- `docs/architecture/dependency-graph.md` — header updated to point
  at NetBox + `cmdb_source.py` dual-source loader.

## Remaining C5/C6 work

| Item | Status |
|---|---|
| C5 marquee gate (deprecation entry, ADR, tombstone) | pending |
| C6 final regression probe + closeout | pending |
| Default flip `CMDB_SOURCE=yaml` → `netbox` | C6 (post-regression) |

## Stop-and-surface conditions checked

The C5.2b/c/docs run was instructed to fold the gates and only
interrupt on equivalence regression, new lossy dimension, regression
probe failure, or plan deviation. None occurred:

- No new lossy dimension surfaced — server.py-side normalization
  bugs in topology-api (`str(None)` → `"None"`, trailing newline on
  `purpose`) were emission/projection issues, not loader/data
  divergence; fixed in the consumer code.
- All equivalence probes show byte-identical output for the
  consumed payload.
- Default `CMDB_SOURCE=yaml` preserved across both consumers; no
  doctrine deviation.
