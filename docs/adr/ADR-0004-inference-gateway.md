# ADR-0004: Inference Gateway

**Status**: accepted  
**Date**: 2026-04-21  
**Phase linkage**: Phase 0 (governance_source_of_truth_reconciliation), Phase 1 (runtime_contract_foundation), Phase 2 (capability_session)  
**Authority sources**: P0-01-AUTHORITY-SURFACE-INVENTORY-1, AS-V7-02, AS-11-HANDOFF-V7, governance/runtime_contract_version.json

---

## Context

The platform uses inference backends to generate semantic modifications, planning outputs, and governance assessments. Two backends currently exist:
- **Local Ollama** (primary for LOCAL-FIRST sessions): `qwen2.5-coder:14b`, `deepseek-coder-v2`, 32B variants
- **Remote API** (primary for SUBSTRATE sessions): Claude via Anthropic API

Prior to this ADR, backend selection was:
- Determined per-call in individual stage probes (`bin/stage_rag*`, `bin/stage*_manager.py`)
- Not governed by a unified contract
- Not recorded in governance artifacts

The V7 handoff (AS-V7-02) identifies inference backend selection as a Phase 1 hardening requirement. The `runtime_contract_version.json` must reference a stable inference gateway specification before Phase 1 can close.

---

## Decision

All inference calls in the platform route through a single **inference gateway** interface defined in `framework/inference_adapter.py`. The gateway contract is:

```
inference_request:
  request_id:         string
  backend:            enum      # local_ollama | remote_api | substrate
  model_id:           string    # specific model identifier
  prompt:             string    # full prompt text
  temperature:        float     # 0.0–1.0
  max_tokens:         int
  session_id:         string    # parent session
  package_class:      string    # current_allowed_class from next_package_class.json

inference_response:
  request_id:         string
  backend_used:       string    # actual backend (may differ if fallback triggered)
  model_used:         string    # actual model
  completion:         string
  tokens_used:        int
  latency_ms:         int
  fallback_triggered: bool
  fallback_reason:    string | null
```

**Backend selection rules**:
1. SUBSTRATE packages: use `remote_api` (Claude) by default
2. LOCAL-FIRST packages: use `local_ollama` by default
3. If primary backend unavailable: trigger fallback, set `fallback_triggered=true`
4. `ratification_only` package class: prohibit `write_unbounded` inference calls
5. All backends must return conformant `inference_response`

**Model routing** (LOCAL-FIRST):
- Fast/default: `qwen2.5-coder:14b` (aider-fast profile)
- Hard tasks: `deepseek-coder-v2` (aider-hard profile)
- Large context: 32B model via `OLLAMA_API_BASE_32B`

---

## Consequences

**Positive**:
- All inference calls are traceable through `request_id` linked to `session_id`
- Fallback behavior is explicit and auditable (not silent degradation)
- Package class gating prevents `ratification_only` sessions from triggering unrestricted inference

**Negative / constraints**:
- All stage probes must use the gateway interface; direct HTTP calls to Ollama/Claude are non-conformant after Phase 1 ratification
- Model ID must be specified explicitly; `auto` selection is not permitted in governance sessions
- The gateway adds latency overhead (~5ms per call for routing logic)

**Phase gate impact**:
- Phase 1 `runtime_contract_version.json` ratification requires that `framework/inference_adapter.py` implements the `inference_request`/`inference_response` contract defined here
- Phase 2 capability sessions must record `backend_used` and `fallback_triggered` in session artifacts
