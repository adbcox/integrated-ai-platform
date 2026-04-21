# Inference Gateway Contract Specification

**Spec ID**: INFERENCE-GATEWAY-CONTRACT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0004 (inference gateway), governance/model_profiles.v1.yaml, governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the internal inference gateway contract for the integrated AI platform. The **inference gateway** is the single chokepoint through which all model inference calls must pass. No application logic — stage probes, manager scripts, framework modules — may call Ollama or any remote API directly.

The machine-readable form is `governance/inference_gateway_contract.v1.yaml`. This document is the human-readable companion.

---

## The Direct-Call Prohibition

> **Application logic must not call Ollama directly.**

This is the defining constraint of the inference gateway. Every inference call must go through the gateway API defined in this contract. Direct calls bypass:

- Telemetry recording (breaks autonomy scoring)
- Fallback handling (breaks the retry/escalation chain)
- Profile resolution (breaks the model routing authority surface)
- The Claude-not-routine enforcement (allows silent SUBSTRATE rescues)

Any import of `requests`, `httpx`, or Ollama client libraries outside `framework/inference_adapter.py` is a contract violation and a hard stop.

---

## Gateway API

### Request fields

Every inference request must supply:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | yes | Unique call identifier; used for telemetry correlation |
| `session_id` | string | yes | Parent session |
| `package_id` | string | yes | Package that originated this request |
| `profile_id` | string | yes | Named profile from `governance/model_profiles.v1.yaml` |
| `prompt` | string | yes | Full prompt text |
| `temperature_override` | float | no | Overrides profile default; must be within profile min/max |
| `max_tokens` | integer | no | Defaults to profile `context_window` limit |
| `stop_sequences` | list | no | Termination tokens |
| `stream` | boolean | no | Default false |

### Response fields

Every response contains:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `request_id` | string | yes | Echoed for correlation |
| `profile_id_resolved` | string | yes | Actual profile used (may differ if fallback triggered) |
| `backend_used` | string | yes | `ollama` or `remote_api` |
| `model_used` | string | yes | Exact model identifier |
| `completion` | string | yes | Generated text |
| `finish_reason` | string | yes | `stop`, `length`, `timeout`, or `error` |
| `fallback_triggered` | boolean | yes | True if fallback to alternate profile occurred |
| `fallback_reason` | string | no | Human-readable fallback cause; null if no fallback |
| `retry_count` | integer | yes | Retries before this response |
| `token_counts` | object | yes | `{prompt_tokens, completion_tokens, total_tokens}` |
| `latency_ms` | integer | yes | Wall-clock time to first token or completion |
| `error` | string | no | Error message if `finish_reason=error`; null otherwise |

---

## Profile Resolution

The gateway resolves `profile_id` from the request to a backend/model/parameters using `governance/model_profiles.v1.yaml` as the authority surface.

**Resolution steps**:

1. Look up `profile_id` in `model_profiles.v1.yaml::profiles`
2. If not found or `enabled=false`: hard stop, return error response
3. Extract `backend`, `model_name`, `context_window`, `timeout_seconds`
4. Apply `temperature_override` if within profile `min`/`max`; else use profile `default`
5. Dispatch to the resolved backend
6. On failure/timeout: check `profile.fallback_to`
7. If `fallback_to` is non-null: repeat from step 1 with fallback profile; set `fallback_triggered=true`
8. If `fallback_to` is null or `ESCALATE`: return escalation response

**The fallback chain never reaches SUBSTRATE (Claude).** See Exceptions below.

---

## Backend Routing

### Backends

| Backend | When used | Hard constraint |
|---------|-----------|-----------------|
| `ollama` | All LOCAL-FIRST profiles | Default; binding when `profile.backend=ollama` |
| `remote_api` | SUBSTRATE packages only | Must never be selected for LOCAL-FIRST packages |

### Ollama routing

The gateway uses `OLLAMA_API_BASE` (default: `http://localhost:11434`) for all standard Ollama profiles. The `long_context` profile uses `OLLAMA_API_BASE_32B` if set; otherwise falls back to `hard`.

