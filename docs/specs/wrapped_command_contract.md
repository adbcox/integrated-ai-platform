# Wrapped Command Contract Specification

**Spec ID**: WRAPPED-COMMAND-CONTRACT-SPEC-1  
**Status**: active  
**Date**: 2026-04-21  
**Phase linkage**: Phase 1 (runtime_contract_foundation)  
**Authority sources**: ADR-0003 (workspace contract), governance/definition_of_done.v1.yaml, governance/execution_control_package.schema.json

---

## Purpose

This document specifies the wrapped command execution contract for all coding runs in the integrated AI platform. A **wrapped command** is any shell or subprocess invocation that passes through the approved wrapper boundary, producing a normalized `CommandResult` with captured output, exit code, duration, and side-effect metadata.

The machine-readable form is `governance/wrapped_command_contract.v1.yaml`. This document is the human-readable companion.

---

## The Raw-Shell Prohibition

> **Raw direct shell execution is not the canonical interface for runtime work.**

All session command execution must go through the approved wrapper boundary. Direct invocation of shell commands (e.g., `os.system()`, bare `subprocess.run()` outside an approved exception) bypasses timeout enforcement, exit-code normalization, side-effect capture, and artifact tracing.

This rule exists because uncontrolled shell execution makes session outputs unobservable: timeouts are not enforced, write violations are not detected, and result shapes are not normalized for governance telemetry.

---

## Command Boundary

Every command executed in a coding run must pass through one of the approved wrapper entrypoints:

| Entrypoint | Scope |
|------------|-------|
| `framework/wrapped_command_runner.py::run_command()` | Primary runtime wrapper (Phase 2+) |
| `bin/run_*.py` scripts using subprocess with explicit timeout | Current Phase 1 approved fallback |
| `subprocess.run()` in `tests/test_*_seam.py` | Seam test validation only |

The wrapper is responsible for:
1. Accepting a command category classification
2. Enforcing the per-category timeout
3. Capturing stdout, stderr, exit_code, duration_ms
4. Recording write-scope metadata
5. Returning a normalized `CommandResult`
6. Signaling `repo_write_violation` when unexpected source-mount writes appear

---

## Command Categories

Every command must be assigned one of six categories:

| Category | Purpose | Write Scope | Default Timeout |
|----------|---------|-------------|-----------------|
| `build` | Compilation, make targets | build_cache_only | 120s |
| `test` | pytest, test suites | scratch_only | 180s |
| `lint` | Static analysis, syntax checks | read_only | 60s |
| `diff` | git diff, file comparison | read_only | 30s |
| `inspect` | File reads, directory listing | read_only | 30s |
| `artifact_emit` | Runner scripts writing governance artifacts | artifact_root_only | 60s |

**Category matters** because it determines timeout enforcement and side-effect expectations. Miscategorizing a command (e.g., marking an artifact_emit as inspect) is a contract violation — the category must reflect the actual write behavior.

---

## Result Contract

Every wrapped command returns a `CommandResult` with these required fields:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `success` / `failure` / `timeout` / `error` |
| `stdout` | string | Captured standard output (truncated at 64KB) |
| `stderr` | string | Captured standard error (truncated at 16KB) |
| `exit_code` | integer | Raw process exit code (-1 on timeout/error) |
| `duration_ms` | integer | Wall-clock elapsed time in milliseconds |
| `category` | string | Category assigned at dispatch |
| `command` | string or list | Command as dispatched |
| `timeout_applied` | integer | Timeout enforced for this invocation |

`status` is derived from `exit_code` against the category's `exit_code_success` list:
- `exit_code` in success list → `status = "success"`
- `exit_code` not in success list → `status = "failure"`
- Process exceeded timeout → `status = "timeout"`, `exit_code = -1`
- Wrapper exception → `status = "error"`, `exit_code = -1`

Note: `diff` commands have `exit_code_success = [0, 1]`. Exit code 1 for diff means differences were found — this is not a failure.

