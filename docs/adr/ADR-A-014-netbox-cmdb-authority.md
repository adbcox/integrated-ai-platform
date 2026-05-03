# ADR-A-014 — NetBox as Authoritative CMDB

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

Block 4.C migrated the service registry from `config/service-registry.yaml`
to NetBox CMDB. CMDB_SOURCE default was `yaml` during the transition window;
flipped to `netbox` in Phase 14 D-DOC (commit `60aeb96`). Seventeen discoveries
surfaced during the migration. This ADR captures the outcome as a durable
architectural decision.

## Decision

NetBox (`netbox.internal`) is the authoritative source of truth for:
- Service inventory (name, host, port, protocol)
- Physical node inventory (devices, IP addresses, roles)
- Network topology (vlans, prefixes, interfaces)

`config/service-registry.yaml` is retained solely as a deprecation-gate
fallback (ADR-A-012 lifecycle requirement) accessible via `CMDB_SOURCE=yaml`.
It is not a write target; updates must go to NetBox.

## Alternatives considered

- **Homegrown YAML only:** Rejected. YAML requires manual sync; no schema
  validation; no query API. Not suitable beyond ~20 services.
- **InvenTree-only:** Rejected. InvenTree models physical parts; it has no
  concept of running services or network topology.
- **Netshot / LibreNMS:** Rejected. Network-discovery-first tools; not
  designed for service registry use.

## Consequences

Positive:
- Single authoritative store; `scripts/cmdb_source.py` is the canonical
  consumer path.
- NetBox GraphQL + REST APIs enable topology-API and cross-index service
  (Block 4.E) without custom parsers.
- Portability: NetBox runs as a Docker container; same API on any host.

Negative:
- NetBox is a dependency; its failure means topology-API degraded to YAML
  fallback (acceptable; YAML is retained for this case).
- Schema changes in NetBox require migration planning (Discovery #16
  round-trip equivalence doctrine — see ADR-A-015).

## Related

- ADR-A-012 (equivalence harness — the migration proof)
- ADR-A-015 (staged-toggle pattern — the transition mechanism)
- `scripts/cmdb_source.py` (implementation)
- `docs/architecture-facts/dependency-graph.md` (topology view, post-D-17-16)
