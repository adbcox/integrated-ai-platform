# RM-AUTO-001

- **ID:** `RM-AUTO-001`
- **Title:** Plain-English goal-to-agent system
- **Category:** `AUTO`
- **Type:** `Program`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `4`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `4`
- **Readiness:** `near`

## Description

Create a plain-English goal-to-agent system that allows the platform to accept user goals in natural language and convert them into governed agentic workflows using the shared runtime substrate, canonical planning controls, and explicit execution boundaries.

## Why it matters

This item is one of the clearest expressions of the platform’s intended usefulness: a user-facing system that turns goals into managed execution rather than requiring constant manual decomposition. It also acts as a forcing function for runtime maturity, orchestration clarity, and governance quality.

## Key requirements

- accept plain-English user goals
- translate goals into structured execution plans
- route work through governed agent/runtime surfaces rather than ad hoc automation
- preserve architecture rules around shared runtime, permissions, artifact generation, and evidence
- support future branch-level goal execution without allowing branch-specific backbone drift

## Affected systems

- control plane and orchestration layer
- shared runtime substrate
- roadmap/execution governance layer
- user-facing control surfaces
- future domain-branch orchestration flows

## Expected file families

- future orchestration/runtime files
- future goal parsing/planning logic
- future execution policy and workflow files
- future UI/control-surface files for goal intake

## Dependencies

- shared runtime substrate maturity
- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-OPS-004` — backup, restore, disaster-recovery, and configuration export verification
- `RM-OPS-005` — end-to-end telemetry, tracing, and audit evidence pipeline

## Risks and issues

### Key risks

- could overpromise broad autonomy before shared runtime and evidence systems are strong enough
- could drift into a parallel execution path outside architecture rules if not tightly governed

### Known issues / blockers

- depends on stronger runtime and evidence discipline than the platform has fully proven today
- requires careful decomposition so it does not become an unbounded umbrella concept

## CMDB / asset linkage

- future agent plans should remain linkable to systems, assets, tools, and services represented in inventory/CMDB surfaces

## Grouping candidates

- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`

## Grouped execution notes

- Shared-touch rationale: this item shares orchestration, runtime, governance, evidence, and active-control-surface concerns with the main active cluster.
- Repeated-touch reduction estimate: high if sequenced with runtime/evidence governance work rather than treated as an isolated product feature.
- Grouping recommendation: `Bundle after substrate exists`

## Recommended first milestone

Define a bounded goal-to-plan pipeline that converts a plain-English goal into a structured execution intent, validates it against architecture/governance rules, and emits a governed execution plan without attempting unconstrained autonomy.

## Status transition notes

- Expected next status: `Decomposing`
- Transition condition: runtime assumptions, planning boundary, and first bounded milestone are explicitly defined
- Validation / closeout condition: a governed goal-to-plan path exists and is demonstrated on top of the shared platform rules

## Notes

This item should be interpreted as an architecture-dependent program capability, not as permission to bolt ad hoc agent autonomy onto the platform.