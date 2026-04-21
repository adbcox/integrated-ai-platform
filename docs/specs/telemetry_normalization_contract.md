# Telemetry Normalization Contract Specification

**Spec ID**: TELEMETRY-NORMALIZATION-CONTRACT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0004 (inference gateway), ADR-0007 (autonomy scorecard), governance/definition_of_done.v1.yaml

---

## Purpose

This document specifies the telemetry normalization contract for all coding runs in the integrated AI platform. A **telemetry record** is the normalized output capture for a single package execution. It is the governance record of what ran, on what model, with what result, at what latency, and whether any escalation or validation failure occurred.

The machine-readable form is `governance/telemetry_normalization_contract.v1.yaml`. This document is the human-readable companion.

---

## The Completeness Requirement

> **Every package execution that produces a governance artifact must emit a complete telemetry record.**

Incomplete telemetry is a DoD violation. Fields that cannot be measured must be reported as `null` with an explicit reason — omitting the field entirely is not permitted. One record per package execution.

---

## Required Fields

Every telemetry record must include these fields:

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `session_id` | string | No | Session executing the package |
| `package_id` | string | No | Package identifier |
| `package_label` | string | No | SUBSTRATE / LOCAL-FIRST / ESCALATION |
| `selected_profile` | string | Yes | Model profile used (null if no inference) |
| `selected_backend` | string | No | ollama / remote_api / substrate / none |
| `prompt_hash` | string | Yes | SHA-256 of primary prompt (null if no inference) |
| `response_hash` | string | Yes | SHA-256 of primary response (null if no inference) |
| `latency_ms` | integer | Yes | Inference latency in ms (null if no inference) |
| `retry_count` | integer | No | Inference retries (0 = no retries) |
| `escalation_status` | string | No | NOT_ESCALATED / ESCALATED / ESCALATION_CANDIDATE |
| `validations_run` | list | No | Ordered list of validation steps executed |
| `validation_results` | object | No | Step name → pass/fail/skip |
| `artifacts_produced` | list | No | Artifact root paths written |

`escalation_status` must always be present — `NOT_ESCALATED` is a valid and required value, not a default omission.

---

## Normalized Units

| Field | Unit | Notes |
|-------|------|-------|
| `latency_ms` | milliseconds (integer) | Wall-clock, not CPU time |
| `duration_ms` | milliseconds (integer) | Command execution duration |
| `retry_count` | count (integer ≥ 0) | |
| `token_counts` | tokens (object) | `prompt_tokens`, `completion_tokens`, `total_tokens` |
| `generated_at` | ISO 8601 with timezone | UTC preferred |

---

## Event Shapes

Telemetry events are emitted at key points:

| Event type | Key fields |
|-----------|------------|
| `package_start` | package_id, package_label, session_id, timestamp |
| `validation_gate` | package_id, gate_name, gate_result (pass/fail/skip), timestamp |
| `inference_call` | package_id, profile_id, backend, prompt_hash, response_hash, latency_ms, retry_count, finish_reason, timestamp |
| `artifact_emit` | package_id, artifact_id, artifact_path, timestamp |
| `package_end` | package_id, escalation_status, validations_run, validation_results, artifacts_produced, timestamp |

Note: Phase 1 packages are not required to emit structured event streams. The artifact fields constitute the Phase 1 telemetry record. Full event stream emission is deferred to Phase 2.

---

## Scoring Linkage

Telemetry records are the input surface for the autonomy scorecard (`governance/autonomy_scorecard.v1.yaml`):

| Scorecard metric | Derived from |
|-----------------|--------------|
| `first_pass_success` | All gates pass AND retry_count == 0 |
| `validation_pass_rate` | Fraction of pass gates across all packages |
| `escalation_rate` | Fraction of ESCALATED packages |
| `artifact_completeness` | artifacts_produced matches declared artifact_outputs |
| `retry_count` | Sum and distribution across packages |

### Claude rescue is not local autonomy

If a LOCAL-FIRST package uses `selected_backend = substrate` (Claude Code executed instead of a local model), that package **must** be recorded as `escalation_status = ESCALATED`. The package may still commit its outputs, but it does not count as local autonomy progress.

Authority: `governance/definition_of_done.v1.yaml::acceptance_rules.local_first.claude_rescue_not_local_autonomy`

---

## Exceptions

### SUBSTRATE packages have null inference fields

SUBSTRATE packages do not perform local model inference. `prompt_hash`, `response_hash`, `latency_ms`, and `selected_profile` may be null. They must still appear in the record with null value — not omitted.

### Seam tests are not telemetry emitters

Seam tests do not emit telemetry records. The package emits one record that includes seam test results in `validation_results`. Tests are a step within the package's telemetry — not separate emitters.

### ESCALATION packages may have partial telemetry

ESCALATION packages that terminate with a hard stop before inference may emit partial telemetry. Required fields not captured before the hard stop may be null with `null_reason = 'hard_stop_before_capture'`.

### Claude rescue counts as escalation for scoring

A LOCAL-FIRST package executed by Claude Code (not a local model) must record `escalation_status = ESCALATED`. This is a scoring rule, not a block on commitment.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Required fields | ADR-0004 (inference gateway — `telemetry_contract.fields`) |
| Scoring linkage | ADR-0007 (autonomy scorecard — `scored_dimensions`) |
| Escalation accounting | governance/definition_of_done.v1.yaml `escalation_handling` |
| Claude rescue rule | governance/definition_of_done.v1.yaml `acceptance_rules.local_first` |
