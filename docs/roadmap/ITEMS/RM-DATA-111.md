# RM-DATA-111

- **ID:** `RM-DATA-111`
- **Title:** Artifact cleanup script
- **Category:** `DATA`
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

Delete artifact directories older than 30 days from artifacts/stage_rag*, artifacts/stage*_manager.

## Deliverable

bin/cleanup_artifacts.py — cleanup_old_artifacts(older_than_days=30) (40 lines)

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
