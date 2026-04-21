# ADR-0006: Artifact Bundle

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-V7-04, AS-CW-01 (governance/ as source of truth), governance/phase_gate_status.json

---

## Context

Every session produces **artifacts** — structured outputs that persist session results, enable auditing, and provide inputs to downstream sessions. Without a bundle contract:
- Artifact schemas vary per session type, making cross-session queries unreliable
- There is no canonical way to declare what a session produced vs. what it consumed
- Phase gate checks cannot reliably verify that a session produced the required artifacts before closure

The V7 handoff (AS-V7-04) requires that artifact bundles include both produced and consumed manifests. The adoption packet (AS-CW-01) requires that all governance artifacts land under `governance/` or `artifacts/governance/`.

---

## Decision

An **artifact bundle** is the complete set of artifacts produced and consumed by a session:

```
artifact_bundle:
  bundle_id:          string    # session_id + "_bundle"
  session_id:         string
  session_type:       string    # mirrors session.primary_session_type
  phase_id:           int
  produced:           list      # list of artifact_record
  consumed:           list      # list of artifact_reference
  generated_at:       iso8601
  bundle_valid:       bool      # all required artifacts present and parseable

artifact_record:
  artifact_id:        string
  artifact_type:      enum      # governance | benchmark | evidence | index | plan | report
  path:               string    # relative to repo root
  schema_ref:         string    # schema registry key or "unregistered"
  generated_at:       iso8601
  content_hash:       string    # SHA-256 of file content at bundle close time

artifact_reference:
  artifact_id:        string
  path:               string
  consumed_at:        iso8601
  readable:           bool
```

**Required produced artifacts by session type**:
```
governance_session:   at least one artifact_type=governance in artifacts/governance/
measurement_session:  at least one artifact_type=benchmark or evidence
planning_session:     at least one artifact_type=plan
capability_session:   at least one artifact_type=evidence + validation evidence
```

**Artifact path conventions** (canonical):
- `artifacts/governance/` — all governance outputs
- `artifacts/baseline_validation/` — measurement and benchmark outputs
- `artifacts/expansion/` — capability session outputs
- `governance/` — closure decisions, ADRs, authority files (write-bounded)

---

## Consequences

**Positive**:
- Phase gate checks can verify `bundle_valid=true` before accepting a closure record
- Content hashing enables detection of post-session artifact tampering
- The `consumed` manifest creates an auditable dependency chain between sessions

**Negative / constraints**:
- Sessions must close their artifact bundle before the workspace transitions to `committing` state
- `content_hash` computation adds ~10ms per artifact at bundle close
- `schema_ref = "unregistered"` is permitted but triggers a governance warning

**Phase gate impact**:
- Phase 0 closure record must reference a `bundle_valid=true` bundle from the closure session
- Phase 1 `runtime_contract_version.json` ratification must verify that `framework/state_store.py` produces conformant artifact bundles
