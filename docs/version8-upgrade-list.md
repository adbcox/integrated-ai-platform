# Version 8 Upgrade List

Canonical machine-readable source: `config/promotion_manifest.json` under `version8_upgrade_list`.

## Current Version 8 status

| Subsystem | Current version | V8 status | Remaining blocker |
| --- | --- | --- | --- |
| Stage system | `stage8-v1` | `complete` | none |
| Manager system | `manager8-v1` | `complete` | none |
| RAG system | `rag8-v1` | `complete` | none |
| Worker Utilization | `worker-routing-v2` | `partial` | adaptive budget tuning from historical outcomes |
| Promotion Engine | `level10-promote-v2` | `partial` | subsystem gates are enforced but not yet deeply weighted in lane-scoring |
| Regression / Qualification | `qualify-v2` | `partial` | deterministic Stage-8 assertions not yet wired into `bin/micro_lane_stage7.sh` |

## What is now landed in code

### Stage 8
- Persisted checkpoints in `artifacts/manager6/plans/<plan_id>/checkpoints.json`
- Resumable execution (`--resume`) that skips completed subplans
- Explicit subplan `rollback_contract` metadata in status/traces/history

### Manager 8
- History-weighted strategy decisioning (`run_grouped` vs `split_first`)
- Explicit strategy transition recording in plan history (`decision_state`)
- Class-budgeted worker gating with auditable `deferred_worker_budget` behavior

### RAG 8
- Conflict-risk scoring (`risk_score`, `conflict_signals`)
- Execution-yield scoring (`yield_score`)
- Cluster ordering by safety/yield before manager execution

### Worker Utilization v8 (partial)
- New class-budget ledger (`promotion/worker_budget.py`)
- Budget decisions consumed by Stage-8 orchestration before dispatch
- Traceable worker-budget decision payloads

### Promotion Engine v8 (partial)
- Subsystem gate matrix in `bin/level10_promote.py`
- Apply-time promotion blocking when required subsystem gates are missing
- Auditable gate matrix persisted in decision history payloads

### Regression / Qualification v8 (partial)
- `bin/level10_qualify.py` now emits deterministic v8 gate assertions
- Machine-readable qualification history at `artifacts/promotion/qualification_history.jsonl`
- Stage8/Manager8/RAG8 metrics included in qualification JSON

## Build order from here

1. Worker Utilization v8 completion (`worker-routing-v3`).
2. Promotion Engine v8 completion (`level10-promote-v3`).
3. Regression / Qualification v8 completion (`qualify-v3`).

Detailed next-tier plan: `docs/version9-upgrade-plan.md`.
