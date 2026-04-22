# Active Item Normalization Audit

## Purpose

This document tracks which active items are already normalized to the newer roadmap governance standard and which items still need item-level normalization work.

## Audit interpretation

### Fully normalized
The item has a current per-item file or equivalent representation that includes the newer planning fields such as maturity, queueing, risk, or status-transition clarity.

### Partially normalized
The item exists canonically, but still uses an older item schema or lacks some of the newer operating-model fields.

### Inventory only
The item is present in summary/inventory surfaces but does not yet have a newer per-item normalization pass.

## Current assessment

### Governance items

- `RM-GOV-006` — partially normalized
- `RM-GOV-007` — partially normalized
- `RM-GOV-008` — partially normalized

### High-value active cluster items needing focused normalization next

- `RM-AUTO-001` — inventory/summary normalization should be reviewed
- `RM-GOV-001` — verify newer schema fields and governance alignment detail
- `RM-OPS-004` — verify readiness, dependencies, and closeout/validation expectations
- `RM-OPS-005` — verify readiness, dependencies, and evidence expectations
- `RM-INV-002` — verify maturity, queueing, risk, and grouped-execution detail

### Broad active backlog

Many active items are currently represented correctly at the summary/index level but still need item-level normalization if they are likely to enter execution soon.

## Recommended next-wave normalization order

1. `RM-GOV-006`
2. `RM-GOV-007`
3. `RM-GOV-008`
4. `RM-AUTO-001`
5. `RM-GOV-001`
6. `RM-OPS-004`
7. `RM-OPS-005`
8. `RM-INV-002`

## Rule

Not every backlog item needs full execution-shaped normalization immediately.
Prioritize the items that are:

- in the active strategic cluster
- likely to enter execution soon
- architecturally central
- dependent on external systems or grouped execution logic
