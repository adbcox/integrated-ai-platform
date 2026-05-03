# CMDB substrate inventory — 2026-05-03 (WP-02)

Scope: intake/audit only, read-only evidence collection across three substrates.

## Substrate A — NetBox (`netbox.internal` / `http://localhost:8084`)

| Field | Value |
|---|---|
| Path/URL | `netbox.internal` (Caddy), API probe via `http://localhost:8084` |
| Last update evidence | Device max `last_updated`: `2026-05-01T23:40:05.703943Z`; Service max `last_updated`: `2026-05-01T17:33:26.763200Z` |
| Entity counts | Devices: **5**; Services: **77**; IP addresses: **0**; Prefixes: **0**; VLANs: **0** |
| Authoritative-by-doctrine | **Yes** (ADR-A-014 declares NetBox authoritative CMDB) |
| Authoritative-by-usage | **Partial** (some consumers default to NetBox; others still carry YAML fallback/runtime substrate dependence) |
| Consumers (read) | `scripts/cmdb_source.py` (`CMDB_SOURCE=netbox` default), `docker/topology-api/server.py` (via `cmdb_source`), `docker/control-plane/app/modules/registry.py` (via `cmdb_source`), `docker/xindex/app/ingest/netbox.py`, `scripts/netbox-register-xindex*.py`, `scripts/network-discovery.py` |
| Schema version | NetBox platform version endpoint returned HTTP 500 during this audit window; schema version not surfaced by queried list endpoints |

Notes:
- API access required token from existing local Vault-rendered credentials file (`~/.vault-agent-secrets/netbox/credentials.env`); value never displayed. Token fingerprint used for verification only: sha256[:12]=`a7f1da287469`.
- NetBox has 77 services while the other two substrates currently have 76.

## Substrate B — `~/.platform-registry/inventory.json` (D-17-29 runtime substrate)

| Field | Value |
|---|---|
| Path | `/Users/admin/.platform-registry/inventory.json` |
| Last update evidence | File mtime: `2026-05-03T10:36:24-0400` |
| Entity counts | Services: **76**; Hosts/service IDs: **74**; Internal IP entries: **51**; Networks: **14** |
| Authoritative-by-doctrine | **Yes (runtime layer)** per D-17-29 / D#25 for ports, internal IPs, dependencies, Caddy-route/runtime metadata |
| Authoritative-by-usage | **Yes (runtime)** — dashboards, doctrine, and runbooks explicitly require consultation before port/routing actions |
| Consumers (read) | `scripts/dashboards/generate_logical_architecture.py`, `scripts/dashboards/generate_physical_architecture.py`, runbook/doctrine procedures, `by-service/*.json` readers |
| Schema version | `1.0` |

Notes:
- `metadata.last_refresh` is null in current file; staleness is instead surfaced via `~/.platform-registry/last-refresh.json` and file mtime.
- This substrate is runtime-descriptive; it includes orphans/sidecars and transient container state not modeled in NetBox.

## Substrate C — `config/service-registry.yaml.DEPRECATED`

| Field | Value |
|---|---|
| Path | `/Users/admin/repos/integrated-ai-platform/config/service-registry.yaml.DEPRECATED` |
| Last update evidence | File mtime: `2026-04-29T15:21:53-0400` |
| Entity counts | Services: **76**; Hosts/service IDs: **75**; IP endpoints: **0**; Networks: **0** |
| Authoritative-by-doctrine | **No**. ADR-A-014: fallback only (`CMDB_SOURCE=yaml`) and not a write target |
| Authoritative-by-usage | **Residual fallback usage** only (mounted into control-plane/topology-api and still loadable via `cmdb_source`) |
| Consumers (read) | `scripts/cmdb_source.py` fallback path, `scripts/validate-cmdb.sh`, `scripts/cmdb-equivalence.sh`, topology/control-plane YAML mounts |
| Schema version | None declared (`schema_version` key absent) |

Notes:
- `.DEPRECATED` suffix is meaningful state: substrate is pre-flagged for retirement but still consumed as a compatibility fallback.
- Metadata fields like `metadata.last_updated` are absent, reinforcing stale/static status.

## Cross-substrate inventory summary

| Axis | NetBox | inventory.json | service-registry.yaml.DEPRECATED |
|---|---:|---:|---:|
| Services | 77 | 76 | 76 |
| Hosts/devices | 5 devices | 74 service IDs | 75 service IDs |
| IP records | 0 | 51 internal entries | 0 |
| Network records | 0 prefixes / 0 VLANs | 14 docker networks | 0 |
| Last update signal | `last_updated` per record | file mtime + refresh sidecar | file mtime only |

## Doctrine vs usage conclusion (WP-02)

1. NetBox is doctrine-authoritative for CMDB intent, but it currently lacks IPAM population (0 IP/prefix/VLAN), so practical runtime routing/address truth is not in NetBox today.
2. `inventory.json` is de-facto runtime authority and heavily consumed for operational decisions.
3. `service-registry.yaml.DEPRECATED` remains a live fallback substrate; the suffix is accurate but retirement is incomplete while mounts/consumers still exist.
