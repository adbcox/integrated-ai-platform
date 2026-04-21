# ADR-0001: Canonical Session and Job Schema

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-11-HANDOFF-V7, AS-CW-01, governance/schema_contract_registry.json

---

## Context

The integrated AI platform executes work through discrete units called **sessions** and **jobs**. A session is a bounded execution context with a declared primary objective and acceptance criteria. A job is an atomic work unit dispatched within a session.

Prior to this ADR, session and job structure was defined implicitly through multiple partially-overlapping files:
- `framework/job_schema.py` — Python-level definitions
- `governance/runtime_contract_version.json` — version pinning
- `governance/schema_contract_registry.json` — registry of canonical schemas

These sources agreed on structure but had no single authoritative specification document that governance and execution could both reference. The V7 handoff surface (AS-11-HANDOFF-V7) and the adoption packet (AS-CW-01) both require that machine-readable governance artifacts under `governance/` supersede all narrative documents.

---

## Decision

The **canonical session schema** is defined as:

```
session:
  session_id:         string   # unique, scoped to session type
  primary_session_type: enum   # capability_session | measurement_session |
                               # planning_session | governance_session
  primary_objective:  string   # single focused goal
  accepted_baseline:  object   # metrics/state at session start
  blockers_resolved:  list     # list of {blocker_id, evidence_ref}
  real_paths_rerun:   list     # list of {path_id, result}
  stop_reason:        string   # why session ended
  generated_at:       iso8601
```

The **canonical job schema** is defined as:

```
job:
  job_id:             string
  job_class:          enum     # capability | measurement | planning |
                               # governance | ratification
  lifecycle:          enum     # pending | dispatched | executing |
                               # completed | failed | escalated
  validation_requirement: object  # {required_commands: list, pass_threshold: float}
  escalation_policy:  object   # {trigger: string, route: string}
  parent_session_id:  string
  generated_at:       iso8601
```

Both schemas are registered in `governance/schema_contract_registry.json` under:
- `canonical_session_schema`
- `canonical_job_schema`

The Python implementation in `framework/job_schema.py` is the authoritative runtime expression of these schemas. The registry is the authoritative governance reference. Both must remain synchronized.

---

## Consequences

**Positive**:
- Sessions and jobs have a single canonical spec that governance and execution share
- Phase 0 gate: any session artifact that omits `primary_session_type` or `stop_reason` is non-conformant
- Phase 1 hardening can pin the schema version via `governance/runtime_contract_version.json`

**Negative / constraints**:
- The `framework/job_schema.py` Python definitions must not diverge from this ADR without a superseding ADR
- Adding new `primary_session_type` values requires updating both the schema registry and this ADR
- `session_id` uniqueness is scoped per session type only; cross-type uniqueness is not enforced at schema level

**Phase gate impact**:
- Phase 0 cannot close without a ratified canonical schema reference (this ADR satisfies that requirement as part of the closure package)
- Phase 1 `runtime_contract_version.json` ratification must reference this ADR as the schema anchor
