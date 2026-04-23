# Roadmap Master

Derived human-readable roadmap summary.
Canonical authority remains `docs/roadmap/items/RM-*.yaml`.

## Control Window Sovereignty Status

- Latest assessment: `LOCAL-EXECUTION-SOVEREIGNTY-CLOSEOUT-1`
- Verdict: `YES` (routine roadmap execution is sovereign on current live state)
- Machine-readable status: `governance/local_execution_sovereignty_status.v1.yaml`
- Evidence: `artifacts/autonomy/local_execution_sovereignty_verdict.json`
- Critical path authority: `docs/roadmap/LOCAL_AUTONOMY_CRITICAL_PATH.md`

## Execution-Governance Contract Hardening

Governed autonomous pull now enforces canonical execution contracts at item level.

- Contract definition: `governance/roadmap_execution_contract.v1.yaml`
- Contract schema: `schemas/roadmap_execution_contract.v1.json`
- Contract validator: `bin/validate_roadmap_execution_contracts.py`
- Selector enforcement + blocker truth:
  - `bin/compute_next_pull.py`
- `artifacts/planning/next_pull.json`
- `artifacts/planning/blocker_registry.json`

## Completed: Integrated Ops/Home/Intel/Inventory Expansion Slice

One bounded shared substrate slice now extends the closed autonomy baseline with a single
governed runtime path and evidence model across operations, home intents, intelligence watch,
and inventory decision support.

- `RM-OPS-006` — Integrated operational expansion layer (single intake/analysis/decision/evidence path) ✓ (archived)
- `RM-HOME-005` — Governed home/local-environment intents through unified runtime path ✓ (archived)
- `RM-INTEL-003` — Governed intelligence watch analysis integrated into operator queue ✓ (archived)
- `RM-INV-003` — Procurement baseline remains complete and is reused by integrated slice ✓ (archived)

Evidence:
- `governance/integrated_ops_home_intel_inventory_policy.v1.yaml`
- `framework/integrated_ops_home_intel_inventory.py`
- `bin/run_integrated_ops_expansion.py`
- `bin/validate_integrated_ops_expansion.py`
- `artifacts/operations/integrated_ops_expansion_run.json`
- `artifacts/validation/integrated_ops_expansion_validation.json`

## Completed: NEXT-Tier Autonomy Expansion Slice

- `RM-GOV-009` — Governed connector control-plane and canonical intake activation (github/gmail/google_calendar boundaries, deny-unlisted posture, runtime route constraints) ✓ (archived)
- `RM-AUTO-001` — Post-substrate plain-English goal to bounded execution contract (packet shaping, route gates, completion/escalation discipline, evidence gates) ✓ (archived)
- `RM-DEV-001` — Apple/Xcode capability aligned to governed local runtime execution authority (control-window and runtime linkage preserved) ✓ (archived)

Evidence:
- `governance/connector_control_plane_policy.v1.yaml`
- `governance/autonomy_goal_execution_contract.v1.yaml`
- `governance/apple_xcode_runtime_contract.v1.yaml`
- `bin/validate_next_tier_autonomy_expansion.py`
- `artifacts/validation/next_tier_autonomy_expansion_validation.json`

## Completed: RM-UI-005 Local Execution Control Window

- `RM-UI-005` — Local execution control dashboard, deterministic routing layer, Aider
  workload packetization, and OpenHands execution interface (canonical item-complete evidence satisfied; archived)
- Canonical item file: `docs/roadmap/items/RM-UI-005.yaml`
- Implemented first-slice surfaces:
  - `framework/rm_ui005_control_window.py`
  - `framework/rm_ui005_openhands.py`
  - `bin/rm_ui005_control_window.py`
  - `bin/rm_ui005_emit_state.py`
  - `artifacts/rm_ui005/control_window_state.json`

## Completed: Phase 0 Closure Bundle

6-item governance foundations bundle establishing authority, execution control, telemetry/audit, backup/DR, inventory, and Apple-platform capability — completed with comprehensive artifact set and validation proof.

