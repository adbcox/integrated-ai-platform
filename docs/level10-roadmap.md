# Level-10 Roadmap (System-Wide)

This roadmap defines Level-10 goals across the six major subsystems and ties each one to concrete repo paths, current status, blockers, and next implementation steps.

## Snapshot

| Subsystem | Current level | Production level | Candidate level | Preview level | Next target |
| --- | --- | --- | --- | --- | --- |
| Stage system | 7 | 3 | 5 | 7 | 8 |
| Manager system | 6 | 4 | 5 | 6 | 7 |
| Retrieval / RAG | 6 | 1 | 3 | 6 | 7 |
| Promotion engine | 6 | 3 | 5 | 6 | 7 |
| Worker utilization | 5 | 3 | 5 | 6 | 6 |
| Regression / qualification | 5 | 3 | 5 | 6 | 6 |

The source of truth for these levels is now `config/promotion_manifest.json` under `subsystem_levels`.

## Version 8 Build List

The concrete cross-subsystem upgrade plan for the next major tier lives in:
- `config/promotion_manifest.json` -> `version8_upgrade_list` (canonical machine-readable source)
- `docs/version8-upgrade-list.md` (operator-facing summary with build order)

## Explicit version movement (this batch)

| Subsystem | Current version | Next target | Decision |
| --- | --- | --- | --- |
| Stage system | `stage7-v1` | `stage8-v1` | building |
| Manager system | `manager6-v1` | `manager7-v1` | building |
| Retrieval / RAG | `rag6-v1` | `rag7-v1` | building |
| Promotion engine | `level10-promote-v1` | `level10-promote-v2` | held |
| Worker utilization | `worker-routing-v1` | `worker-routing-v2` | deferred |
| Regression / qualification | `qualify-v1` | `qualify-v2` | held |

Rationale and validation requirements are tracked in `subsystem_versions` inside the manifest.

## Level-10 definitions and gaps

### 1) Stage system
- **Current**: Stage-6 preview exists (`bin/stage6_manager.py`) and orchestrates sequential Stage-5 jobs.
- **Level-10 definition**: autonomous multi-lane stage planner that safely promotes/rolls back based on objective evidence.
- **Main blockers**:
  - Stage-6 is preview-only and constrained to limited targets.
  - Promotion is not yet automatically driven by lane evidence.
- **Next code steps**:
  - Expand Stage-6 target coverage with lane-aware guards.
  - Add automatic stage-lane advancement gates keyed to qualification output.

### 2) Manager system
- **Current**: Manager-4 lane dispatcher + Manager-5 orchestration.
- **Level-10 definition**: hierarchical plan decomposition with bounded retries, lifecycle persistence, and auditable decision points.
- **Manager5-v3 landed**:
  - Failed secondary grouped targets now get bounded per-target refinement retry (`max_secondary_retries`) before final decision.
  - If a retried secondary still fails, Manager-5 can mark a bounded drop and continue remaining grouped jobs (`continue_on_secondary_failure`) instead of aborting the whole plan.
  - Plan history now emits `partial_success` when grouped execution succeeds with bounded secondary drops.
- **Main blockers**:
  - Qualification loop is not fully integrated into manager decisions.
  - Retry/refinement policy remains simple.
- **Next code steps**:
  - Policy-driven retry strategy (retry classes, cool-down windows, bounded refinements).
  - Manager gate integration with unified qualification report.

### 3) Retrieval / RAG
- **Current**: RAG-4 uses RAG-3 output and companion hints for Stage-6.
- **Level-10 definition**: provenance-rich, confidence-calibrated retrieval that reliably ranks primary + companion anchors for orchestration.
- **Main blockers**:
  - Confidence calibration was shallow.
  - Companion reason metadata was not rich enough for downstream orchestration.
- **Next code steps**:
  - Add confidence calibration telemetry and threshold tuning.
  - Add lane-specific retrieval quality baselines to qualification.

### 4) Promotion engine
- **Current**: lane-aware manifest + candidate qualification (`bin/promotion_qualify.py`).
- **Level-10 definition**: unified promotion control plane with subsystem-level policies and evidence-based lane progression.
- **Main blockers**:
  - Qualification remained candidate-lane focused.
  - No single report linked all subsystems to promotion evidence.
- **Next code steps**:
  - Promote unified qualification output into promotion decision records.
  - Add machine-readable promotion decisions with explicit subsystem pass/fail.

### 5) Worker utilization
- **Current**: local worker is used for Stage-3/4/5 classes with bounded task classes (`config/aider_task_classes.json`).
- **Level-10 definition**: worker-first execution that maximizes safe local throughput with clear escalation boundaries and measurable success.
- **Main blockers**:
  - Worker outcomes were not surfaced consistently in system-wide qualification.
  - Escalation metrics are not tied to stage progression.
- **Next code steps**:
  - Add class-level worker utilization metrics to qualification output.
  - Connect escalation analytics to lane and stage policies.

### 6) Regression / qualification framework
- **Current**: lane-specific packs (`bin/micro_lane_regression.sh`, `bin/micro_lane_stage5.sh`) and candidate qualifier.
- **Level-10 definition**: continuous, minimal deterministic validation with subsystem readiness scoring and promotion gating.
- **Main blockers**:
  - Framework lacked subsystem-wide readiness scoring.
  - Preview-lane confidence checks were mostly manual.
- **Next code steps**:
  - Add stage6-specific deterministic regression pack.
  - Feed qualification outputs directly into promotion policy transitions.

## Implementation focus for this batch

1. Stage-7 multi-plan orchestration (`bin/stage7_manager.py`) with explicit subplan lifecycle and partial-completion reconciliation.
2. Manager-6 split-on-failure recovery semantics over Stage-6 subplan execution.
3. RAG-6 clustered subplan planner (`bin/stage_rag6_plan_probe.py`) that emits lane-clean grouped subplans for Stage-7.
4. Coarse major-version source-of-truth updates in `config/promotion_manifest.json`.

Those changes are now implemented in:
- `bin/stage7_manager.py`
- `bin/stage_rag6_plan_probe.py`
- `bin/micro_lane_stage7.sh`
- `bin/stage6_manager.py`
- `config/promotion_manifest.json`
