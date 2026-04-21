# ADR-0003: Workspace Contract

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-V7-01 (canonical_roadmap), AS-CW-02 (phase closure requires explicit record), governance/current_phase.json

---

## Context

The platform's execution model requires that each session operate within a **workspace** — a bounded file-system and state scope that isolates session writes from the broader repository. Without a workspace contract, sessions can:
- Write artifacts to arbitrary paths
- Leave partial state on failure
- Conflict with concurrent sessions
- Bypass governance artifact gates

The V4 handoff (AS-V4-01) and V7 handoff (AS-V7-01) both reference the canonical roadmap as the authoritative phase structure. The adoption packet (AS-CW-02) requires that phase closure records exist before a phase is considered complete. A workspace contract is needed to specify where phase artifacts land and what constitutes a valid workspace state.

---

## Decision

A **workspace** is defined as:

```
workspace:
  workspace_id:       string    # scoped to session_id
  session_id:         string    # parent session
  phase_id:           int       # canonical phase this workspace operates under
  root_path:          string    # absolute path to workspace root
  artifact_paths:     object    # {artifact_type: relative_path, ...}
  allowed_write_paths: list     # paths this session may write to
  forbidden_write_paths: list   # paths this session must not write to
  cleanup_policy:     enum      # retain | retain_on_failure | delete_on_success
  state:              enum      # initializing | active | committing | closed | failed
```

**Workspace lifecycle**:
1. `initializing` — paths declared, not yet active
2. `active` — session is executing; writes permitted to `allowed_write_paths` only
3. `committing` — session is writing final artifacts; governance artifact gates enforced
4. `closed` — workspace is sealed; no further writes
5. `failed` — workspace is sealed due to error; artifacts retained per `cleanup_policy`

**Canonical artifact path conventions**:
- Governance artifacts: `artifacts/governance/`
- Benchmark artifacts: `artifacts/` subdirectories by stage
- Phase closure records: `governance/phase{N}_closure_decision.json`
- ADR documents: `docs/adr/`

**Forbidden write paths** (always forbidden regardless of session type):
- `governance/canonical_roadmap.json` — immutable without explicit closure ADR
- `governance/authority_adr_*` — append-only, no modification of existing
- `config/promotion_manifest.json` — frozen pending migration per AS-CW-01

---

## Consequences

**Positive**:
- Sessions cannot accidentally overwrite governance artifacts outside their allowed scope
- Phase gate checks can verify workspace state before accepting closure artifacts
- `artifacts/governance/` is the canonical landing zone for all governance session outputs

**Negative / constraints**:
- Workspace initialization adds overhead to session startup
- Sessions that need write access to multiple scopes must explicitly declare all paths
- The `cleanup_policy` must be set to `retain_on_failure` for governance sessions to preserve audit trails

**Phase gate impact**:
- Phase 0 closure record (`governance/phase0_closure_decision.json`) must be produced in a `committing` workspace state
- Phase 1 cannot ratify the runtime contract without verifying that the workspace contract is enforced in `framework/`
