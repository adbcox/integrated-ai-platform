# RM-AUTO-001 — Execution Pack

## Title

**RM-AUTO-001 — Plain-English goal-to-agent system**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-DEV-003`, `RM-GOV-001`

## Objective

Allow the system to take plain-English goals and convert them into bounded, traceable agent workflows with explicit task decomposition, tools, validation, and artifacts.

## Why this matters

This is the bridge between a strong local development assistant and a more general operational agent system.

## Required outcome

- plain-English goal intake
- task decomposition into bounded work units
- explicit tool/workflow selection
- validation and artifact closure per unit
- traceable final outcome with escalation when needed

## Recommended posture

- preserve boundedness and traceability at every stage
- do not let plain-English convenience erase scope control
- keep agent plans linked back to roadmap IDs or operational classes where applicable

## Required artifacts

- goal intake record
- decomposition plan
- selected tool/workflow record
- per-step validation outputs
- completion/escalation summary

## Best practices

- decompose into small bounded units
- preserve explicit allowed tools and files where relevant
- keep escalation rules visible
- require artifact completeness for every agent-run unit

## Common failure modes

- vague goals turning into unbounded action
- hidden multi-step mutation with no artifacts
- no distinction between planning and execution authority
- agent workflows that bypass the runtime and roadmap rules

## Recommended first milestone

Build the goal intake and bounded decomposition layer first, before broader autonomous execution depth.