Before dispatching, the gateway pings the Ollama health endpoint (`/api/tags`). An unavailable backend triggers the fallback chain without counting as a retry.

### Remote API routing

`remote_api` is only permitted when the package routing label is `SUBSTRATE`. Attempting to use `remote_api` in a LOCAL-FIRST package is a hard stop with `escalation_triggered=true`.

---

## Timeout and Retry Policy

### Timeouts

Timeouts are per-profile (see `model_profiles.v1.yaml`):

| Profile | Timeout |
|---------|---------|
| `fast` | 120s |
| `balanced` | 180s |
| `hard` | 300s |
| `long_context` | 600s |

A timeout is treated as a failure, not a retry. It immediately triggers the `fallback_to` chain.

### Retry budget

The gateway allows **at most one retry per profile** for transient errors (network blip, backend temporarily unavailable). Retries are not permitted for timeouts, context-length exceeded, or model-not-found errors.

### Failure class handling

| Failure class | Action |
|---------------|--------|
| Transient network error | Retry once; if retry fails, trigger `fallback_to` |
| Timeout | No retry; trigger `fallback_to` immediately |
| Context length exceeded | No retry; try `long_context` if available; else escalate |
| Model not found | Hard stop (configuration error); no fallback |
| All profiles exhausted | Return escalation response |

---

## Telemetry Contract

Every gateway call emits a telemetry record appended to the session artifact bundle. Required fields:

| Field | Description |
|-------|-------------|
| `session_id` | Links record to parent session |
| `package_id` | Package that originated the call |
| `selected_profile` | The profile actually used (`profile_id_resolved`) |
| `selected_backend` | The backend actually used |
| `prompt_hash` | SHA-256 of prompt text (always emitted, even on error) |
| `response_hash` | SHA-256 of completion text |
| `token_counts` | `{prompt_tokens, completion_tokens, total_tokens}` |
| `latency_ms` | Wall-clock latency |
| `finish_reason` | `stop` / `length` / `timeout` / `error` |
| `retry_count` | Retries before final response |
| `fallback_triggered` | Whether fallback occurred |
| `escalation_triggered` | Whether the call ended in escalation |
| `error_class` | Failure class if applicable; null on success |

### Scoring derivation

Telemetry records are the canonical source for autonomy scorecard metric computation:

- `first_pass_success`: `retry_count=0 AND fallback_triggered=false AND escalation_triggered=false`
- `retry_count`: directly from `retry_count` field
- `escalation_rate`: derived from `escalation_triggered=true`

---

## Exceptions

### Claude is escalation-only

Claude (SUBSTRATE / `remote_api`) is not a routine inference backend profile. It must never appear in a fallback chain for LOCAL-FIRST packages. Any invocation of `remote_api` for a LOCAL-FIRST package is an escalation event:
- `escalation_triggered=true`
- `first_pass_success` not credited for that session

### Temperature override bounds enforced

An out-of-bounds `temperature_override` is rejected with a hard stop — it does not silently fall back to the profile default.

### Prompt hash required even on error

The telemetry record must always include `prompt_hash`, even if the request failed before reaching the backend.

### No ambient inference

Inference calls must only be made with a valid `session_id` and `package_id`. Speculative pre-generation or keepalive prompts are forbidden.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Gateway API shape | ADR-0004 (inference_request / inference_response) |
| Profile resolution | `governance/model_profiles.v1.yaml` |
| Fallback chain | ADR-0004 (`fallback_triggered` field) + DoD (`local_first_fallback`) |
| Telemetry | ADR-0001 (session schema `session_id` linkage) + ADR-0004 |
| Direct-call prohibition | ADR-0004 ("all inference calls route through gateway") |
| Autonomy scoring | `governance/autonomy_scorecard.v1.yaml::telemetry_contract.scoring_use` |
| Claude exception | DoD `escalation_handling.claude_rescue_not_local_autonomy` |

---

## Implementation Note

The runtime implementation of this contract lives in `framework/inference_adapter.py`. That file is the only place in the codebase permitted to make direct backend calls. All other modules must use the gateway API. The contract in this file takes precedence over the Python implementation; any divergence is a Phase 1 hardening defect.
