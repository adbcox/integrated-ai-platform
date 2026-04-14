# Version 8 Upgrade List

This file is the operator-facing view of the Version 8 build list. The canonical machine-readable source is `config/promotion_manifest.json` under `version8_upgrade_list`.

## Scope

- Stage 8
- Manager 8
- RAG 8
- Promotion Engine v8
- Worker Utilization v8
- Regression / Qualification Framework v8

## Build Order

1. Stage 8 (`build_next`)
2. Manager 8 (`build_next`)
3. RAG 8 (`build_next`)
4. Worker Utilization v8 (`staged_later`)
5. Promotion Engine v8 (`staged_later`)
6. Regression / Qualification v8 (`blocked_until_stage8_manager8_rag8_move`)

## Stage 8

- Current: `stage8-v1`
- Target: `stage9-v1`
- Goal: harden resumed multi-phase execution into deterministic production gates and interruption handling contracts.
- Landed in `stage8-v1`:
  - persisted `checkpoints.json` for Stage-7/8 plans
  - `--resume` mode that skips completed subplans from checkpoints
  - explicit `rollback_contract` payload per executed subplan
- Validation completed:
  - paused run resumed from checkpoints without rerunning completed subplans
  - checkpoint/history include rollback-contract semantics
- Operator-visible change now: interrupted Stage-8 plans can be resumed safely.
- Dependencies: Manager 8, Regression/Qualification v8.

## Manager 8

- Current: `manager6-v1`
- Target: `manager8-v1`
- Goal: strategy-scored retry/split/drop orchestration driven by plan-family outcomes.
- Gap:
  - split-on-failure exists but strategy selection is not history-weighted.
  - plan lifecycle exists without explicit scored strategy state-machine.
- Required code:
  - strategy scorer using recent plan-history outcomes
  - persisted lifecycle transitions: `evaluate -> choose_strategy -> execute -> reconcile`
  - bounded rescue budget per plan family
- Validation:
  - one Stage-7 run with different strategies chosen per subplan
  - trace tags show why alternatives were rejected
- Operator-visible change: manager choices become score-explained instead of fixed fallback order.
- Dependencies: RAG 8.

## RAG 8

- Current: `rag6-v1`
- Target: `rag8-v1`
- Goal: conflict-aware, execution-yield-ordered subplan clustering.
- Gap:
  - clustering is linkage/family-based but not conflict-risk-scored.
  - ordering is rank-forward, not execution-yield aware.
- Required code:
  - conflict-risk features (anchor overlap, proximity, shell-shape collision)
  - per-cluster yield score and ordering
  - emitted rationale: `risk_score`, `yield_score`, `conflict_signals`
- Validation:
  - RAG output includes risk/yield metadata
  - Stage-7 run shows fewer manager-side dropped targets
- Operator-visible change: Stage-7 receives cleaner, risk-ordered subplans before manager repair.
- Dependencies: Manager 8.

## Promotion Engine v8

- Current: `level10-promote-v1`
- Target: `promotion-engine-v8`
- Goal: subsystem-gated promotion decisions with Stage-7 readiness gates.
- Gap:
  - promotion logic is still lane-centric
  - subsystem evidence is present but not hard-gated
- Required code:
  - subsystem gate matrix in `level10_promote`
  - apply-time blocking when required subsystem evidence is missing
  - auditable pass/fail per subsystem in decision history
- Validation:
  - dry-run emits subsystem gate matrix
  - apply blocks when gate evidence is missing
- Operator-visible change: promotions show explicit subsystem blockers.
- Dependencies: Regression/Qualification v8.

## Worker Utilization v8

- Current: `worker-routing-v1`
- Target: `worker-utilization-v8`
- Goal: class-budgeted worker routing with adaptive escalation signals used by Stage-7 manager.
- Gap:
  - no explicit per-class budget ledger consumed by Stage-7 planning
  - escalation telemetry is not fed back into planning strategy
- Required code:
  - worker class budget ledger
  - adaptive escalation hints (`defer`, `split`, `manual`)
  - per-plan-family worker outcome summary persistence
- Validation:
  - Stage-7 run with budget-driven adaptive reroute
  - trace fields include worker budget decisions
- Operator-visible change: reroutes are explained by budget/safety contracts.
- Dependencies: Manager 8.

## Regression / Qualification v8

- Current: `qualify-v1`
- Target: `qualify-v8`
- Goal: enforce deterministic Stage-7 + subsystem gate assertions for v8 readiness.
- Gap:
  - qualification summarizes state but does not assert required v8 gates
  - Stage-7 evidence is not mandatory in gate checks
- Required code:
  - explicit v8 gate assertions in `level10_qualify`
  - machine-readable gate history file
  - Stage-7 regression assertions for required operational evidence
- Validation:
  - qualification JSON contains gate verdicts + missing evidence
  - regression fails when required gate evidence is absent
- Operator-visible change: clear pass/fail reasons for v8 readiness per subsystem.
- Dependencies: Stage 8, Manager 8, RAG 8.
