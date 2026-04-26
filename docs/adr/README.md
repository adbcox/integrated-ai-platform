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
| [ADR-A-007](ADR-A-007.md) | External systems should be adopted where commodity fit is strong | Accepted |
| [ADR-A-008](ADR-A-008.md) | Branches may not fork the platform | Accepted |

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
