# Roadmap Index

Derived index of roadmap state. Canonical status is in `docs/roadmap/items/RM-*.yaml`.
Artifact note: `artifacts/**` references in this document are derived local evidence
surfaces and may be gitignored/non-committed; they are never canonical authority.

## Control Window Sovereignty Status

- Latest assessment: `LOCAL-EXECUTION-SOVEREIGNTY-CLOSEOUT-1`
- Verdict: `YES`
- Status surface: `governance/local_execution_sovereignty_status.v1.yaml`
- Evidence artifact: `artifacts/autonomy/local_execution_sovereignty_verdict.json`
- Critical path authority: `docs/roadmap/LOCAL_AUTONOMY_CRITICAL_PATH.md`

## Execution-Governance Hardening Index

- Canonical contract: `governance/roadmap_execution_contract.v1.yaml`
- Schema: `schemas/roadmap_execution_contract.v1.json`
- Validator: `bin/validate_roadmap_execution_contracts.py`
- Pull and blocker artifacts:
  - `artifacts/planning/next_pull.json`
  - `artifacts/planning/blocker_registry.json`

## Completed Integrated Expansion Index

- `RM-OPS-006` — Integrated operational expansion layer for governed ops/home/intel/inventory (`completed`, `archived`)
- `RM-HOME-005` — Governed home/local-environment intents through unified runtime (`completed`, `archived`)
- `RM-INTEL-003` — Governed intelligence watch and operator analysis surface (`completed`, `archived`)
- `RM-INV-003` — Procurement and search baseline reused as inventory decision-support core (`completed`, `archived`)

## Completed RM-OPS-007 Convergence Index

- `RM-OPS-007` — Operational convergence and archive-truth hardening (`completed`, `archived`)
- Convergence runner: `bin/run_rm_ops007_archive_convergence.py`
- Convergence validator: `bin/validate_rm_ops007_convergence.py`
- Convergence report: `artifacts/operations/rm_ops007_archive_convergence_report.json`
- Validation artifact: `artifacts/validation/rm_ops007_convergence_validation.json`
- Held items after convergence: `RM-DEV-008`, `RM-DEV-009` (`status=completed`, `execution_status=not_started`)

Integrated expansion evidence:
- `governance/integrated_ops_home_intel_inventory_policy.v1.yaml`
- `framework/integrated_ops_home_intel_inventory.py`
- `bin/run_integrated_ops_expansion.py`
- `bin/validate_integrated_ops_expansion.py`
- `artifacts/operations/integrated_ops_expansion_run.json`
- `artifacts/validation/integrated_ops_expansion_validation.json`

## Completed Canonical Item

- `RM-UI-005` — Local execution control dashboard, routing layer, Aider orchestration, and OpenHands interface (`completed`, `archived`)
  - canonical file: `docs/roadmap/items/RM-UI-005.yaml`
  - first-slice artifact: `artifacts/rm_ui005/control_window_state.json`

## Completed NEXT-Tier Expansion

- `RM-GOV-009` — Connector control-plane + canonical intake activation (`completed`, `archived`)
- `RM-AUTO-001` — Plain-English goal to bounded execution contract (`completed`, `archived`)
- `RM-DEV-001` — Apple/Xcode governed runtime capability (`completed`, `archived`)

NEXT-tier evidence:
- `governance/connector_control_plane_policy.v1.yaml`
- `governance/autonomy_goal_execution_contract.v1.yaml`
- `governance/apple_xcode_runtime_contract.v1.yaml`
- `artifacts/validation/next_tier_autonomy_expansion_validation.json`

## Completed Bundles

**Phase 1 Runtime Foundation** (1 item, completed):
- `RM-PHASE1-001` — Ollama-first inference gateway and runtime foundation ✓

Runtime foundation evidence:
- 1 runtime profile authority (`governance/runtime_profiles.v1.yaml`)
- 5 runtime modules (`runtime/inference_gateway.py`, `workspace_controller.py`, `artifact_writer.py`, `command_runner.py`, `runtime_executor.py`)
- 6 runtime schemas (`runtime/schemas/*.v1.json` - all valid and tested)
- 4 validation scripts:
  * `bin/validate_phase1_runtime_foundation.py` — foundation validation (25+ checks)
  * `bin/validate_phase1_runtime_execution_path.py` — execution path validation (16+ checks)
  * `bin/validate_phase1_closeout.py` — comprehensive closeout validation (12 checks)
  * `bin/test_phase1_runtime_integration.py` — integration test suite (8 scenarios)
- 4 validation artifacts (all PASS):
  * `artifacts/validation/phase1_runtime_foundation_validation.json`
  * `artifacts/validation/phase1_runtime_execution_path_validation.json`
  * `artifacts/validation/phase1_closeout_validation.json`
  * `artifacts/validation/phase1_integration_tests.json`
- 3 proof artifacts:
  * `artifacts/examples/phase1_runtime_run_example.json` (foundation proof)
  * `artifacts/examples/phase1_execution_control_example.json` (control package)
  * `artifacts/examples/phase1_runtime_execution_example.json` (execution with session linkage)

## Completed Bundles (continued)

**Phase 2 Multi-Layer Substrate** (8 items: 8 completed):

### Phase 2 Core Infrastructure (Completed)
- `RM-CORE-001` — Introduce internal inference gateway ✓
- `RM-CORE-002` — Standardize model profiles ✓

Phase 2 core evidence:
- Canonical gateway: `framework/inference_gateway.py` (typed API, telemetry integration)
- Gateway adapter: `runtime/inference_gateway.py` (unified runtime path)
- Model profiles: `framework/model_profiles.py` (profile resolution)
- Profile authority: `governance/runtime_profiles.v1.yaml` (fast/balanced/hard)
- Validation: Foundation and closeout validators both PASS

