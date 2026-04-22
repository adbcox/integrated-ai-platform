# RM-AUTO-001

- **ID:** `RM-AUTO-001`
- **Title:** Plain-English goal-to-agent system
- **Category:** `AUTO`
- **Type:** `Program`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `Critical`
- **Priority class:** `P1`
- **Queue rank:** `2`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `4`
- **Readiness:** `near`

## Description

Create a plain-English goal-to-agent system that allows the platform to accept user goals in natural language and convert them into governed agentic workflows using the shared runtime substrate, canonical planning controls, explicit execution boundaries, and the local execution-control system.

This item is part of the **local autonomy critical path**, but it is intentionally sequenced **after** the core local execution substrate is trustworthy.

## Why it matters

This item is one of the clearest expressions of the platform’s intended usefulness: a user-facing system that turns goals into managed execution rather than requiring constant manual decomposition. It also acts as a forcing function for runtime maturity, orchestration clarity, and governance quality.

However, this item must not be used to outrun the local substrate. It should sit on top of the local control/routing/governance/evidence stack, not compensate for its absence.

## Key requirements

- accept plain-English user goals
- translate goals into structured execution plans
- route work through governed agent/runtime surfaces rather than ad hoc automation
- preserve architecture rules around shared runtime, permissions, artifact generation, and evidence
- support future branch-level goal execution without allowing branch-specific backbone drift
- consume the same routing, completion, blocker, and connector surfaces as the local execution stack

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

- `RM-UI-005` — local execution control dashboard, task-detection routing layer, Aider workload orchestration system, and OpenHands execution interface
- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-OPS-004` — backup, restore, disaster-recovery, and configuration export verification
- `RM-OPS-005` — end-to-end telemetry, tracing, and audit evidence pipeline
- `RM-GOV-009` — external application connectivity and integration control plane

## Risks and issues

### Key risks

- could overpromise broad autonomy before shared runtime and evidence systems are strong enough
- could drift into a parallel execution path outside architecture rules if not tightly governed
- could become a prompt shell over weak substrate instead of a real governed autonomy layer

### Known issues / blockers

- depends on stronger runtime and evidence discipline than the platform has fully proven today
- requires careful decomposition so it does not become an unbounded umbrella concept
- should not be prioritized ahead of the NOW-tier local autonomy substrate items

## CMDB / asset linkage

- future agent plans should remain linkable to systems, assets, tools, and services represented in inventory/CMDB surfaces

## Grouping candidates

- `RM-UI-005`
- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-GOV-009`

## Grouped execution notes

- Shared-touch rationale: this item shares orchestration, runtime, governance, evidence, connectors, and active-control-surface concerns with the local autonomy critical path.
- Repeated-touch reduction estimate: high if sequenced after substrate maturity rather than treated as an isolated product feature.
- Grouping recommendation: `Bundle immediately after substrate exists`

## Recommended first milestone

Define a bounded goal-to-plan pipeline that converts a plain-English goal into a structured execution intent, validates it against architecture/governance rules, and emits a governed local execution plan without attempting unconstrained autonomy.

## Status transition notes

- Expected next status: `Decomposing`
- Transition condition: runtime assumptions, planning boundary, connector dependencies, and first bounded milestone are explicitly defined
- Validation / closeout condition: a governed goal-to-plan path exists and is demonstrated on top of the shared platform rules and local execution substrate

## Notes

This item should be interpreted as an architecture-dependent program capability, not as permission to bolt ad hoc agent autonomy onto the platform.