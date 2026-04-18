# ADR 0006 — Tactical Unlock Criteria

Status: accepted (RECON-W2)
Owner: governance/tactical_unlock_criteria.json
Baseline commit: 53ae4d4f177b176a7bffaa63988f63fa0efa622c

## Context

ADR 0002 (RECON-W1) established three classifications for tactical families:

- `canonically_authorized_family`
- `provisional_precursor`
- `paused_pending_reconciliation`

ADR 0002 did not enumerate a machine-readable gate for promotion or
demotion. That gap is what this ADR closes.

## Decision

1. Every tactical family listed in
   `governance/tactical_unlock_criteria.json` has an explicit
   `unlock_preconditions[]` list. A family may not transition out of
   `locked` until every precondition is satisfied and a review packet is
   authorized.
2. Unlock states form the following transition lattice:

   ```
   locked  ->  eligible_for_review  ->  unlocked
   ```

   Downward transitions (`unlocked -> eligible_for_review -> locked`) are
   always permitted and require only a recorded ADR.
3. For RECON-W2 specifically, every family remains `locked`. No precondition
   has been satisfied at baseline commit.
4. ADR 0003 remains in force. `live_bridge` (LOB) is locked and its unlock
   requires the ADR 0003 pause to be explicitly lifted in addition to all
   other preconditions.
5. Unlock evaluation is performed deterministically by
   `bin/governance_unlock_evaluator.py`. The script writes only to
   `governance/` and must not modify code under any tactical family's prefix.

## Consequences

- New tactical packages for a locked family are blocked at governance review.
- A future reconciliation package that satisfies the preconditions for a
  family may raise the unlock state; the state change must be ratified in a
  subsequent ADR.
- The legacy promotion manifest (`config/promotion_manifest.json`) remains
  separate and is not a valid unlock path.

## Supersedes

- Any implicit assumption that a family could be promoted to
  `canonically_authorized_family` without satisfying the explicit
  preconditions recorded here.
