# Roadmap

This directory contains the roadmap authority layer for the system.

Operating model:

- repo is canonical for roadmap semantics and architectural planning fields
- machine-readable roadmap files are the primary AI-operable authority surface
- Plane is a secondary operational layer only
- sync is repo-authoritative by default
- execution, validation, grouping, and CMDB linkage are preserved as first-class fields

Canonical machine-readable files begin in:

- `docs/roadmap/data/enums.yaml`
- `docs/roadmap/data/roadmap_registry.yaml`
- `docs/roadmap/data/sync_state.yaml`
- `docs/roadmap/items/RM-GOV-001.yaml`