- `RM-AUTO-001` — Goal-to-agent baseline (goal intake schema, task decomposition, bundle packaging, approval workflow) ✓ (archived)
- `RM-GOV-001` — Canonical roadmap authority (machine-readable registry and sync surfaces) ✓ (archived)
- `RM-OPS-005` — Telemetry and audit pipeline (event schema, trace model, audit evidence, validation proof) ✓ (archived)
- `RM-OPS-004` — Backup and disaster recovery (backup model, restore procedures, DR playbooks, rollback rules) ✓ (archived)
- `RM-INV-002` — Inventory and capability mapping (asset inventory schema, photo metadata linkage, capability classification) ✓
- `RM-DEV-001` — Xcode and Apple platform (Swift/ObjC support, build system, testing framework, code signing, AppStore deployment) ✓ (archived)

**Status**: All 6 items completed (P1 priority), Phase 0 governance foundation established  
**Validation**: All artifacts exist on disk and are valid; validation script passes with 100% success  
**Item files**: `docs/roadmap/items/RM-{AUTO-001,GOV-001,OPS-005,OPS-004,INV-002,DEV-001}.yaml`  
**Governance schemas**: 6 comprehensive schemas covering goal intake, execution governance, telemetry, backup/restore, inventory, and Apple workflow  
**ADRs**: 7 architectural decision records documenting session schema, tool system, workspace contract, inference gateway, permissions, artifacts, and autonomy scorecard  
**Validation artifact**: `artifacts/validation/phase0_closure_validation.json` (all checks pass)  
**Completion checklist**: `docs/standards/DEFINITION_OF_DONE.md`

## Completed: Phase 1 Runtime Foundation

1-item runtime foundation establishing local-first execution with Ollama primary and Claude API fallback — feature-complete with profile-based routing, deterministic workspace management, bounded command execution, structured artifact emission, execution harness, and comprehensive validation.

- `RM-PHASE1-001` — Ollama-first inference gateway and runtime foundation (profile authority, gateway, workspace controller, artifact writer, command runner, executor, schemas, validation, closeout) ✓

**Status**: Phase 1 runtime foundation layer (P1 priority), local-first execution baseline complete with comprehensive validation proof  
**Foundation execution**: All 5 runtime modules implemented, 6 schemas defined, validation passing (25+ checks)  
**Harness execution**: Runtime executor orchestrates session/job → profile → workspace → command → artifact flow with schema compliance  
**Validation coverage**: Closeout validator (12 checks), integration test suite (8 scenarios), all passing  
**Item file**: `docs/roadmap/items/RM-PHASE1-001.yaml`  
**Runtime modules**: `runtime/{inference_gateway,workspace_controller,artifact_writer,command_runner,runtime_executor}.py`  
**Schemas**: `runtime/schemas/{inference_request,inference_response,profile_selection,workspace_state,runtime_run_artifact,runtime_execution_result}.v1.json`  
**Authority**: `governance/runtime_profiles.v1.yaml` (fast/balanced/hard profiles)  
**Foundation validation**: `artifacts/validation/phase1_runtime_foundation_validation.json` (PASS, 25+ checks)  
**Harness validation**: `artifacts/validation/phase1_runtime_execution_path_validation.json` (PASS, 16+ checks)  
**Closeout validation**: `artifacts/validation/phase1_closeout_validation.json` (PASS, 12/12 checks)  
**Integration tests**: `artifacts/validation/phase1_integration_tests.json` (PASS, 8/8 tests)  
**Validators**: Foundation (25+ checks), execution-path (16 checks), closeout (12 checks), integration (8 scenarios)  
**Foundation proof**: `artifacts/examples/phase1_runtime_run_example.json` (end-to-end execution)  
**Harness proof**: `artifacts/examples/phase1_runtime_execution_example.json` (real session/job linkage)

## In Progress: Phase 2 Multi-Layer Substrate

