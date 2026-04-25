# RM-REFACTOR-009

- **ID:** `RM-REFACTOR-009`
- **Title:** Rename confusing variable names in stage_rag4
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

Rename tgt→target_file, ent→entity_name, sc→score throughout stage_rag4_plan_probe.py.

## Deliverable

bin/stage_rag4_plan_probe.py — all single-letter loop vars replaced with descriptive names

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
