# Phase 3 Developer-Assistant MVP Baseline Specification

**Spec ID**: PHASE3-MVP-BASELINE-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 3 (developer_assistant_mvp)  
**Authority sources**: governance/phase2_substrate_baseline.v1.yaml, governance/local_run_validation_pack.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the Phase 3 developer-assistant MVP baseline — the first real product slice built on top of the Phase 2 substrate. Phase 3 produces a bounded developer-assistant loop that can intake a repo, accept a task, inspect relevant paths, run validations, and produce a structured result package.

The machine-readable form is `governance/phase3_mvp_baseline.v1.yaml`. This document is the human-readable companion.

---

## Phase Identity

- **Phase ID**: `phase_3`
- **Label**: Phase 3 — Developer Assistant MVP
- **Status**: `in_progress` (gate met by P3-01)
- **Scope**: New-file implementation only; no modifications to existing live runtime modules

---

## Required Modules

### Phase 3 (P3-01)

| Module | Classes |
|--------|---------|
| `framework/repo_intake_v1.py` | `RepoIntakeV1` |
| `framework/developer_task_v1.py` | `DeveloperTaskV1` |
| `framework/developer_assistant_loop_v1.py` | `DeveloperAssistantLoopV1`, `LoopResultV1` |
| `framework/result_package_v1.py` | `ResultPackageV1` |
| `framework/mvp_benchmark_runner_v1.py` | `MVPBenchmarkRunnerV1`, `BenchmarkSuiteResultV1` |

### Phase 2 (inherited)

| Module | Classes |
|--------|---------|
| `framework/substrate_runtime_v1.py` | `SubstrateRuntimeV1` |
| `framework/substrate_conformance_v1.py` | `SubstrateConformanceCheckerV1` |

---

## Required Capabilities

| Capability | Module | Description |
|-----------|--------|-------------|
| `repo_intake` | `repo_intake_v1.py` | Accept repo root + task metadata as typed `RepoIntakeV1` |
| `bounded_task_shape` | `developer_task_v1.py` | Task with target_paths, validation_sequence, retry_budget |
| `substrate_backed_loop` | `developer_assistant_loop_v1.py` | Inspect + validate loop using substrate tools |
| `result_packaging` | `result_package_v1.py` | Bundle loop outputs into `ResultPackageV1` |
| `benchmark_execution` | `mvp_benchmark_runner_v1.py` | Run ≥3 synthetic tasks; report pass_rate |

---

## Developer Assistant Loop

The `DeveloperAssistantLoopV1.run()` method executes in three steps:

1. **Inspect**: Read each `target_path` using `read_file` tool; record inspection status
2. **Validate**: Execute `validation_sequence` steps; each is synthetic (workspace structure check)
3. **Emit**: Optionally publish a result summary to an artifact path using `publish_artifact` tool

Returns a `LoopResultV1` with:
- `inspected_paths` — paths read during inspection
- `validations_run` — validation steps executed
- `validation_results` — step → pass/fail map
- `final_outcome` — success if all validation steps pass
- `escalation_status` — always `NOT_ESCALATED` for synthetic steps

---

## Benchmark Runner

`MVPBenchmarkRunnerV1.run()` executes 4 default benchmark cases:

| Case | Kind | Target |
|------|------|--------|
| bench-001 | inspect | `framework/repo_intake_v1.py` |
| bench-002 | inspect | `framework/substrate_runtime_v1.py` + `substrate_conformance_v1.py` |
| bench-003 | validate | `governance/phase2_substrate_baseline.v1.yaml` |
| bench-004 | inspect | `framework/developer_task_v1.py` + `result_package_v1.py` |

Returns `BenchmarkSuiteResultV1` with `tasks_run`, `tasks_passed`, `pass_rate`, `failure_modes`.

---

## Completion Requirements

| Requirement | Evidence |
|------------|---------|
| `bounded_loop_runs` | Loop completes; `LoopResultV1` has `final_outcome` + `escalation_status` |
| `artifact_complete_outputs` | `ResultPackageV1.to_dict()` has all required fields |
| `benchmark_pack_executes` | `tasks_run >= 3`, `pass_rate` in [0.0, 1.0] |
| `explicit_escalation_accounting` | All outputs report `NOT_ESCALATED` |

---

## Completion Gate

Phase 3 MVP is complete when:
1. All completion requirements are met
2. Benchmark `pass_rate > 0.75` on default suite
3. Seam tests pass
4. `make check` passes

**Gate status**: Met by P3-01.

---

## Remaining Blockers

### P3-BLOCKER-01 (deferred to Phase 4)

The loop executes synthetic validation steps only. Real patch/apply/commit steps require a local model (Aider/Ollama) to generate code changes. Phase 4 will wire a local model backend into the loop.

### P3-BLOCKER-02 (deferred to Phase 4)

Benchmark tasks are inspect/validate only. Real patch_generation and apply cases require the local model backend and will be scored against real diffs in Phase 4.

---

## Relationship to Governance

| Baseline element | Authority |
|-----------------|-----------|
| Required modules | governance/phase2_substrate_baseline.v1.yaml (Phase 3 scope) |
| Completion requirements | governance/local_run_validation_pack.v1.yaml |
| Escalation accounting | governance/definition_of_done.v1.yaml |
| Benchmark structure | governance/autonomy_scorecard.v1.yaml (pass_rate metric) |