Phase 2 establishes unified runtime substrate with ops and UI layers. Core infrastructure (CORE items) complete and validated. OPS layer (tracing, recovery, profiling) is proposed foundation. UI layer (monitoring, failure analysis, metrics) is blocked on OPS completion.

### Completed: Phase 2 Core Infrastructure

2-item core substrate establishing unified inference gateway and model profiling — complete with unified implementation and validation. Gateway is canonical single entrypoint; all execution routed through it.

- `RM-CORE-001` — Introduce internal inference gateway (unified gateway with typed API, profile resolution, injectable executor) ✓
- `RM-CORE-002` — Standardize model profiles (fast/balanced/hard profiles with selection heuristics) ✓

**Status**: Core infrastructure (P1 priority), inference gateway unified and validated  
**Canonical gateway**: `framework/inference_gateway.py` (InferenceGateway class, GatewayRequest/GatewayResponse, telemetry)  
**Gateway adapter**: `runtime/inference_gateway.py` (wraps canonical gateway, provides backward-compatible functions)  
**Profile authority**: `governance/runtime_profiles.v1.yaml` (fast/balanced/hard with context windows, timeouts, retry budgets)  
**Model profiles**: `framework/model_profiles.py` (ModelProfile dataclass, profile resolution)  
**Execution path**: `runtime/runtime_executor.py` uses unified gateway via adapter  
**Validation**: Foundation (PASS), closeout (PASS, 12/12 checks), all validators confirm unified path  
**Item files**: `docs/roadmap/items/RM-{CORE-001,CORE-002}.yaml`

### Completed: Phase 2 Operations Layer

3-item ops foundation adding execution tracing, failure recovery, and performance profiling.
Integrated into runtime_executor with comprehensive validation.

- `RM-OPS-001` — Execution tracing and monitoring (structured logs, session/job/command linkage) ✓
- `RM-OPS-002` — Failure analysis and recovery (retry policy, failure taxonomy, fallback routing) ✓
- `RM-OPS-003` — Performance profiling and optimization (timing metrics, resource tracking) ✓

**Status**: Ops substrate (P1 priority), all 3 items completed with validation passing  
**Implementation**: ExecutionTracer, failure_classifier, performance_profiler modules integrated into runtime_executor  
**Schemas**: 3 new schemas for execution_trace, failure_record, performance_profile  
**Validation**: bin/validate_phase2_ops.py confirms all OPS artifacts complete and consistent  
**Item files**: `docs/roadmap/items/RM-OPS-{001,002,003}.yaml` (status: completed)  
**Architecture**: Sequential integration — OPS-001 enables OPS-002 enables OPS-003 → UI items now unblocked  
**Readiness**: Completed; UI layer can proceed with implementation

### Completed: Phase 2 UI Layer

3-item UI layer for execution monitoring and failure analysis. Completed with real artifact consumption from OPS substrate.

- `RM-UI-002` — Execution dashboard (monitoring surface, trace viewer) ✓
- `RM-UI-003` — Failure analyzer UI (failure event display, recovery suggestions) ✓
- `RM-UI-004` — Performance metrics display (timing graphs, bottleneck viewer) ✓

**Status**: UI layer (P2 priority), implementation complete with validation  
**Item files**: `docs/roadmap/items/RM-UI-{002,003,004}.yaml` (status: completed)  
**Implementation**: Execution dashboard (7029 bytes), failure analyzer (2516 bytes), metrics UI (5531 bytes)  
**Real artifact consumption**: All three modules consume OPS execution traces, failure records, and performance profiles  
**Integration**: Extended control_center_server.py with /api/ops endpoints and unified dashboard rendering  
**Validation**: 9/9 checks passed; validator proves real artifact consumption  
**Validator**: `bin/validate_phase2_ui.py` with comprehensive coverage of UI modules and artifact integration

## Completed: Integration Phase 1 Bundle

