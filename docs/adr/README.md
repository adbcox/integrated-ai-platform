# Architecture Decision Records

Individual ADR files live here. Each file is one decision.

## Index

| ID | Title | Status |
|----|-------|--------|
| [ADR-A-001](ADR-A-001.md) | Retain the existing control plane | Accepted |
| [ADR-A-002](ADR-A-002.md) | Shared runtime substrate is mandatory | Accepted |
| [ADR-A-003](ADR-A-003.md) | Ollama-first is the default coding posture | Accepted |
| [ADR-A-004](ADR-A-004.md) | Aider is an adapter, not a backbone | Accepted |
| [ADR-A-005](ADR-A-005.md) | Claude Code is supervisory or exceptional | Accepted |
| [ADR-A-006](ADR-A-006.md) | Repo docs are canonical for architecture and roadmap planning | Accepted |
| [ADR-A-007](ADR-A-007-media-sync-syncthing.md) | Syncthing replaces rclone SFTP for seedbox→QNAP transfers | Accepted |
| [ADR-A-008](ADR-A-008.md) | Branches may not fork the platform | Accepted |
| [ADR-A-009](ADR-A-009.md) | Vault as authoritative secret store — migration from .env | Accepted |
| [ADR-A-010](ADR-A-010-external-systems.md) | External systems should be adopted where commodity fit is strong | Accepted |
| [ADR-A-011](ADR-A-011-ivv-loop-pattern.md) | IV&V loop pattern (audit → execution → validation → regression) | Accepted |
| [ADR-A-012](ADR-A-012-equivalence-harness-doctrine.md) | Equivalence harness doctrine for source-of-truth migrations | Accepted |
| [ADR-A-013](ADR-A-013-folded-gates-doctrine.md) | Folded gates for mechanical applications of proven patterns | Accepted |
| [ADR-A-014](ADR-A-014-netbox-cmdb-authority.md) | NetBox as Authoritative CMDB | Accepted |
| [ADR-A-015](ADR-A-015-staged-toggle-migration.md) | Staged-Toggle Pattern for Source-of-Truth Migrations | Accepted |
| [ADR-A-016](ADR-A-016-canonical-patterns-registry.md) | Canonical Patterns Registry | Accepted |
| [ADR-A-017](ADR-A-017-vault-warm-copy-backup-strategy.md) | Vault file-backend warm-copy is the backup strategy | Accepted |
| [ADR-A-018](ADR-A-018-replace-plane-with-openproject.md) | Replace Plane CE with OpenProject CE as PM substrate | Accepted |
| [ADR-A-020](ADR-A-020-track2-agent-roles.md) | Track 2 Agent Role Codification | Accepted |

## Format

Each ADR file follows this template:
```
# ADR-X-NNN — Title
Status: Accepted | Superseded | Deprecated
Date: YYYY-MM-DD
Supersedes: (if applicable)
Superseded-by: (if applicable)

## Context
Why this decision was needed.

## Decision
What was decided.

## Consequences
What this means for the platform going forward.
```

## Governance

- New ADRs require PR review from a CODEOWNER
- ADRs are immutable once Accepted (create a new ADR to supersede)
- ADRs that conflict with existing Accepted ADRs must explicitly supersede them
- This directory is protected: only ADRs belong here