---

## Timeout Policy

Timeouts are enforced per category and cannot be disabled:

| Category | Default Timeout |
|----------|----------------|
| build | 120s |
| test | 180s |
| lint | 60s |
| diff | 30s |
| inspect | 30s |
| artifact_emit | 60s |
| (default) | 120s |

An explicit `timeout_override` at dispatch time takes precedence over category defaults. On timeout:
- Process is terminated
- `status = "timeout"`, `exit_code = -1`
- `stderr` includes: `Command terminated by wrapper timeout enforcement`

If more than 3 timeouts occur in a session, flag as escalation candidate in `residual_notes`. No automatic retry on timeout.

---

## Side-Effect Metadata

Every command carries side-effect metadata describing its write footprint:

| Field | Description |
|-------|-------------|
| `files_touched` | Expected write paths (empty for read-only categories) |
| `write_scope` | Classification: `read_only` / `scratch_only` / `artifact_root_only` / `build_cache_only` / `source_mount_declared` |
| `artifact_outputs` | Declared artifact root paths written (artifact_emit only) |
| `repo_write_violation_signal` | `true` if unexpected source-mount writes detected post-execution |

The `repo_write_violation_signal` is set by comparing post-execution `git status` against the package's `allowed_files`. Any untracked or modified file not in `allowed_files` and not gitignored triggers the signal. This does not cause an automatic hard stop — it surfaces the violation to session governance.

---

## Exceptions

### Seam tests use `subprocess.run()` directly

`tests/test_*_seam.py` files may call `subprocess.run()` to test runner scripts. This is scratch-mount test work, not runtime command execution.

### Runner scripts implement the wrapper

`bin/run_*.py` scripts may use `subprocess.run()` because they *are* the wrapper boundary for their validation commands — they are not bypassing the wrapper, they are implementing it.

### `make check` and `make quick` direct calls

Validation-discipline calls to `make check` and `make quick` are approved direct subprocess calls at Phase 1. Full wrapper enforcement is deferred to Phase 2 runtime implementation.

### Interactive commands require escalation

Commands requiring interactive input (TTY, interactive I/O) cannot be wrapped by the standard timeout/capture contract. These must be declared as ESCALATION-required. The wrapper must not attempt to wrap interactive commands.

### Undeclared raw shell requires declaration

Any direct shell usage outside the approved exceptions above is non-canonical and must be declared in the package's `residual_notes` as a `wrapper_boundary_violation`. This does not block commit but it must be visible in session governance.

---

## Relationship to ADRs and Governance

| Contract element | Authority |
|-----------------|-----------|
| Wrapper boundary | ADR-0003 (workspace contract — source mount, scratch mount) |
| Side-effect metadata | workspace_contract.v1.yaml `path_scope_rules.repo_write_violation_signal` |
| Timeout enforcement | governance/definition_of_done.v1.yaml `acceptance_rules` |
| Result contract | ADR-0006 (artifact bundle — normalized output capture) |
| Exception handling | `execution_control_package.schema.json::escalation_rule` |

---

## Example

A typical Phase 1 session using runner scripts:

```python
# Approved: runner script IS the wrapper boundary
result = subprocess.run(
    [sys.executable, "bin/run_wrapped_command_contract_check.py"],
    capture_output=True, text=True, timeout=60,
)
# result.returncode, result.stdout, result.stderr are the normalized result shape

# Approved in seam tests: testing the runner
def test_runner_script_executes():
    result = subprocess.run([sys.executable, ...], capture_output=True, text=True)
    assert result.returncode == 0

# Non-canonical (flag in residual_notes if used outside approved exceptions):
# os.system("make check")
# subprocess.run("make check", shell=True)  # without timeout enforcement
```

The wrapped command contract enforces:
1. Every command has a declared category
2. Timeouts are always enforced
3. Result shape is always normalized
4. Side-effect metadata is always captured
5. Repo write violations are always signaled
