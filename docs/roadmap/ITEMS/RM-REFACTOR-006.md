# RM-REFACTOR-006

- **ID:** `RM-REFACTOR-006`
- **Title:** Extract _parse_log() into framework/log_parser.py
- **Category:** `REFACTOR`
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

Move the 80-line _parse_log() function from server.py into a standalone importable module.

## Deliverable

framework/log_parser.py — parse_executor_log(path: Path) -> dict (extracted, tested)

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