### Phase 2 Operations Layer (Completed)
- `RM-OPS-001` — Execution tracing and monitoring ✓
- `RM-OPS-002` — Failure analysis and recovery ✓
- `RM-OPS-003` — Performance profiling and optimization ✓

Phase 2 ops evidence:
- Execution tracer: `runtime/execution_tracer.py` (structured trace events)
- Failure classifier: `runtime/failure_classifier.py` (taxonomy, recovery suggestions)
- Performance profiler: `runtime/performance_profiler.py` (timing, bottleneck analysis)
- OPS schemas: `runtime/schemas/{execution_trace,failure_record,performance_profile}.v1.json`
- OPS validator: `bin/validate_phase2_ops.py` (comprehensive OPS validation)
- Validation artifact: `artifacts/validation/phase2_ops_validation.json` (PASS)

### Phase 2 UI Layer (Completed)
- `RM-UI-002` — Execution dashboard ✓
- `RM-UI-003` — Failure analyzer UI ✓
- `RM-UI-004` — Performance metrics display ✓

UI layer completed with real artifact consumption: all three modules integrate with OPS substrate

Phase 2 UI evidence:
- Execution dashboard: `framework/execution_dashboard_ui.py` (ExecutionDashboardUI class)
- Failure analyzer: `framework/failure_analyzer_ui.py` (FailureAnalyzerUI class)
- Performance metrics: `framework/performance_metrics_ui.py` (PerformanceMetricsUI class)
- Artifact loader: `framework/ops_artifact_loader.py` (OpsArtifactLoader for artifact discovery)
- UI validator: `bin/validate_phase2_ui.py` (9-check validator, 100% pass rate)
- Control center integration: `framework/control_center_server.py` (extended with OPS endpoints and UI rendering)
- Validation artifact: `artifacts/validation/phase2_ui_validation.json` (all 9/9 checks PASS)

## All Completed Bundles

**Phase 1 Runtime Foundation** (1 item, all completed):
- `RM-PHASE1-001` — Ollama-first inference gateway and runtime foundation ✓

Phase 1 runtime foundation evidence:
- 1 runtime profile authority (`governance/runtime_profiles.v1.yaml`)
- 5 runtime modules (`runtime/inference_gateway.py`, `workspace_controller.py`, `artifact_writer.py`, `command_runner.py`, `runtime_executor.py`)
- 6 runtime schemas (`runtime/schemas/*.v1.json` - all valid)
- 4 validators:
  * `bin/validate_phase1_runtime_foundation.py` — foundation validation (25+ checks)
  * `bin/validate_phase1_runtime_execution_path.py` — execution path validation (16 checks)
  * `bin/validate_phase1_closeout.py` — comprehensive closeout validation (12 checks)
  * `bin/test_phase1_runtime_integration.py` — integration test suite (8 scenarios)
- 4 validation artifacts (all PASS):
  * `artifacts/validation/phase1_runtime_foundation_validation.json`
  * `artifacts/validation/phase1_runtime_execution_path_validation.json`
  * `artifacts/validation/phase1_closeout_validation.json`
  * `artifacts/validation/phase1_integration_tests.json`
- 3 proof artifacts:
  * `artifacts/examples/phase1_runtime_run_example.json` (foundation proof)
  * `artifacts/examples/phase1_execution_control_example.json` (control package)
  * `artifacts/examples/phase1_runtime_execution_example.json` (execution with session linkage)

**Phase 0 Closure Bundle** (6 items, all completed):
- `RM-AUTO-001` — Goal-to-agent baseline (completed; archived)
- `RM-GOV-001` — Canonical roadmap authority registry (completed; archived)
- `RM-OPS-005` — Telemetry and audit pipeline (completed; archived)
- `RM-OPS-004` — Backup and disaster recovery (completed; archived)
- `RM-INV-002` — Inventory and capability mapping (completed)
- `RM-DEV-001` — Xcode and Apple-platform capability (completed; archived)

Governance foundation evidence:
- 6 comprehensive governance schemas (`governance/*.v1.yaml`)
- 7 architectural decision records (`governance/adr/*.md`)
- Definition of Done checklist (`docs/standards/DEFINITION_OF_DONE.md`)
- Validation script and 100% success proof (`artifacts/validation/phase0_closure_validation.json`)

**Integration Phase 1 Bundle** (5 items, all completed):
- `RM-INV-003` — Procurement and search baseline (completed)
- `RM-ED-001` — Edition builder baseline (completed)
- `RM-UI-001` — Master control center baseline (completed)
- `RM-DOCAPP-002` — Website generation baseline (completed)
- `RM-HW-001` — Electrical design baseline (completed)

Integration evidence: `governance/system_integration_manifest.v1.yaml`  
Execution report: `artifacts/integration_phase1_execution_report.md`

## Newly archived (phase0 global gate closure)

- `RM-GOV-002`

## Newly archived bundle

- `RM-DEV-002`
- `RM-DEV-004`
- `RM-DEV-007`
- `RM-CORE-005`
- `RM-GOV-005`
- `RM-INV-005`

## Previously archived bundles

- `RM-DEV-003`, `RM-INTEL-001`
- `RM-INV-004`, `RM-GOV-004`, `RM-AUTO-002`, `RM-DEV-006`, `RM-INTEL-002`, `RM-CORE-004`

## Evidence links

- `artifacts/governance/rm_bundle_6_closeout_validation.json`
- `artifacts/governance/rm_bundle_6_archive_validation.json`
- `artifacts/governance/phase0_global_gate_closure.json`

## Execution packs

See `docs/roadmap/EXECUTION_PACK_INDEX.md`.
