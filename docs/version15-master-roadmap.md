# Version 15 Master Roadmap

This is the canonical review roadmap for taking the current Stage-9/Manager-9/RAG-9 stack to **Version 15** across:
1. stage system
2. manager/orchestration
3. retrieval/RAG
4. promotion engine/control loop
5. worker utilization/local execution
6. regression/qualification
7. local-model learning/training loop

This document is planning-only and review-first. It is grounded in current repo state (`config/promotion_manifest.json`, Stage-7/8 managers, RAG6/8 planner, qualify/promote tooling, and artifacts layout).

## Part 1 — Current-state assessment

### 1) Stage system
- Current version/level: `stage9-v1`, level 9 (building).
- Current real capability:
  - Multi-plan Stage-7/8 orchestration.
  - Persisted checkpoints (`artifacts/manager6/plans/<plan>/checkpoints.json`).
  - Resume support and rollback-contract metadata.
- Main blockers:
  - Deterministic rollback verification now exists, but replay/interruption contracts still need stronger mixed-outcome guarantees.
  - Stage-9 is operational preview, not production default.
- Main dependencies: Manager strategy quality, RAG cluster quality, qualification gates.
- Current contribution to Codex-5.1 replacement: medium. It can run bounded complex multi-target workflows, but still needs stronger deterministic recovery guarantees.

### 2) Manager/orchestration system
- Current version/level: `manager9-v1`, level 9 (building).
- Current real capability:
  - History-weighted strategy selection.
  - Explicit retry/split/defer state transitions.
  - Subplan reconciliation and class-budgeted gating.
  - Qualification-aware strategy posture + family-memory/budget-forecast decision tags.
- Main blockers:
  - Strategy memory now spans worker-family outcomes, but remains lane-local and non-hierarchical.
  - Long-horizon policy learning still lacks proactive multi-family repackaging.
- Main dependencies: Worker budget feedback quality, RAG calibration quality.
- Current contribution to Codex-5.1 replacement: high for bounded orchestration, medium for sustained high-complexity problem solving.

### 3) Retrieval / RAG system
- Current version/level: `rag9-v1`, level 9 (building).
- Current real capability:
  - Lane-clean clustered planning.
  - Conflict-risk and execution-yield metadata.
  - Ordered subplans for manager execution.
- Main blockers:
  - Execution-feedback calibration is now baseline but still family/cohort-oriented rather than fully predictive across mixed-family plans.
  - Remaining noisy edge cases still need stronger path-level suppression and conflict priors.
- Main dependencies: Manager outcome telemetry, qualification assertions on planning quality.
- Current contribution to Codex-5.1 replacement: medium-high for code-target discovery and packaging.

### 4) Promotion engine / control loop
- Current version/level: `level10-promote-v2`, level 8.
- Current real capability:
  - Subsystem gate matrix generation.
  - Apply-time gate enforcement.
  - Auditable decision history.
- Main blockers:
  - Promotion policy remains lane-metric-first in several paths.
  - Subsystem readiness is enforced, but not deeply weighted in primary scoring logic.
- Main dependencies: Qualification v8+ determinism and robust subsystem metrics.
- Current contribution to Codex-5.1 replacement: low-medium (governs rollout quality but does not directly improve coding capability).

### 5) Worker utilization / local execution
- Current version/level: `worker-routing-v2`, level 8.
- Current real capability:
  - Class-budgeted routing decisions.
  - Budget-driven defer behavior integrated into orchestration traces.
- Main blockers:
  - No adaptive budget tuning from historical yield/failure.
  - No mature utilization SLOs by task class and complexity tier.
- Main dependencies: Manager state machine, regression metrics, learning loop.
- Current contribution to Codex-5.1 replacement: medium. Local execution is active but not yet maximized for hard task classes.

### 6) Regression / qualification framework
- Current version/level: `qualify-v2`, level 8.
- Current real capability:
  - Subsystem-oriented v8 gate assertions.
  - Machine-readable qualification history.
  - Stage8/Manager8/RAG8 metric snapshots.
- Main blockers:
  - Stage-8 deterministic regression assertions are not fully wired into operational packs (notably `micro_lane_stage7.sh` hard-gates).
  - Limited benchmark-style evaluation for high-complexity coding tasks.
- Main dependencies: Stage/Manager/RAG telemetry consistency and promotion policy.
- Current contribution to Codex-5.1 replacement: medium-low (measurement quality improving, but not yet enough to prove replacement at scale).

