# Roadmap Index

## Canonical machine-readable roadmap authority

The machine-readable roadmap source of truth is seeded in:

- `docs/roadmap/data/enums.yaml`
- `docs/roadmap/data/roadmap_registry.yaml`
- `docs/roadmap/data/sync_state.yaml`
- `docs/roadmap/items/RM-GOV-001.yaml`

Operating rule:

- repo is canonical for roadmap semantics and architectural fields
- Plane is secondary operational state only
- sync is repo-authoritative by default
- roadmap items must remain AI-operable through explicit scope, allowed files, forbidden files, validation order, rollback rule, and artifact outputs

## Initial ingested canonical items

### Phase 0 governance items

- `RM-GOV-002` — Reconcile source-of-truth surfaces
- `RM-GOV-003` — Create core ADR set
- `RM-GOV-004` — Create machine-readable execution-control package
- `RM-GOV-005` — Create CMDB-lite registry
- `RM-GOV-006` — Lock definition of done for coding runs
- `RM-GOV-007` — Lock autonomy scorecard

### Phase 1 core runtime items

- `RM-CORE-001` — Introduce internal inference gateway
- `RM-CORE-002` — Standardize model profiles
- `RM-CORE-003` — Standardize workspace layout
- `RM-CORE-004` — Stabilize artifact persistence
- `RM-CORE-005` — Wrap local execution commands
- `RM-CORE-006` — Establish baseline local-run validation

<<<<<<< HEAD
### Development capability items

- `RM-DEV-003` — Bounded autonomous code generation
- `RM-DEV-005` — Local autonomy uplift, OSS intake, and Aider reliability hardening

### Intelligence capability items

- `RM-INTEL-001` — Open-source watchtower with update alerts and adoption recommendations

### High-priority development items (completed)

- `RM-DEV-005` — Local autonomy uplift, OSS intake, and Aider reliability hardening **(COMPLETED)**
  - Local autonomy uplift validated via Phase 4 and Phase 5 substrate packs
  - Aider constrained to controlled adapter / transport target (ADR 0023)
  - OSS intake formalized with registry, boundaries, and rollback strategy
  - Repo-visible authority artifacts now carry prior chat-only decisions