5-item integration bundle defining capability baseline across procurement, deployment, UI, documentation, and hardware — now completed with full end-to-end integration demonstrated.

- `RM-INV-003` — Procurement evaluator (bin/procurement_evaluator.py) — Real part scoring, decision making, alternatives ✓
- `RM-ED-001` — Edition resolver (bin/edition_resolver.py) — Feature packaging, platform-specific deployment targets ✓
- `RM-UI-001` — Master control center (framework/control_center_server.py) — Web interface, real-time status, API endpoints ✓
- `RM-DOCAPP-002` — Website generator (bin/site_generator.py) — HTML generation, SEO metadata, sitemap ✓
- `RM-HW-001` — Hardware processor (bin/hardware_design_processor.py) — ESP32/Nordic BOM generation, design assistant ✓

**Status**: All items completed (P2 priority), real implementation deployed  
**Execution**: Full integration chain operational end-to-end (hardware → procurement → edition → website → UI)  
**Integration point**: `governance/system_integration_manifest.v1.yaml` + `bin/run_integration_demo.py` full orchestration  
**Item files**: `docs/roadmap/items/RM-{ED-001,INV-003,UI-001,DOCAPP-002,HW-001}.yaml`  
**Artifacts**: `artifacts/integration_demo/{01,02,03,04}_*.json`, `artifacts/integration_demo/INTEGRATION_SUMMARY.json`  
**Execution report**: `artifacts/integration_phase1_execution_report.md`

## Archived in this pass (phase0 global gate closure)

- `RM-GOV-002` — Reconcile source-of-truth surfaces

Evidence:
- `artifacts/governance/phase_authority_inventory.json`
- `artifacts/governance/phase0_residual_authority_closure.json`
- `artifacts/governance/phase0_global_gate_closure.json`

## Archived in this pass (formerly ready_for_archive)

- `RM-DEV-002` — Dual-model inline QC coding loop for the developer assistant
- `RM-DEV-004` — Embedded firmware assistant for Nordic and ESP platforms
- `RM-DEV-007` — Indexed code search and multi-repo retrieval backend
- `RM-CORE-005` — Identity, secrets, permissions, and trust-boundary management
- `RM-GOV-005` — Cycle, release, and batch-governance model for roadmap execution
- `RM-INV-005` — Asset-to-roadmap and asset-to-execution linkage layer

## Archived in this pass (RM-OPS-007 convergence)

- `RM-OPS-007` — Operational convergence and archive-truth hardening
- `RM-UI-005`
- `RM-AUTO-001`
- `RM-GOV-001`
- `RM-OPS-005`
- `RM-OPS-004`
- `RM-GOV-009`
- `RM-OPS-006`
- `RM-HOME-005`
- `RM-INTEL-003`
- `RM-INV-003`
- `RM-CORE-003`
- `RM-CORE-006`
- `RM-DEV-005`
- `RM-DOCAPP-002`
- `RM-ED-001`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-HW-001`

Held at `ready_for_archive` after convergence (insufficient execution readiness):
- `RM-DEV-008`
- `RM-DEV-009`

Archive reconciliation evidence:
- `artifacts/governance/rm_bundle_6_archive_validation.json`
- `artifacts/governance/rm_bundle_6_closeout_validation.json`

## Archived items (existing)

- `RM-DEV-003`
- `RM-INTEL-001`
- `RM-INV-004`
- `RM-GOV-004`
- `RM-AUTO-002`
- `RM-DEV-006`
- `RM-INTEL-002`
- `RM-CORE-004`

## Authority model

- Layer 1 (authoritative): `docs/roadmap/items/RM-*.yaml`
- Layer 2 (derived planning): `governance/roadmap_dependency_graph.v1.yaml`, `artifacts/planning/next_pull.json`
- Layer 3 (derived summary): `docs/roadmap/ROADMAP_STATUS_SYNC.md`, `docs/roadmap/ROADMAP_MASTER.md`, `docs/roadmap/ROADMAP_INDEX.md`
