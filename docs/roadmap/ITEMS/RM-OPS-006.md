# RM-OPS-006

- **ID:** `RM-OPS-006`
- **Title:** Governed desktop computer-use and non-API automation layer for local operator tasks
- **Category:** `OPS`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `soon`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `4`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a governed desktop computer-use and non-API automation layer that allows the platform to perform bounded local operator tasks through GUI automation where direct APIs do not exist or are insufficient.

This item is intended to capture desktop/task automation inspired by the utility of advanced coding/desktop assistants, while keeping the capability subordinate to the platform’s local-first governance, completion contracts, blocker handling, and execution routing rules.

The goal is not to create uncontrolled “computer use.” The goal is to create a bounded automation layer for desktop-facing tasks that can be routed, monitored, validated, and reviewed using the same governance model as the rest of the system.

## Why it matters

A meaningful portion of high-value local work still happens in desktop applications, browser flows, installers, settings panels, and tools without clean APIs. If the platform can only automate API-friendly systems, it will leave substantial real-world operator work on the table.

This item matters because it:

- expands the practical utility of the local execution system
- allows controlled automation of non-API tasks
- supports future operator productivity and admin workflows
- reinforces the need for strict completion validation and visible state reporting

## Key requirements

### Desktop automation scope
- support bounded GUI automation for local desktop tasks
- support browser and application workflows where APIs are absent or insufficient
- support explicit task packets, not vague freeform computer use

### Governance requirements
- route computer-use tasks through the same task-detection and routing/control layers
- require explicit scope, completion checks, and validation rules where feasible
- capture artifacts/logs/screens or equivalent state evidence as needed
- prevent this layer from bypassing blocker, validation, and completion gates

### Safety requirements
- support visible step/state reporting
- support confirmation requirements for risky actions
- support bounded allowlists / forbidden actions where appropriate
- prevent silent destructive automation

### Operator UX
- integrate with the local execution control surface
- show task objective, current step, and outcome state
- show whether the automation path is deterministic, confirmed, or blocked

## Affected systems

- local execution routing layer
- control dashboard / operator UI
- validation / artifact surfaces
- future desktop/browser automation adapters

## Expected file families

- future desktop automation orchestration docs
- future browser/GUI adapter files
- future validation and step-record artifacts
- future operator confirmation/state model files

## Dependencies

- `RM-UI-005` — local execution control dashboard, task-detection routing layer, Aider workload orchestration system, and OpenHands execution interface
- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-OPS-005` — telemetry, tracing, and audit evidence pipeline

## Risks and issues

### Key risks
- overreaching into unconstrained computer-use behavior
- insufficient observability for GUI-driven failures
- fragile automation against changing UI states

### Known issues / blockers
- first automation class must remain tightly bounded
- should not be promoted as generally reliable until deterministic cases are proven

## CMDB / asset linkage

- should later link to host/device capability state and workstation environment metadata where useful

## External dependency documentation pack

- **Official docs home:** any adopted desktop/browser automation tooling chosen during implementation
- **Primary repo or vendor page:** to be recorded during adoption
- **API / integration docs:** to be recorded during adoption
- **Known caveats / integration constraints:** this layer must remain governed and subordinate to the same completion/blocker model as other execution surfaces
- **Adoption note:** `conditional-adopt`

## Grouping candidates

- `RM-UI-005`
- `RM-GOV-009`
- `RM-OPS-005`

## Grouped execution notes

- Shared-touch rationale: execution routing, validation evidence, and external integration posture overlap strongly.
- Repeated-touch reduction estimate: high.
- Grouping recommendation: `Bundle after RM-UI-005 execution-control substrate is stable`

## Recommended first milestone

Define and implement one bounded desktop/browser automation task class with visible step state, confirmation posture, and completion validation.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: one bounded automation task class and one safe execution path are explicitly defined
- Validation / closeout condition: one governed desktop automation slice works end to end with visible task state and bounded completion rules

## Notes

This item is the canonical roadmap home for controlled desktop/computer-use automation and should be treated as a governed execution capability, not an unconstrained autonomy item.