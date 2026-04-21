# Model Profiles Specification

**Spec ID**: MODEL-PROFILES-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0004 (inference gateway), governance/cmdb_lite_registry.v1.yaml::model_profiles, governance/definition_of_done.v1.yaml (acceptance_rules.local_first)

---

## Purpose

This document specifies the typed model profiles used by the Ollama-first LOCAL-FIRST execution route. A **model profile** is a named, machine-readable specification that binds a model identifier to its backend, context window, timeout, temperature policy, and intended task class.

The machine-readable form is `governance/model_profiles.v1.yaml`. This document is the human-readable companion.

Model profiles govern how the inference gateway (ADR-0004) selects a model for LOCAL-FIRST coding runs. They are the authority surface for LOCAL-FIRST routing decisions — the Makefile targets (`aider-fast`, `aider-hard`, `aider-smart`) are derived from these profiles.

---

## Scope

Model profiles cover **LOCAL-FIRST** execution only. SUBSTRATE (Claude) and ESCALATION runs are not covered by this specification. See the exceptions section for the explicit rule that Claude is not a routine model profile.

---

## Required Profiles

### `fast`

**Model**: `qwen2.5-coder:14b`  
**Context window**: 32,768 tokens  
**Timeout**: 120 seconds  
**Makefile target**: `aider-fast`

The default profile for LOCAL-FIRST packages. Used for narrow, routine coding slices: guard clause additions, assertion additions, single-file replacements, and governance documentation. Low temperature (0.15 default) for deterministic, precise edits.

Use `fast` when the task:
- Touches ≤ 2 files
- Has a simple, well-defined task class (guard clause, assertion, replacement)
- Does not require cross-module reasoning

### `balanced`

**Model**: `qwen2.5-coder:14b`  
**Context window**: 32,768 tokens  
**Timeout**: 180 seconds  
**Makefile target**: `aider-fast`

Same model as `fast` but with a wider temperature band (0.20 default) and longer timeout for bounded multi-file modifications. Use when the task touches 2–5 files with coordinated changes but does not require a larger model.

Use `balanced` when the task:
- Touches 2–5 files
- Requires coordinated changes across files (e.g., add a method and update its callers)
- Does not require deep architectural reasoning

### `hard`

**Model**: `deepseek-coder-v2`  
**Context window**: 65,536 tokens  
**Timeout**: 300 seconds  
**Makefile target**: `aider-hard`

The fallback model for tasks where `fast` or `balanced` fail. Used for complex refactors, architectural changes within bounded scope, and multi-step semantic generation tasks.

Use `hard` when:
- `fast` or `balanced` returned non-semantic (deterministic fallback) results
- The task requires deeper architectural reasoning
- The task involves multi-step semantic generation across files

`hard` is the end of the fallback chain. If `hard` fails, the run must escalate — it must not silently route to SUBSTRATE.

### `long_context`

**Model**: `32b-model` (via `OLLAMA_API_BASE_32B`)  
**Context window**: 131,072 tokens  
**Timeout**: 600 seconds  
**Makefile target**: `aider-smart`

For tasks that require large context windows — whole-file rewrites, cross-module semantic analysis, or long document generation. Requires the `OLLAMA_API_BASE_32B` environment variable to be set. If the variable is absent, falls back to `hard`.

Use `long_context` when:
- The primary model's context window is insufficient for the file sizes involved
- The task requires reading an entire large file before generating changes
- Long document generation tasks exceed 32K tokens of context

---

## Profile Fields

Each profile must declare all of the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `profile_id` | string | Stable unique identifier (matches the profile key) |
| `backend` | string | Must be `ollama` for all LOCAL-FIRST profiles |
| `model_name` | string | Exact model identifier as registered in Ollama |
| `context_window` | integer | Maximum context window in tokens |
| `timeout_seconds` | integer | Maximum inference time before treating as failure |
| `temperature_policy` | object | `default`, `min`, `max`, `rationale` |
| `intended_task_class` | list | One or more task class strings |
| `enabled` | boolean | Whether this profile is available for routing |

---

## Routing Rules

### Selection order

1. Use the profile explicitly declared in the package's model profile reference (if any)
2. Default to `fast` for packages touching ≤ 2 files with simple task classes
3. Use `balanced` for packages touching 3–5 files with coordinated changes
4. Use `hard` when `fast`/`balanced` produce non-semantic results
5. Use `long_context` when the primary model's context window is insufficient

### Fallback chain

```
fast      → hard → ESCALATE
balanced  → hard → ESCALATE
hard      → ESCALATE (no further fallback)
long_context → hard → ESCALATE
```

The fallback chain always terminates at `ESCALATE`. There is no path from a LOCAL-FIRST profile to SUBSTRATE (Claude).

### File scope enforcement

No profile may be used for a task touching more than `max_file_scope` files (5 for all current profiles). A task that requires touching more than 5 files must either be split into sub-packages or request an ESCALATION label.

### Timeout policy

If a model does not respond within `timeout_seconds`, the attempt is a failure. Increment `retry_count`; attempt the `fallback_to` profile if available; escalate if the fallback also times out.

---

## Exceptions

### Claude is not a routine profile

SUBSTRATE (Claude) is not a model profile for LOCAL-FIRST routing. Any use of Claude in a LOCAL-FIRST package is an escalation event, not a valid profile selection. There is no `claude` profile in this authority surface, and none should be added without an explicit ESCALATION label and control-window approval.

**Scoring impact**: Counts as `escalation_rate +1`; does not credit `first_pass_success` for the LOCAL-FIRST session. See `governance/autonomy_scorecard.v1.yaml::exceptions::claude_escalation_not_counted_as_local_autonomy`.

### Disabled profile must not be used

A profile with `enabled=false` must not be selected for any LOCAL-FIRST run. Attempting to use a disabled profile is a hard stop.

### Fallback exhaustion requires escalation

When the fallback chain terminates at `ESCALATE`, the exec terminal must escalate to the control window. It must not route to SUBSTRATE, use an out-of-chain profile, or retry indefinitely.

### `long_context` requires `OLLAMA_API_BASE_32B`

If `OLLAMA_API_BASE_32B` is absent, `long_context` is treated as unavailable and `hard` is used as the fallback. If `hard` also fails, escalate.

---

## Package Class Gate

All LOCAL-FIRST routing is gated by `governance/next_package_class.json::current_allowed_class`. Under `ratification_only` (the current class), only `governance_session` and `measurement_session` types are permitted. LOCAL-FIRST capability sessions are blocked until the package class advances.

---

## Relationship to ADRs and Governance

| Profile element | Authority |
|-----------------|-----------|
| `backend = ollama` | ADR-0004 (inference gateway backend selection rules) |
| Fallback chain | ADR-0004 (fallback_triggered field) + DoD (local_first_fallback rule) |
| File scope | ADR-0003 (workspace contract — allowed_write_paths) |
| Claude exception | DoD escalation_handling.claude_rescue_not_local_autonomy |
| Scoring impact | autonomy_scorecard.v1.yaml::exceptions |
| Package class gate | governance/next_package_class.json (AS-CW-03) |

---

## Example

The `fast` profile is the entry point for the vast majority of LOCAL-FIRST packages. A typical guard clause addition runs:

```sh
make aider-fast AIDER_MICRO_MESSAGE="shell/file.sh::function_name add guard clause" \
                AIDER_MICRO_FILES="shell/file.sh"
```

This uses `qwen2.5-coder:14b` at temperature 0.15 with a 120-second timeout. If it fails, the fallback is `make aider-hard`.
