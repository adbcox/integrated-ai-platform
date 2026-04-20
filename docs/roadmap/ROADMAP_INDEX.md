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
