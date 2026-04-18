# ADR 0018 — Phase 1 Local Runtime Hardening Closure

Status: accepted (PHASE-1-CLOSE-1)
Owner: governance/phase1_local_runtime_closure_evidence.json
Baseline commits:
- RECON-W1:          53ae4d4f177b176a7bffaa63988f63fa0efa622c
- RECON-W2A:         595dc8750ed671fb23d3cec0be434c76dad818f5
- RECON-W2C:         6b2446180a4d1e9194ef682aacd33fc12f1f4c46
- PHASE-1-CLOSE-1:   4ab27440264e16c5b0db8bb736f822d4fbc706c6

## Context

ADR 0004 and `governance/phase1_ratification_decision.json` already
record Phase 1 (`runtime_contract_foundation`) as `closed` with
contract version `rt-1.0.0+4d80fbeedd6c`. That closure ratified the
runtime-primitive surface (`worker_runtime.py`, `tool_system.py`,
`workspace.py`, `permission_engine.py`, `sandbox.py`) as the
machine-readable foundation.

The authoritative schedule further requires that the local route be
dependable enough to be the default coding engine before Phase 2
shared-runtime substrate work begins. At the ratification baseline
those local-runtime-hardening deliverables were not yet in-tree.

PHASE-1-CLOSE-1 (`4ab27440…`) added the bounded local runtime
hardening surfaces:

- `framework/inference_gateway.py` — single internal API for local
  model invocation.
- `framework/model_profiles.py` — three stable local coding profiles
  (`fast`, `balanced`, `hard`), Ollama default, one dormant vLLM
  placeholder.
- `framework/runtime_workspace_contract.py` — deterministic
  `source_root` / `scratch_root` / `artifact_root` contract with
  read-only source enforcement.
- `framework/runtime_artifact_service.py` — per-run bundle manifest
  writer.
- `framework/local_command_runner.py` — thin subprocess wrapper
  producing normalized command telemetry.
- `framework/runtime_telemetry_schema.py` — normalized
  `InferenceTelemetry`, `CommandTelemetry`, `ValidationRecord`,
  `RunBundleManifest` shapes.
- `framework/runtime_validation_pack.py` and
  `artifacts/phase1_local_runtime_validation_report.py` — end-to-end
  baseline validation pack.
- Six deterministic offline test modules covering every surface above
  plus the end-to-end validation pack (29 tests).

## Decision

1. Phase 1 local runtime hardening is formally closed against the
   authoritative schedule. The evidence record is
   `governance/phase1_local_runtime_closure_evidence.json`.

2. `governance/phase1_ratification_decision.json` remains the
   machine-readable Phase 1 governance decision artifact. ADR 0004
   remains its ratifying ADR. This ADR is additive: it records the
   local-runtime-hardening closure event and its evidence refs, not
   a replacement of Phase 1 governance authority.

3. The next implementation phase is Phase 2 — shared agent runtime
   substrate work — which now has a stable local runtime contract to
   build on. No Phase 2 implementation is authorized by this ADR.

4. `current_allowed_class` remains `ratification_only`. This packet
   did not consume a class transition. No tactical family is unlocked.
   LOB-W3 remains paused under ADR 0003.

## Consequences

- Callers may depend on the Phase 1 local runtime surfaces as a
  stable contract: profile-driven inference invocation, deterministic
  workspace/artifact layout, wrapped command execution, and normalized
  telemetry.
- `make phase1-runtime-test` and `make phase1-runtime-validate` are
  the authoritative closure-evidence gates for this slice.
- A later packet that wires a real Ollama subprocess executor into
  `InferenceGateway` does not require re-closing Phase 1; the gateway
  interface is the stable contract.

## Invariants explicitly preserved

- No `framework/` primitive edits (`worker_runtime.py`, `tool_system.py`,
  `workspace.py`, `permission_engine.py`, `sandbox.py`, `job_schema.py`,
  `session_schema.py` all byte-identical).
- No `bin/` edits.
- No governance generator source edits.
- No tactical family unlocked.
- LOB-W3 remains paused under ADR 0003.
- `current_allowed_class` = `ratification_only`.
- Canonical phases remain 0..6.
- All existing ADRs (0001..0017) byte-identical.

## Supersedes

None.
