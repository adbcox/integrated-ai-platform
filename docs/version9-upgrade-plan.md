# Version 9 Upgrade Plan

This plan is grounded in the post-session Version 8 state reflected in:
- `config/promotion_manifest.json`
- `docs/version8-upgrade-list.md`

## Stage system
- Current version: `stage8-v1`
- Version 8 status: `complete`
- Remaining blocker: Stage-8 rollback semantics are contract metadata; rollback execution is still delegated to Stage-6/5 behavior.
- Version 9 target: `stage9-v1` deterministic interruption/recovery contract with explicit stage-level rollback verification hooks.
- Why v9 next: Stage-8 resume works; the next operational risk is deterministic rollback verification for production readiness.
- Dependencies: Manager 9 reconciliation policy, Qualify v3 deterministic stage assertions.
- Recommended order: 4

## Manager system
- Current version: `manager8-v1`
- Version 8 status: `complete`
- Remaining blocker: strategy scoring is history-weighted but still short-horizon and family-local.
- Version 9 target: `manager9-v1` long-horizon adaptive strategy engine with persisted cross-plan family learning and conflict-aware rescue policy.
- Why v9 next: core strategy machine exists; next gain is better cross-run adaptation and reduced rescue churn.
- Dependencies: RAG 9 calibrated conflict/yield features, Worker v3 adaptive budget signals.
- Recommended order: 2

## RAG system
- Current version: `rag8-v1`
- Version 8 status: `complete`
- Remaining blocker: risk/yield scoring is static and not calibrated from execution outcomes.
- Version 9 target: `rag9-v1` execution-feedback-calibrated clustering with dynamic conflict/yield weighting by observed manager outcomes.
- Why v9 next: RAG now emits needed signals; next gain is stability and precision from outcome feedback loops.
- Dependencies: Manager 9 outcome persistence schema.
- Recommended order: 3

## Promotion Engine
- Current version: `level10-promote-v2`
- Version 8 status: `partial`
- Remaining blocker: subsystem gates are enforced, but promotion scoring remains lane-first instead of subsystem-readiness-weighted.
- Version 9 target: `level10-promote-v3` weighted subsystem-readiness promotion policy with lane+subsystem composite decisions.
- Why v9 next: apply-time safety exists; next gain is better decision quality and fewer false HOLD states.
- Dependencies: Qualify v3 deterministic subsystem gate confidence.
- Recommended order: 5

## Worker Utilization
- Current version: `worker-routing-v2`
- Version 8 status: `partial`
- Remaining blocker: class budgets are enforced but not adaptively tuned from historical outcomes.
- Version 9 target: `worker-routing-v3` adaptive class-budget model with plan-family escalation memory and bounded auto-tuning.
- Why v9 next: budget gating works; next gain is throughput without increased failure.
- Dependencies: Manager 9 strategy consumer.
- Recommended order: 1

## Regression / Qualification Framework
- Current version: `qualify-v2`
- Version 8 status: `partial`
- Remaining blocker: deterministic Stage-8 regression assertions are not yet hard-enforced in `bin/micro_lane_stage7.sh`.
- Version 9 target: `qualify-v3` deterministic subsystem gate regression pack + reproducible gate history diffing.
- Why v9 next: gate assertions exist in qualification output; next gain is deterministic enforcement in the operational regression path.
- Dependencies: Stage 9 rollback verification signals, Promotion v3 weighted gates.
- Recommended order: 6

## Recommended Version 9 build order

1. Worker Utilization (`worker-routing-v3`)
2. Manager (`manager9-v1`)
3. RAG (`rag9-v1`)
4. Stage (`stage9-v1`)
5. Promotion Engine (`level10-promote-v3`)
6. Regression / Qualification (`qualify-v3`)
