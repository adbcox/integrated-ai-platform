# RM-DOCS-104

- **ID:** `RM-DOCS-104`
- **Title:** Troubleshooting runbook: executor won't start
- **Category:** `DOCS`
- **Type:** `Feature`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `1`
- **Target horizon:** `immediate`
- **LOE:** `S`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `immediate`

## Description

Step-by-step diagnosis for executor startup failures: pgrep check, log tail, Ollama ping, port conflicts.

## Deliverable

docs/runbooks/executor_startup.md — 10-step checklist with expected outputs

## Dependencies

- no external blocking dependencies

## Risks and issues

### Key risks
- none; low-complexity isolated task

### Known issues / blockers
- none; ready to start

## Status transition notes

- Expected next status: `In progress`
- Transition condition: file created and verified
- Validation / closeout condition: module importable or script runs without error

## Notes

Self-contained S-LOE task — suitable for autonomous executor without human input.
