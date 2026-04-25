# RM-REFACTOR-015

- **ID:** `RM-REFACTOR-015`
- **Title:** Convert MILESTONE_COUNTS from set to sorted tuple
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

Replace `MILESTONE_COUNTS = {25, 50, 100, 150, 200}` with sorted tuple in voice_notifier and slack_notifier.

## Deliverable

bin/voice_notifier.py + framework/slack_notifier.py — deterministic iteration order

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
