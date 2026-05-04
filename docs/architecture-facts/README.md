# Architecture Facts Index

Canonical inventory for `docs/architecture-facts/`.
These files are durable doctrine/finding records, not phase-local
status docs.

## Core Doctrine

| File | Status | Description |
|---|---|---|
| `integration-audit-doctrine.md` | canonical | Cross-phase findings chronicle (Findings 1–16) and audit doctrine. |
| `execution-surface-roles.md` | canonical | Role boundaries across control/execution/autonomous surfaces. |
| `promotion-criteria.md` | canonical | Gate criteria for execution-surface promotion by class/cell. |
| `class-taxonomy.md` | canonical | Durable work-class taxonomy for migration decisions. |
| `migration-telemetry.md` | canonical | Telemetry schema and evidence model for migration outcomes. |

## Platform Architecture Facts

| File | Status | Description |
|---|---|---|
| `host-portability.md` | canonical | Host topology and portability constraints (Mini/Studio/Threadripper). |
| `exo-cluster.md` | canonical | exo distributed-inference architecture and operational boundaries. |
| `mcp-servers.md` | canonical | MCP server architecture and topology. |
| `dependency-graph.md` | canonical | Service dependency graph and regeneration path. |
| `opnsense-dns-authority.md` | canonical | Verified DNS authority posture (Dnsmasq sole, Unbound forbidden). |
| `vault-agent-sidecar-pattern.md` | canonical | Canonical credential sidecar pattern. |
| `model-provenance.md` | canonical | Model provenance verification doctrine. |

## Execution Surface / Goose

| File | Status | Description |
|---|---|---|
| `goose-capability-boundary.md` | canonical | Enabled/disabled capability boundaries and posture history. |
| `goose-session-pipeline.md` | canonical | Per-session Goose pipeline and review flow. |
| `local-tool-calling.md` | canonical | Findings on local tool-calling protocol behavior. |

## PM / Identity / Capability Meta

| File | Status | Description |
|---|---|---|
| `openproject-migration.md` | canonical | Durable findings from Plane->OpenProject migration. |
| `openproject-enrichment-doctrine.md` | canonical | OpenProject enrichment source mapping and write rules. |
| `identifier-conventions.md` | canonical | Canonical ID conventions (`D-NN-MM`, `WP-NN-MM-XX`, etc.). |
| `capability-self-knowledge.md` | canonical | Doctrine for false-negative capability claims. |
| `known-capabilities.md` | canonical | Operator working registry of known capabilities. |

## Notes

- All files in this directory are currently active canonical references.
- Retired/superseded material should live under `docs/_archive/` or
  `docs/_retired/`, not here.
- Phase state remains canonical in `docs/PROJECT_FRAMEWORK.md` §9 and
  `docs/PHASE_ROADMAP.md`.
