# ADR-A-015 — Staged-Toggle Pattern for Source-of-Truth Migrations

**Status:** Accepted
**Date:** 2026-04-30
**Phase:** 15

## Context

When migrating an authoritative data source, the platform cannot do a hard
cutover: running services depend on the old source, and a bug in the new
source could break production. Block 4.C's NetBox migration proved a pattern
that safely handles this class of problem.

## Decision

All source-of-truth migrations use the staged-toggle pattern:

1. **Build a unified loader** that accepts both old and new sources via a
   single env-var flag (`CMDB_SOURCE=yaml|netbox`). The loader is the only
   code that knows which source is active.
2. **Default to old** (`CMDB_SOURCE=yaml` initially). New source is opt-in.
3. **Prove equivalence at migration time** (ADR-A-012): run the loader in
   both modes against the same snapshot; assert byte-identical output.
4. **Flip the default** after a stability window (≥1 week no incidents that
   would have demanded old-source fallback).
5. **Retain the old source** as a fallback for at least one full release cycle
   after the flip. Remove only when ADR-A-012 deprecation-gate re-run passes.

## Consequences

Positive:
- Zero-downtime migration; instant rollback by env-var flip.
- Migration correctness provable before cutover.
- Fallback path is documented and tested.

Negative:
- Loader must maintain two code paths during the transition window.
- Requires discipline not to write to the old source during transition.

## Related

- ADR-A-012 (equivalence harness doctrine)
- ADR-A-014 (NetBox as CMDB — first application of this pattern)
- `docs/runbooks/migrate-source-of-truth.md` (step-by-step procedure)