### 7) Learning/training/improvement loop for local coding model
- Current version/level: not formalized as a dedicated versioned subsystem (functionally early-stage).
- Current real capability:
  - Rich traces/history are collected.
  - Failure classes increasingly convert into guards/routing rules.
- Main blockers:
  - No formal curriculum pipeline turning traces into training-ready datasets and eval cohorts.
  - Weak separation between “wrapper got better” vs “model got better.”
- Main dependencies: Worker utilization data quality, regression framework maturity, manager/rag explanation artifacts.
- Current contribution to Codex-5.1 replacement: low today; this is the key multiplier needed to make the local model itself stronger.

## Part 2 — Define the target

## Version 15 target by subsystem

### Stage system at v15
- Autonomous multi-phase execution with deterministic checkpoint/replay and verified rollback semantics.
- Supports bounded heterogeneous multi-plan jobs with conflict-aware partitioning and safe partial-completion contracts.

### Manager system at v15
- Hierarchical orchestrator with long-horizon adaptive strategy policy.
- Explicit finite-state lifecycle for retry/split/drop/rescue/defer/manual escalation.
- Uses persistent policy memory and confidence-aware decisioning.

### RAG system at v15
- Execution-feedback-calibrated retrieval and clustering.
- Adaptive conflict/yield estimation, robust lane/domain intent handling, and reliable companion expansion without out-of-lane noise.

### Promotion engine at v15
- Subsystem-readiness-first promotion governance.
- Deterministic apply-time enforcement with staged rollout profiles and rollback-aware promotion contracts.

### Worker utilization at v15
- Local-first routing by default for all safe classes up to defined complexity tiers.
- Adaptive class budgets and escalation thresholds tuned from measured outcomes.

### Regression/qualification at v15
- Deterministic subsystem gate suite + benchmark harness for complex coding tasks.
- Continuous machine-readable history with trend-based decision support.

### Learning/training loop at v15
- Stable data pipeline from traces -> curated datasets -> model adaptation -> benchmark verification.
- Clear attribution of gains to model improvement vs orchestration changes.

## “Local system replaces Codex 5.1-level work” (practical repo definition)

For this repo, replacement means the local stack can independently handle target complex coding classes:
- multi-file refactors within allowed scope,
- orchestration/manager/RAG architecture changes,
- non-trivial bug fixing with iterative retry/reconciliation,
- safe shell/script target handling with explicit contracts.

Sustained complexity requirements:
- complete bounded multi-subplan jobs with low avoidable failure rate,
- recover from interruption/partial failure without human rescue in most cases,
- preserve auditability and safety invariants.

Quality/safety requirements:
- deterministic guardrails (scope, shell risk, literal safety, rollback semantics),
- reproducible qualification evidence,
- promotion gating based on subsystem readiness.

Out-of-scope at first replacement milestone:
- unrestricted broad-repo redesign,
- unsafe shell operations outside established policy,
- highly ambiguous tasks with no anchor/contract and no safe fallback path.

## Part 3 — Milestone ladder from current state to Version 15

Coarse major milestones only.

### Stage system ladder
- Current: `stage9-v1`
- Next: `stage10` — stronger deterministic replay/interruption contracts across mixed-family outcomes.
- Mid: `stage11` — production-capable resumed multi-plan execution with deterministic conflict isolation.
- Mid: `stage13` — broader heterogeneous job contracts and safer autonomous reconciliation.
- Target: `stage15` — high-confidence autonomous stage planner with verified replay/rollback correctness.

### Manager system ladder
- Current: `manager8-v1`
- Next: `manager9` — long-horizon adaptive strategy memory.
- Mid: `manager11` — hierarchical policy planner across subplan families and escalation modes.
- Mid: `manager13` — proactive failure prevention and dynamic plan repackaging.
- Target: `manager15` — robust autonomous orchestration with explainable policy actions.

### RAG system ladder
- Current: `rag9-v1`
- Next: `rag10` — deeper predictive conflict/yield priors using broader execution cohorts.
- Mid: `rag11` — robust query-intent/domain fusion with adaptive link confidence.
- Mid: `rag13` — predictive conflict/yield modeling and context-window-efficient plan packaging.
- Target: `rag15` — high-precision retrieval/planning substrate for autonomous coding workflows.

### Promotion engine ladder
- Current: `level10-promote-v2`
- Next: `v3` — subsystem-weighted promotion decisions.
- Mid: `v5` — rollout profiles with auto-revert semantics.
- Mid: `v7` — predictive readiness scoring and staged adoption control.
- Target: `v15` — governance-quality promotion control loop with deterministic policy contracts.

