# Version 15 Execution Ladder

This document is the coordinated implementation ladder from current subsystem versions to Version 15, with explicit dependency order and Codex 5.1 replacement prerequisites.

## Source Of Truth

- `config/promotion_manifest.json` is authoritative for current/next/after-next version tracking.
- This ladder defines execution order and dependency gates for implementation.

## Coordinated Ladder

| Subsystem | Current Version | Next Version | After Next | Version 15 Target | Current Status |
| --- | --- | --- | --- | --- | --- |
| Stage system | `stage9-v1` | `stage10-v1` | `stage11-v1` | `stage15-v1` | building |
| Manager/orchestration | `manager13-v1` | `manager14-v1` | `manager15-v1` | `manager15-v1` | building |
| Retrieval / RAG | `rag10-v1` | `rag11-v1` | `rag12-v1` | `rag15-v1` | building |
| Promotion engine / control loop | `level10-promote-v2` | `level10-promote-v3` | `level10-promote-v4` | `level10-promote-v15` | validated |
| Worker utilization / local execution | `worker-routing-v2` | `worker-routing-v3` | `worker-routing-v4` | `worker-routing-v15` | building |
| Regression / qualification | `qualify-v2` | `qualify-v3` | `qualify-v4` | `qualify-v15` | validated |
| Learning / training / attribution | `learning-v10` | `learning-v11` | `learning-v12` | `learning-v15` | building |

## What Each Version Step Unlocks

### Stage system
- `stage10-v1`: deterministic interruption/replay contracts across mixed subplan outcomes.
- `stage11-v1`: conflict-isolated resumed execution with explicit continuation guarantees.
- `stage13-v1`: broader heterogeneous execution contracts with safer partial completion.
- `stage15-v1`: high-confidence autonomous stage planner with verified replay/rollback correctness.

### Manager/orchestration
- `manager13-v1`: proactive pre-dispatch split/drop/defer/order shaping from cross-run strategy/family recurrence trends.
- `manager14-v1`: autonomous multi-run adaptation with replay-priority selection across bounded complex classes.
- `manager15-v1`: robust autonomous orchestration with explainable policy trace lineage and bounded high-complexity recovery.

### Retrieval / RAG
- `rag10-v1`: deeper conflict/yield priors from broader execution cohorts.
- `rag11-v1`: stronger intent/domain fusion and adaptive confidence shaping.
- `rag13-v1`: predictive packaging for lower-context, higher-yield execution.
- `rag15-v1`: high-precision planning substrate for autonomous bounded complex coding.

### Promotion engine / control loop
- `level10-promote-v3`: subsystem-weighted promotion decisions become primary, not lane-only.
- `level10-promote-v5`: staged rollout profiles with rollback-aware promote/demote contracts.
- `level10-promote-v7`: predictive readiness with deterministic adoption controls.
- `level10-promote-v15`: governance-quality deterministic control loop for production evolution.

### Worker utilization / local execution
- `worker-routing-v3`: adaptive class/family budgets from historical outcomes.
- `worker-routing-v4`: complexity-tier routing with bounded confidence-aware escalations.
- `worker-routing-v7`: stable local-first defaults for targeted bounded complex classes.
- `worker-routing-v15`: maximal safe local execution share with stable quality floor.

### Regression / qualification
- `qualify-v3`: deterministic Stage-8/9 assertions in operational packs.
- `qualify-v4`: subsystem gate trend deltas and deterministic failure signatures.
- `qualify-v7`: benchmark suites for bounded complex classes.
- `qualify-v15`: decision-grade subsystem qualification for autonomous operation.

### Learning / training / attribution
- `learning-v10`: operational loop converting real benchmark/campaign/curation artifacts into replay/training queues.
- `learning-v11`: curriculum cohorts tied to failure signatures and class-level first-attempt deficits.
- `learning-v12`: controlled adaptation experiments with gate-linked rollback criteria.
- `learning-v15`: continuous model-improvement loop with auditable model-vs-wrapper gains.

## Dependency Graph (Execution Order)

1. `worker-routing-v3` + `qualify-v3` + `learning-v10`
2. `manager11-v1` + `rag10-v1`
3. `stage10-v1`
4. `level10-promote-v3`
5. `manager11-v1` + `rag11-v1` + `stage11-v1`
6. `qualify-v7` + `worker-routing-v7` + `learning-v11`
7. `promotion v5+` rollout controls
8. `v13` wave across stage/manager/rag/learning
9. `v15` convergence wave

Rationale:
- Local-model capability acceleration depends first on worker/qualification/learning loops being operational and reusable on real artifacts.
- Manager and RAG moves produce direct first-attempt quality shifts.
- Stage and promotion follow once decision quality and signal quality are materially stronger.

## Codex 5.1 Replacement Prerequisite Versions (Minimum Gate)

- Stage: `stage9-v1` validated with deterministic reconciliation evidence
- Manager: `manager13-v1` validated with proactive pre-dispatch recurrence shaping and cross-run strategy evidence
- RAG: `rag10-v1` validated with execution-cohort clustered planning and mixed-family feedback priors
- Worker: `worker-routing-v3` validated (adaptive budgets operational)
- Regression: `qualify-v3` validated (deterministic stage assertions operational)
- Promotion: `level10-promote-v3` validated (subsystem-weighted enforcement)
- Learning: `learning-v10` building/validated (artifact-to-action loop operational)

## Current-Codex Gap-Closing Prerequisite Versions

- Stage/Manager/RAG at least `v11` wave
- Worker at least `v7`
- Qualification at least `v7`
- Promotion at least `v5`
- Learning loop at least `v12`

These are required before claiming meaningful convergence toward current Codex-level capability on bounded complex classes.
