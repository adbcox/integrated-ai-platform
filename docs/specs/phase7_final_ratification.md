# Phase 7 Final Ratification Specification

**Spec ID**: PHASE7-FINAL-RATIFICATION-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 7 (full_autonomy_and_promotion)  
**Authority sources**: governance/phase7_terminal_closeout.v1.yaml, governance/phase7_promotion_baseline.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the final Phase 7 promotion gate ratification logic. `FinalPromotionRatifierV1` consumes the complete Phase 7 evidence chain and emits a single binary promotion decision. The decision is always truthful: if live dispatch evidence is absent or dry-run-only, the gate is blocked and all remaining blockers are listed explicitly.

The machine-readable form is `governance/phase7_final_ratification.v1.yaml`.

---

## Evidence Inputs

| Input | Path | Required |
|-------|------|---------|
| Promotion pack | `artifacts/substrate/phase7_promotion_pack_check.json` | Yes |
| Live evidence pack | `artifacts/substrate/phase7_live_evidence_pack_check.json` | Yes |
| Live proof chain | `artifacts/local_runs/local_live_proof_chain.json` | No — optional; clears live dispatch blocker if present with `live_dispatch_succeeded = true` |

---

## Ratification Logic

`FinalPromotionRatifierV1.ratify()` checks six requirements in order:

1. **promotion_pack_all_checks_passed** — `phase7_promotion_pack_check.json all_checks_passed = true`
2. **promotion_ready_true** — `promotion_ready = true` in promotion pack
3. **live_evidence_all_checks_passed** — `phase7_live_evidence_pack_check.json all_checks_passed = true`
4. **live_evidence_telemetry_complete** — `telemetry_complete = true` in live evidence
5. **live_dispatch_succeeded** — `live_dispatch_succeeded = true` in live evidence OR in live proof chain; `dry_run_only` blocks
6. **local_autonomy_progress_preserved** — no invariant violations in escalation accounting

Returns `FinalRatificationResultV1`:
- `phase7_final_ratified` — True only when all requirements met (no blockers)
- `promotion_gate_cleared` — same as `phase7_final_ratified`
- `remaining_blockers` — explicit list of all unresolved blocking conditions
- `live_evidence_seen` — True if live evidence pack loaded successfully
- `final_summary` — evidence ingestion detail and per-requirement status

---

## Current State (P7-03)

As of P7-03, five of six requirements are met:

| Requirement | Status |
|-------------|--------|
| promotion_pack_all_checks_passed | PASS |
| promotion_ready_true | PASS |
| live_evidence_all_checks_passed | PASS |
| live_evidence_telemetry_complete | PASS |
| live_dispatch_succeeded | **BLOCKED** — dry_run_only (Aider not installed) |
| local_autonomy_progress_preserved | PASS |

**Remaining blocker**: P7-FINAL-BLOCKER-01 — `live_dispatch_succeeded = false`.

---

## How to Clear the Final Blocker

1. Install Aider in the execution environment
2. Run a bounded live task (e.g., `make aider-fast AIDER_MICRO_MESSAGE="..."`)
3. The live execution session produces `artifacts/local_runs/local_live_proof_chain.json` with `live_dispatch_succeeded = true`
4. Re-run `bin/run_phase7_final_ratification_check.py`
5. `FinalPromotionRatifierV1` detects `live_proof_chain.json`, removes the live dispatch blocker, and returns `phase7_final_ratified = true`

---

## Terminal Decision

Phase 7 is fully ratified when all six requirements are met and `FinalPromotionRatifierV1` returns `phase7_final_ratified = true`.

**Current decision status**: `pending` — P7-FINAL-BLOCKER-01 open.

One live Aider execution session is the only remaining step.
