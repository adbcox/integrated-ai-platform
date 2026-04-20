# ADR 0025: Phase 7 Closure — V8 Gate Closure and Codex 5.1 Benchmark

**Status**: Ratified
**Package**: CAP-P7-CLOSE-1
**Date**: 2026-04-20
**Authority owner**: governance

## Decision

Phase 7 (`v8_gate_closure_and_codex51_benchmark`) is declared **closed_ratified**.
All 9 v8 gates are READY at commit `f5013c3`.

## Evidence

9/9 v8 gates confirmed READY via `governance/phase7_closure_evidence.json`
(collected 2026-04-20T21:49:03Z, `ratified_by: collect_phase7_evidence.py`):

1. **stage8_ready** — stage7_manager executed with stage8 lane (`stage_version=stage8-v1`); checkpoint+resume cycle completed; `rollback_contract_coverage=1.0`; `resumed_runs=1`, `checkpointed_runs=1`.

2. **manager8_ready** — `manager_strategy_decision_rows=1`; manager5 lifecycle: `plans=3`, `with_state=3`, `with_attempts=3`.

3. **rag8_ready** — rag6: `plans=13`, `clusters=39`, `clusters_with_risk=39`, `clusters_with_yield=39`.

4. **worker8_ready** — `worker_budget_decisions=3` from stage8 subplan execution.

5. **promotion8_ready** — `candidate_success=4` via 4 successful manager4 candidate-lane runs (distinct targets, `lane=candidate`, `manifest_version=7`, within 7-day trace window).

6. **qualification8_ready** — regression framework evidence met; `version8_upgrade_list` present in manifest.

7. **gate_chain_ready** — `full_qualification_rate=0.5` (meets threshold 0.5); `g4_repo_quick` coverage=1; `fully_qualified=1` (`discovery_mode=naming_convention`).

8. **benchmark8_ready** — `class_count=1` (`framework_code`), `all_classes_passed=True`.

9. **attribution8_ready** — `orchestration_delta=1.0`, `model_delta=1.0`, `has_attribution=True`.

Capability session commits: `3324d8d` through `f5013c3`.

## Authority

This ADR ratifies:
- `governance/phase7_closure_evidence.json` (package_id: CAP-P7-CLOSE-1)
- `governance/phase7_closure_decision.json` (decision: closed)

No tactical family is unlocked by this closure. All tactical families remain locked at baseline_commit `53ae4d4f177b176a7bffaa63988f63fa0efa622c`.

## Next authorized work

Final closeout ratification is the next required governance step. No new capability sessions are authorized. Package class advances to `ratification_only` pending final project closeout ratification.
