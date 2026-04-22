# Status Transition Rules

## Purpose

This document defines how roadmap items should move between statuses so the roadmap does not accumulate inconsistent or ambiguous state.

## Normal status flow

The default lifecycle is:

1. `Proposed`
2. `Accepted`
3. `Decomposing`
4. `Planned`
5. `Execution-ready`
6. `In progress`
7. `Validating`
8. `Completed`
9. `Archived` or equivalent closed state reflected through status-sync surfaces where applicable

## Non-linear statuses

These may occur when appropriate:

- `Deferred`
- `Frozen`
- `Rejected`

## Transition rules

### Proposed -> Accepted
Use when the item has been accepted into the canonical roadmap and has enough normalized definition to remain in backlog inventory.

### Accepted -> Decomposing
Use when the item clearly matters but still needs structural breakdown, grouping review, or sharper scope.

### Decomposing -> Planned
Use when the item has enough shape for queueing, but is not yet execution-ready.

### Planned -> Execution-ready
Use only when the execution-readiness checklist has been satisfied.

### Execution-ready -> In progress
Use when the item or grouped package has actually entered execution, not merely because it is likely to start soon.

### In progress -> Validating
Use when implementation work is materially complete and the main remaining work is validation, verification, or closeout evidence.

### Validating -> Completed
Use only when the required closeout evidence exists and status-sync surfaces are updated.

## Non-linear transition guidance

### Any active state -> Deferred
Use when the item remains worthwhile but is not being pursued in the current horizon.

### Any active state -> Frozen
Use when the item should remain visible but intentionally inactive, often due to strategic pause, unresolved dependency, or wait-for-evidence posture.

### Proposed or Accepted -> Rejected
Use when the item should not remain on the roadmap.

## Rule

Do not use status names as vague mood labels.
Status must describe actual planning or execution state.
