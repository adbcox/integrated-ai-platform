# Active Item Normalization Audit

## Purpose

This document records the final normalization state of the active backlog after the full-governance cleanup pass.

## Interpretation

### Fully normalized
The item has a current per-item file using the newer roadmap governance schema, including maturity, queueing, risks/issues, and status-transition notes.

### Explicit blocked placeholder
The active ID has been retained as a file, but canonical title/scope could not be recovered from current repo-owned authoritative surfaces. These items are intentionally excluded from autonomous target selection until recovered or retired.

## Final state

### Fully normalized active items

- `RM-AUTO-001`
- `RM-CORE-001`
- `RM-CORE-002`
- `RM-DEV-001`
- `RM-DOCAPP-001`
- `RM-DOCAPP-002`
- `RM-GOV-001`
- `RM-GOV-002`
- `RM-GOV-003`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-GOV-008`
- `RM-HOME-001`
- `RM-HW-001`
- `RM-HW-002`
- `RM-INV-001`
- `RM-INV-002`
- `RM-INV-003`
- `RM-LANG-001`
- `RM-MEDIA-001`
- `RM-MEDIA-002`
- `RM-MEDIA-003`
- `RM-MEDIA-004`
- `RM-OPS-001`
- `RM-OPS-002`
- `RM-OPS-003`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-SHOP-001`
- `RM-SHOP-002`
- `RM-SHOP-003`
- `RM-SHOP-004`
- `RM-UI-001`
- `RM-UI-002`
- `RM-UI-003`
- `RM-UI-004`
- `RM-AUTO-MECH-001`

### Explicit blocked placeholders

- `RM-HOME-002`
- `RM-HOME-003`
- `RM-HOME-004`
- `RM-MEDIA-005`
- `RM-SHOP-005`

## Rule

The autonomous system may select only from the fully normalized active items unless and until a blocked placeholder is canonically recovered and reactivated.
