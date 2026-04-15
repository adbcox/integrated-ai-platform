# Claude-Code Roadmap (Governing)

## 1. Purpose
This repository is building a local-first autonomous coding runtime that can complete bounded complex coding tasks at a Codex-replacement level, then advance toward Version 15 subsystem targets.

The intended outcome is Claude Code-like operator value (terminal-native autonomous edit/test/fix loops with explicit control), implemented with open-source-first components and governed by this repo's replacement gate, qualification, and promotion discipline.

This roadmap directly supports the local-first/Codex-reduction goal by prioritizing:
- strong autonomous coding runtime primitives,
- safe bounded execution,
- measurable first-attempt quality gains,
- trusted model-vs-wrapper attribution.

## 2. Current strengths
Grounded in current repo state and the deep research report:
- staged orchestration with resume/checkpoint semantics (`stage7_manager`, `stage_rag6_plan_probe`, manager traces/plans).
- framework control-plane baseline with job schema, scheduler, worker pool, inference adapter, state artifacts, and learning hooks (`framework/*`, `bin/framework_control_plane.py`).
- artifact-driven benchmark/campaign/curation/learning loop and replacement metrics (`bin/codex51_*`, `docs/codex51-benchmark-ops.md`).
- promotion/qualification governance with subsystem-level evidence surfaces (`bin/level10_qualify.py`, `bin/level10_promote.py`, `config/promotion_manifest.json`).
- trusted-pattern intake and reusable-code-library generation paths in learning outputs.

## 3. Key missing layers
The report-identified missing runtime layers that must now be built as first-class code:
- typed Tool System (action/observation contract, schema validation, auditable tool traces).
- Workspace abstraction (repo-scoped execution context, deterministic paths, artifact roots).
- permission engine (allow/ask/deny policy by tool/action/path/command class).
- sandboxed command/test execution (bounded environment isolation and enforceable constraints).
- inner-loop autonomy runtime (explicit edit -> run -> interpret -> repair loop with budgets and stop conditions).
- stronger codebase understanding substrate (repomap/symbol-aware + semantic retrieval integration).
- evaluation/promotion discipline tied to runtime-level autonomy metrics (not wrapper-only gains).
- continuous learning integration from runtime trajectories back into priors/replay/prevention.

## 4. Milestone roadmap

### Milestone M1: Runtime Contract Foundation
Objective:
- establish typed tool/workspace/permission/sandbox contracts and route real framework jobs through them.

Required deliverables:
- `framework/tool_system.py` with typed action/observation schemas.
- `framework/workspace.py` workspace controller abstraction.
- `framework/permission_engine.py` rule-based allow/deny decisions.
- `framework/sandbox.py` bounded shell execution adapter.
- worker runtime integration and trace evidence.

Dependencies:
- existing framework scheduler/state/learning modules.

Acceptance criteria:
- at least one real repo task class runs end-to-end via tool+workspace+permission+sandbox stack.
- artifacts include command traces + permission decisions.

### Milestone M2: Inner-Loop Autonomous Repair
Objective:
- codify bounded edit/test/fix cycles with explicit budgets and stop reasons.

Required deliverables:
- runtime loop contract for iterative repairs.
- failure taxonomy and retry strategy selection hooks.
- manager-visible loop telemetry.

Dependencies:
- M1 runtime primitives.

Acceptance criteria:
- bounded complex class shows fewer manual interventions and improved first-attempt or first-loop success.

### Milestone M3: Codebase Understanding Upgrade
Objective:
- improve multi-file precision with repomap + semantic + symbol-aware retrieval integration.

Required deliverables:
- repomap artifact generation path.
- retrieval join layer for runtime planning context.
- context budget policy by task class.

Dependencies:
- M1 tool/runtime traces and M2 loop instrumentation.

Acceptance criteria:
- measurable reduction in wrong-target edits and retry churn on representative tasks.

### Milestone M4: Autonomy Safety and Policy Hardening
Objective:
- reduce unsafe automation risk while increasing autonomous execution share.

Required deliverables:
- compound command policy evaluation and pre-tool hooks.
- prompt-injection guard checks on tool outputs.
- policy profiles aligned to bounded task classes.

Dependencies:
- M1 permission and sandbox enforcement.

Acceptance criteria:
- no policy bypasses in regression packs; unsafe attempts deterministically blocked/escalated.

### Milestone M5: Qualification, Promotion, and Learning Convergence
Objective:
- make runtime autonomy improvements promotion-eligible via hard evidence and attribution.

Required deliverables:
- runtime-specific gate assertions in qualification.
- model-vs-wrapper attribution deltas tied to runtime loop outcomes.
- replay/training export from runtime trajectories.

Dependencies:
- M1-M4.

Acceptance criteria:
- promotion decisions can reference deterministic runtime capability evidence, not docs-only or wrapper-only gains.

## 5. Ranked implementation priorities
1. typed tool/workspace/permission/sandbox runtime core (M1).
2. inner-loop bounded autonomous repair contract (M2).
3. command-policy hardening (compound command semantics + pre-tool checks) (M4).
4. codebase understanding substrate (repomap + symbol/semantic retrieval) (M3).
5. runtime-focused qualification assertions and dashboards (M5).
6. replay-priority execution queue integrated with manager policy updates.
7. model/backend selection policy by task class and risk tier.
8. resource-aware scheduling (CPU/memory/concurrency budgets) across backend profiles.
9. training-data export hardening for SFT/DPO-ready trajectory bundles.
10. rollout safety controls for runtime autonomy profiles in promotion engine.

## 6. Top deliverable to start now
Top deliverable: Milestone M1 bounded slice.

Why first:
- it converts existing framework scaffolding into a real autonomous coding runtime boundary.
- it enables safe command/test execution and permission evidence, unlocking all later autonomy work.
- it is the shortest path to measurable capability gain across execution, learning, and governance layers.

This session implementation slice:
- add typed tool action/observation contract,
- add workspace controller,
- add permission policy evaluator,
- add sandboxed shell executor abstraction,
- wire worker runtime to use these for real task execution.

## 7. Anti-drift rule
This file is the governing technical roadmap for the autonomous coding runtime phase.

Future sessions must align implementation choices to this roadmap unless new empirical evidence (benchmark/regression/runtime traces) justifies an explicit roadmap revision in-repo.

Docs-only, telemetry-only, or version-label-only changes do not count as roadmap execution progress without real code-path movement and real-path rerun evidence.
