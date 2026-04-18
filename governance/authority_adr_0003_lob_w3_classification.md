# ADR 0003 — LOB-W3 Classification

Status: accepted (RECON-W1)
Owner: governance/tactical_family_classification.json (family_id = "live_bridge")

## Context

The `live_bridge_*` helper surface (the LOB tactical family) has been expanded
across multiple packages culminating in LOB-INT-3 and related reconciliation
work visible in recent commit history. There has been internal pressure to
open an LOB-W3 package as the next canonical step.

At the time of RECON-W1 none of the following conditions holds:

- a canonical phase authorizes the LOB family as
  `canonically_authorized_family` (see ADR 0002)
- runtime-primitive adoption by `live_bridge_*` files is measured and
  ratified in `governance/runtime_adoption_report.json`
- named offline regression coverage exists for the LOB family

Additionally, the canonical phase that could authorize further LOB expansion
(Phase 6 — controlled expansion) is not canonically authorized at
as_of_commit.

## Decision

1. LOB-W3 is paused as canonical work. No new LOB tactical package may be
   opened as canonical work by this repository until a later reconciliation
   package explicitly lifts the pause.
2. Existing committed LOB / `live_bridge_*` code is retained in-tree and
   classified as `provisional_precursor` in
   `governance/tactical_family_classification.json`.
3. A later reconciliation package may lift this pause only when all of the
   following are true:
   - canonical phase authority permits LOB work (see ADR 0001 and ADR 0002)
   - measurable runtime-primitive adoption exists for the LOB family in
     `governance/runtime_adoption_report.json`
   - named offline regression coverage exists for the LOB family

## Consequences

- `live_bridge_*` code remains importable and no behavior is modified by this
  ADR.
- Attempts to open an LOB-W3 package are blocked at governance review until
  the pause is lifted.
- This ADR does not retire any file. Retirement, if ever decided, must be a
  separate ADR.

## Supersedes

- Any implicit plan to open LOB-W3 immediately after LOB-INT-3.