### Worker utilization ladder
- Current: `worker-routing-v2`
- Next: `v3` — adaptive class-budget tuning.
- Mid: `v7` — complexity-tier routing with confidence-aware escalation.
- Mid: `v11` — local-first execution at high coverage with bounded manual fallback.
- Target: `v15` — maximized safe local execution share with stable quality.

### Regression/qualification ladder
- Current: `qualify-v2`
- Next: `v3` — deterministic Stage-8 gate assertions in operational packs.
- Mid: `v7` — subsystem benchmark suites for complex coding classes.
- Mid: `v11` — model-vs-orchestration attribution metrics.
- Target: `v15` — decision-grade qualification stack for autonomous operation.

### Learning/training loop ladder
- Current: early-stage (implicit, rule-heavy).
- Next: `v9` equivalent capability — trace curation pipeline + failure/success taxonomy.
- Mid: `v11` — curriculum and replay datasets tied to benchmark tasks.
- Mid: `v13` — controlled model adaptation experiments with gating.
- Target: `v15` — continuous improvement loop with clear model capability gains.

## Part 4 — Codex 5.1 replacement milestone

### Milestone name
**“Local system reaches Codex 5.1-level task replacement for bounded complex coding tasks.”**

### Target task classes (first wave)
- Manager/stage orchestration upgrades involving multi-file edits and policy-safe behavior changes.
- RAG retrieval/ranking and plan-packaging upgrades with validation.
- Stage-8 multi-plan runs requiring split/retry/resume/reconcile semantics.
- Safety-preserving script/shell target handling with explicit contracts.

### What local model must do directly
- Produce correct first-attempt code for non-trivial multi-file tasks at materially higher rate.
- Interpret and apply failure-memory signals without requiring constant manager rescue.
- Generate safe, auditable edits that satisfy contract preflight.

### What manager/RAG/promotion must provide
- Manager: bounded adaptive recovery and explicit decision-state auditing.
- RAG: clean, high-yield target sets with low noise.
- Promotion/qualification: hard evidence gates that prevent false readiness claims.

### Success criteria
- Sustained success-rate threshold on defined complex task benchmark set.
- Low repeated-failure rate for previously solved failure classes.
- Demonstrated local-first execution share increase without quality regression.
- Qualification and promotion evidence agree on readiness.

### Failure signals (not yet achieved)
- High manager rescue dependence for routine complex tasks.
- Frequent contract preflight drops for common valid targets.
- No measurable increase in model-direct first-attempt success.
- Improvement only visible in wrapper heuristics, not benchmark outcomes.

### Prerequisites before declaring success
- Stage9, Manager9, RAG9 capabilities validated.
- Worker v3 and Qualify v3 in place.
- Benchmark suite and attribution metrics operational.

## Part 5 — Training and learning plan for the local coding model

### Data to collect (must be first-class)
- Per-attempt plan payloads, strategy decisions, retry transitions, and final outcomes.
- Per-target contract failures/successes with explicit failure class.
- Retrieval features (risk/yield/conflict/link metrics) and downstream execution outcome.
- Worker routing decisions and escalation reasons.

### Failure handling policy
- Convert repeated deterministic failure classes into:
  - guards (hard safety checks),
  - manager strategy rules,
  - RAG ranking penalties/filters,
  - curated negative training examples.

### Success handling policy
- Convert high-yield successful patterns into:
  - reusable contract templates,
  - preferred prompt/message shapes,
  - positive training examples by task class and complexity.

### Distinguish orchestration vs model gains
- Maintain paired evaluation slices:
  - “manager assist on” vs “manager assist constrained”.
  - “retrieval enriched” vs “retrieval baseline.”
- Track:
  - first-attempt success,
  - rescue-needed rate,
  - manual-escalation rate.
- Claim model improvement only when first-attempt and low-rescue metrics improve on fixed benchmark sets.

### Rule/config first, training second
- First: encode deterministic failures into guards/routing.
- Next: accumulate stable labeled traces.
- Then: generate training/fine-tuning curriculum from validated trace cohorts.
- Finally: run controlled adaptation experiments with regression gates before rollout.

### Local-first without chaos
- Increase local default scope by explicitly promoted task classes only.
- Budget escalation and failure thresholds per class.
- Freeze expansion if regression/quality gates fail.

## Part 6 — Local-first execution policy

### Default local now
- Stage-3/5/6/7/8 safe classes in `bin/` with valid contracts and bounded plans.
- Manager/RAG evolution tasks with deterministic regression proof requirements.

### Move local next
- More heterogeneous multi-file refactors inside scoped families.
- Increased script/shell-safe classes with explicit anchor strategies.

