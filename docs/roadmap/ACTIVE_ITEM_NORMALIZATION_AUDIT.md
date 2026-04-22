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

- `RM-GOV-006` — fully normalized
- `RM-GOV-007` — fully normalized
- `RM-GOV-008` — fully normalized

### Active strategic cluster

- `RM-AUTO-001` — fully normalized
- `RM-GOV-001` — fully normalized
- `RM-OPS-004` — fully normalized
- `RM-OPS-005` — fully normalized
- `RM-INV-002` — fully normalized

### Broad active backlog

Many active items are currently represented correctly at the summary/index level but still need item-level normalization if they are likely to enter execution soon.

## Recommended next-wave normalization order

1. `RM-INV-001`
2. `RM-INV-003`
3. `RM-CORE-001`
4. `RM-CORE-002`
5. `RM-UI-001`
6. `RM-UI-002`
7. `RM-HOME-001`
8. `RM-MEDIA-001`
9. `RM-MEDIA-002`
10. `RM-HW-001`

## Rule

Not every backlog item needs full execution-shaped normalization immediately.
Prioritize the items that are:

- in the active strategic cluster
- likely to enter execution soon
- architecturally central
- dependent on external systems or grouped execution logic
