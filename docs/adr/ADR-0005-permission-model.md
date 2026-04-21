# ADR-0005: Permission Model

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-V7-03, AS-CW-03 (next_package_class gating), governance/next_package_class.json, governance/tactical_family_classification.json

---

## Context

The platform requires a permission model that governs what actions sessions, tools, and inference calls may perform. Without a unified permission model:
- Sessions can invoke any tool regardless of their declared `primary_session_type`
- Package class gating (AS-CW-03) has no enforcement mechanism below the script level
- `write_unbounded` and `privileged` operations lack a consistent gate

The V7 handoff (AS-V7-03) identifies the permission model as a critical Phase 1 component. The `next_package_class.json` is the binding gate for package admission (AS-CW-03), but the mechanism by which that gate propagates into session-level tool permissions has not been specified.

---

## Decision

The **permission model** is a four-layer hierarchy:

### Layer 1: Package Class Gate
`governance/next_package_class.json::current_allowed_class` is checked at session initialization. Sessions of a non-allowed class are rejected before any tool dispatch.

Current allowed class: `ratification_only`

Package class → allowed session types:
```
ratification_only:   governance_session, measurement_session
capability_session:  capability_session, measurement_session, planning_session
tactical_review:     all session types
```

### Layer 2: Session Type Permissions
Each `primary_session_type` has a declared maximum tool permission level:

```
governance_session:    write_bounded (governance paths only)
measurement_session:   read_only
planning_session:      read_only + write_bounded (artifacts/ only)
capability_session:    write_bounded (with explicit file grants)
```

### Layer 3: Tool Permission Level
Defined per tool in ADR-0002. Enforced by `framework/permission_engine.py`.

### Layer 4: Tactical Family Lock
`governance/tactical_family_classification.json` classifies families as EO/ED/MC/LOB/ORT/PGS. All tactical families remain locked at baseline_commit per `governance/tactical_unlock_criteria.json` until an explicit per-family unlock review packet is ratified.

**Enforcement chain**:
1. Package class gate (Layer 1) → reject non-conformant sessions at admission
2. Session type check (Layer 2) → restrict available tool permission levels
3. Tool permission check (Layer 3) → reject individual tool calls above session ceiling
4. Family lock check (Layer 4) → reject writes to locked tactical family paths

---

## Consequences

**Positive**:
- `ratification_only` package class cannot spawn `capability_session` — gate is enforced at Layer 1
- `governance_session` cannot trigger `write_unbounded` or `privileged` tools — gate at Layer 2
- Tactical family locks are not bypassable by any session type below `tactical_review` package class

**Negative / constraints**:
- `framework/permission_engine.py` must implement all four layers; current implementation covers Layer 3 only
- Adding a new `primary_session_type` requires updating this ADR and the permission matrix
- Cross-layer conflicts (e.g., governance_session needing privileged access) require control window escalation

**Phase gate impact**:
- Phase 1 ratification requires that `framework/permission_engine.py` is verified against Layers 1–3
- Phase 2 capability sessions require Layer 4 (tactical family lock) verification before any capability writes
