# Phase 7 Terminal Closeout Specification

**Spec ID**: PHASE7-TERMINAL-CLOSEOUT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 7 (full_autonomy_and_promotion)  
**Authority sources**: governance/phase7_promotion_baseline.v1.yaml, governance/phase6_local_first_transition_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 7 terminal closeout surfaces — the live-evidence proof surfaces that convert the synthetic promotion proof from P7-01 into structured live evidence. Terminal closeout is the final step before full local autonomy is declared.

The machine-readable form is `governance/phase7_terminal_closeout.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_7`
- **Label**: Phase 7 — Terminal Closeout
- **Status**: `terminal_closeout_in_progress`

---

## Required Modules

| Module | Classes |
|--------|---------|
| `framework/live_aider_proof_v1.py` | `LiveAiderProofV1`, `AiderProofResultV1` |
| `framework/real_telemetry_ingestion_v1.py` | `RealTelemetryIngestionV1`, `TelemetryIngestionResultV1` |
| `framework/live_escalation_evidence_v1.py` | `LiveEscalationEvidenceV1`, `EscalationEvidenceSummaryV1` |
| `framework/promotion_gate_ratifier_v1.py` | `PromotionGateRatifierV1`, `PromotionGateResultV1` |
| `framework/phase7_terminal_closeout_v1.py` | `Phase7TerminalCloseoutV1`, `Phase7TerminalCloseoutResultV1` |

---

## Required Live Evidence

| Evidence | Surface | Description |
|---------|---------|-------------|
| `live_or_truthful_dispatch_proof` | `LiveAiderProofV1` | Live dispatch result or explicit dry-run-only fallback with failure_reason |
| `real_telemetry_ingestion` | `RealTelemetryIngestionV1` | Ingestion of persistent ledger + real artifact paths |
| `explicit_escalation_accounting` | `LiveEscalationEvidenceV1` | Escalation evidence from actual workflow records; local_autonomy_progress_preserved |
| `promotion_gate_decision` | `PromotionGateRatifierV1` | Gate cleared or all blockers listed explicitly |

---

## Live Aider Proof

`LiveAiderProofV1.prove()` returns `AiderProofResultV1`:
- `live_dispatch_attempted` — whether live dispatch was attempted
- `live_dispatch_succeeded` — whether it completed successfully
- `dispatch_mode` — `live` | `dry_run_only` | `blocked`
- `failure_reason` — explicit reason when not live (no false claims)

When `attempt_live=False` or Aider not installed: `dispatch_mode = "dry_run_only"`, truthful disclosure.

---

## Real Telemetry Ingestion

`RealTelemetryIngestionV1.ingest()` returns `TelemetryIngestionResultV1`:
- `ledger_entries_seen` — count of entries in persistent ledger
- `real_artifacts_seen` — count of known artifact files found on disk
- `synthetic_only` — True if all ledger entries use synthetic run IDs
- `telemetry_complete` — True only when `ledger_entries_seen > 0 AND real_artifacts_seen > 0`
- `evidence_gaps` — explicit list of gaps

---

## Live Escalation Evidence

`LiveEscalationEvidenceV1.derive()` returns `EscalationEvidenceSummaryV1`:
- `escalation_events_seen` — total events in workflow
- `escalation_required_events` — events where escalation_requested = True
- `remote_assist_events` — events using Claude/remote executor
- `local_autonomy_progress_preserved` — True when no remote executor event violates invariant
- `evidence_gaps` — explicit invariant violations or gaps

---

## Promotion Gate Ratifier

`PromotionGateRatifierV1.ratify()` checks all four live evidence dimensions:
1. Aider proof: live dispatch succeeded, OR dry-run-only noted as blocker
2. Telemetry: `telemetry_complete = True`
3. Escalation: `local_autonomy_progress_preserved = True`
4. Promotion: `promotion_result.promotion_ready = True`

Returns `PromotionGateResultV1` with `promotion_gate_cleared` and all `blockers_remaining`.

---

## Terminal Closeout Assembly

`Phase7TerminalCloseoutV1.assemble()` bundles all four surfaces:
- `phase6_closeout` — Phase 6 closed?
- `promotion_result` — Phase 7 promotion ready?
- `gate_result` — Promotion gate cleared?
- `telemetry` — Telemetry complete?

`terminal_closeout_ready = phase6_closed AND promotion_ready AND promotion_gate_cleared`

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `phase6_closed_true` | phase6_closed = true in terminal closeout |
| `promotion_ready_decided` | promotion_ready present as boolean |
| `blockers_remaining_explicit` | blockers_remaining present as list |
| `terminal_gate_decided` | terminal_closeout_ready present as boolean |

---

## Remaining Blockers

### P7-LIVE-BLOCKER-01 (deferred to first real Aider execution session)
LiveAiderProofV1 falls back to dry_run_only when Aider is not installed. Full live dispatch proof requires Aider and a real task.

### P7-LIVE-BLOCKER-02 (deferred to first real Aider execution session)
RealTelemetryIngestionV1 currently consumes substrate package artifacts only. Real Aider/Ollama execution artifacts will extend real_artifacts_seen in live sessions.

---

## Terminal Gate

Phase 7 terminal closeout is complete when **all** of the following are true:

1. `phase6_closed = true`
2. `promotion_ready = true` (or all blockers listed)
3. `promotion_gate_cleared = true` (or all gate blockers listed)
4. `terminal_closeout_ready = true` OR `blockers_remaining` fully explicit
5. `all_checks_passed = true` in terminal artifact
6. `make check` passes
7. Phase 7 live-evidence seam tests pass

**Gate status**: `pending` — P7-LIVE-BLOCKER-01 (dry_run_only dispatch) explicitly disclosed.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Phase 7 promotion | governance/phase7_promotion_baseline.v1.yaml |
| Phase 6 closeout | governance/phase6_local_first_transition_baseline.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Live run validation | governance/local_run_validation_pack.v1.yaml |