### Still requires higher-level/manual support
- Ambiguous targets with no safe anchor/contract.
- Cross-domain tasks outside current lane policy and safety envelope.

### Progressive local execution share expansion
- Raise local share only when:
  - failure budget holds,
  - regression gates stay green,
  - first-attempt quality trend improves.
- Per-phase target local share (guideline):
  - current: ~60-70% safe classes
  - milestone (Codex 5.1 replacement gate): 80%+ targeted complex class
  - v15 target: 90%+ within declared scope

### Meaningful share metrics
- Local-executed task count by complexity tier.
- Local first-attempt success rate.
- Rescue/manual escalation ratio.
- Repeated-failure recurrence rate by class.

## Part 7 — Build order and roadmap priorities

## Recommended build order
1. Worker v3 adaptive budgets (feeds manager quality quickly).
2. Manager 9 adaptive long-horizon strategy.
3. RAG 9 execution-feedback calibration.
4. Stage 9 deterministic rollback verification.
5. Qualify v3 deterministic Stage-8 assertions in operational pack.
6. Promotion v3 subsystem-weighted scoring.
7. Codex-5.1 replacement benchmark gate.
8. Progression toward v11/v13/v15 tiers.

## Top 5 highest-leverage initiatives
1. Establish benchmarked complex-task evaluation set for Codex-5.1 replacement gate.
2. Implement manager long-horizon policy memory with measurable rescue reduction.
3. Add RAG feedback calibration loop tied to actual execution outcomes.
4. Complete deterministic Stage-8 regression and rollback verification gates.
5. Build training-data curation pipeline from traces with strict labeling standards.

## Top 5 “do not get distracted by this yet”
1. Stage 16+ naming/planning before v9 gate completion.
2. Broad policy rewrites without evidence from benchmark deltas.
3. Cosmetic telemetry expansion without decision impact.
4. New lane proliferation before current lane quality is stable.
5. Large architecture rewrites that bypass current safety contracts.

## Part 8 — Review-ready execution roadmap

## Phase A — Stabilize v8 completions (near-term)
- Goal: close partial v8 blockers (worker/promotion/qualification).
- Entry: current `stage9/manager9/rag9` operational.
- Exit:
  - worker adaptive budget tuning landed,
  - qualification deterministic stage8 assertions landed,
  - promotion subsystem-weighted scoring landed.
- Risks: false confidence from partial metrics.
- Decision gate: human review of benchmark design and gate definitions.

## Phase B — Build v9 capability tier
- Goal: complete Stage9/Manager9/RAG9 and supporting controls.
- Entry: Phase A complete and stable.
- Exit:
  - deterministic rollback verification,
  - manager long-horizon strategy memory,
  - rag feedback-calibrated ranking.
- Risks: overfitting policy to recent traces.
- Decision gate: benchmark pass against Codex-5.1 replacement prerequisites.

## Phase C — Codex 5.1 replacement milestone
- Goal: declare first strategic replacement gate for target complex classes.
- Entry: v9 capabilities + benchmark harness + attribution metrics.
- Exit:
  - sustained pass on task-class benchmarks,
  - acceptable rescue/escalation rates,
  - promotion/qualification evidence aligned.
- Risks: wrapper-improvement illusion vs model improvement.
- Decision gate: explicit human sign-off with failure-mode review.

## Phase D — v11/v13 to v15 trajectory
- Goal: scale from milestone success to robust v15 autonomy.
- Entry: Phase C success.
- Exit:
  - expanded task coverage,
  - high local-execution share in-scope,
  - stable safety + quality under continuous change.
- Risks: expanding scope too quickly.
- Decision gate: quarterly architecture and safety review.

## Part 9 — Immediate next actions

### Next 3 most important actions
1. Finalize and approve the Codex-5.1 replacement benchmark task set and pass criteria.
2. Implement Worker v3 adaptive budget tuning with measurable effect on manager rescue rates.
3. Wire deterministic Stage-8 assertions into `bin/micro_lane_stage7.sh` and enforce them in qualification gates.

### Next 3 most important human review decisions
1. Replacement milestone pass thresholds (success, rescue, escalation, recurrence).
2. Whether promotion decisions should become subsystem-first immediately at v3 or staged gradually.
3. Acceptable scope boundary for “in-scope complex tasks” at replacement milestone.

### Next 3 things Codex should not implement before roadmap approval
1. Stage10+ capability work that depends on unapproved benchmark/gate definitions.
2. New lane classes or expanded unsafe target scope.
3. Model-training/fine-tuning rollout without approved trace curation and attribution policy.
