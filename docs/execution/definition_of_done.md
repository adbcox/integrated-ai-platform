# Definition of Done — Local Coding Run

schema_version: 1
authority: docs/execution/definition_of_done.md

## 1. Artifact completeness

- `artifacts/baseline_validation/latest.json` must exist and be non-empty
- artifact must contain `all_passed`, `commands`, and `generated_at`
- each command entry must include `return_code`, `success`, `duration_ms`, `stdout_head`

## 2. Validation pass/fail semantics

- `make check` must exit 0
- `make quick` must exit 0
- `all_passed: true` means DoD is met
- any non-zero exit means DoD is not met

## 3. Rollback semantics

- any change that causes `all_passed: false` on baseline re-run must be reverted before merge/promotion
- baseline artifact commit hash is the regression reference point

## 4. Telemetry completeness

Each command execution must record:

- `command_name`
- `return_code`
- `duration_ms`
- `started_at`
- `completed_at`
- `stdout` first 2000 chars
- `stderr` first 500 chars

A `run_bundle_manifest.json` must be present at the artifact root for the run.

## 5. Escalation handling

- if `definition_of_done_met: false` in `latest.json`, the work item must not advance
- escalation is required when check or quick fails and the cause is not immediately correctable in the current session
