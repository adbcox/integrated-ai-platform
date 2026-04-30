# ADR-A-016 — Canonical Patterns Registry

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

Block 4.C surfaced 17 discoveries. Many of these are not one-off fixes but
reusable patterns that should be applied consistently across the platform.
Today these live only in discovery comments in closeout docs; they decay into
tribal knowledge. This ADR formalises a canonical patterns registry.

## Decision

`docs/canonical-patterns/` is the platform's patterns registry. Each pattern
file documents:
- The problem class it solves
- The canonical implementation (code snippet or config excerpt)
- The discovery or incident that proved the pattern necessary
- The services it applies to today

Current entries:
- `plane-connector-usage.md` — Plane V1 API usage (RateLimitError order,
  `labels` vs `label_ids`, first-batch-verify, `_with_429_retry`)

New patterns are added when:
- A Discovery identifies a cross-cutting concern (applies to >1 service)
- A runbook references the same implementation more than once

## Consequences

Positive:
- Execution windows can reference a canonical pattern rather than
  re-deriving it from discovery notes.
- New blocks onboard faster; fewer repeated discoveries.

Negative:
- Patterns require maintenance; stale patterns are worse than no patterns.
- Review patterns on each major version bump of external dependencies.

## Related

- ADR-A-013 (folded gates doctrine — patterns registry reduces gate overhead)
- `docs/canonical-patterns/` (the registry itself)
