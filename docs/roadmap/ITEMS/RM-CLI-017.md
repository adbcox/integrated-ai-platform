# RM-CLI-017

- **ID:** `RM-CLI-017`
- **Title:** CLI tool: run security audit
- **Category:** `CLI`
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

bin/platform audit — run framework/security audit checks and print findings with severity.

## Deliverable

bin/platform_cli.py — audit subcommand calling security_audit.py (35 lines)

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
