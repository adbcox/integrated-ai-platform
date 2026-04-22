# Local Autonomy Critical Path

## Purpose

This document defines the concrete **now / next / later** execution path for reaching the user’s stated priority:

> do not prioritize broad new development until the platform can perform development work locally and holistically under governed local execution.

This document is a strategic execution map. It does not replace canonical item files. The canonical authority for individual item state remains in the roadmap item files and roadmap status surfaces.

## Primary goal

Reach a state where the platform can perform the majority of in-scope development work locally with:

- local model execution as the default path
- governed routing and execution lanes
- truthful completion and blocker handling
- visible validation and evidence
- reusable connector/control-plane support
- minimal dependence on Claude Code / Codex for routine development work

## What counts as success

The critical path is successful when all of the following are true:

1. the local execution/control surface is the normal operator path for development work
2. the system can route bounded tasks into the correct lane automatically or near-automatically
3. task execution has reliable completion semantics and does not falsely mark partial work as done
4. telemetry/evidence and backup/recovery are strong enough to support operational trust
5. core connectors needed for development and assistant workflows are governed through one control plane
6. plain-English goal intake can safely produce governed local execution plans on top of the same substrate
7. external cloud coding systems are fallback tools, not the normal execution backbone

## Critical-path items

### Tier 1 — NOW

1. `RM-UI-005`
   - local execution control dashboard
   - task-detection and routing layer
   - Aider workload orchestration system
   - OpenHands execution interface
   - companion/overlay mode later on same governed surface

2. `RM-GOV-001`
   - roadmap-to-development governance operating system
   - canonical planning / execution / impact / naming / grouped-execution truth

3. `RM-OPS-005`
   - telemetry, tracing, and audit evidence pipeline
   - required for trusting local execution and proving what actually happened

4. `RM-OPS-004`
   - backup / restore / configuration export verification
   - required so local autonomy does not outrun recoverability

### Tier 2 — NEXT

5. `RM-GOV-009`
   - external application connectivity and integration control plane
   - especially GitHub, Google Calendar, and Gmail as first-class connector priorities

6. `RM-AUTO-001`
   - plain-English goal-to-agent system
   - only after governance/runtime/control/evidence substrate is trustworthy

7. `RM-DEV-001`
   - Apple/Xcode coding capability under the same governed local runtime
   - expands the local development window into a key coding environment without changing the backbone

### Tier 3 — LATER

8. `RM-OPS-006`
   - governed desktop computer-use and non-API automation

9. `RM-HOME-005`
   - local voice and ambient assistant layer

10. `RM-INTEL-003`
   - personalized real-news briefing

11. `RM-INV-003`
   - inventory-aware procurement and hardware upgrade-value decision support

12. `RM-OPS-007`
   - emulator / BlueStacks lab (conditional, later, non-priority)

## NOW

The immediate objective is to finish the local development substrate and make it the default development path.

### What to do now

- finish and harden `RM-UI-005` until it is a trustworthy daily operator surface
- keep `RM-GOV-001` aligned so roadmap truth, queue truth, blocker truth, and execution truth stay synchronized
- complete the minimum viable telemetry/evidence layer in `RM-OPS-005`
- complete the minimum viable recovery/configuration verification layer in `RM-OPS-004`

### Done-enough condition for NOW tier

- RM-UI-005 provides real runnable local control/routing for development work
- local task routing is reliable enough for bounded feature/bugfix/audit/control-window work
- completion semantics are truthful and regression-tested
- blocker and next-target surfaces are reliable
- validation and evidence are visible and usable
- backup/restore/config export verification exists for the critical local execution state

## NEXT

Once the NOW tier is stable, expand from local execution substrate to reusable assistant capability.

### What to do next

- implement `RM-GOV-009` connector posture for GitHub, Google Calendar, and Gmail first
- use those connectors as shared infrastructure, not branch-specific hacks
- implement `RM-AUTO-001` as governed goal-to-plan / goal-to-execution over the same substrate
- implement `RM-DEV-001` so Apple/Xcode work also runs through the same local governed execution model

### Done-enough condition for NEXT tier

- the system can take a bounded English goal and turn it into a governed local plan
- GitHub is available as a governed development connector
- Google Calendar/Gmail are available as governed connector surfaces for future assistants
- Apple-platform coding tasks no longer require a separate execution backbone

## LATER

After the local development window is truly credible, broaden into adjacent personal-assistant and higher-level capability branches.

### What to do later

- governed desktop computer-use (`RM-OPS-006`)
- voice/ambient assistant (`RM-HOME-005`)
- real-news intelligence (`RM-INTEL-003`)
- procurement intelligence (`RM-INV-003`)
- emulator lab (`RM-OPS-007`) only if still justified

## Local Model Runtime and Execution Policy

### Canonical local execution rule
Default local development must run through the local model stack first.

Normal order:
1. local heavy planning/framework tier
2. local Aider execution tier
3. local validation/control-window truth check
4. external escalation only if the local path proves insufficient

Do not jump directly to Claude Code or Codex for normal complex tasks.

### Tier definitions

#### Tier S — small local tier
Use for:
- one-file edits
- literal replacements
- small patch corrections
- narrow validation-driven repair

Not for:
- planning-heavy tasks
- broad refactors
- architecture decisions

#### Tier M — mid local tier
Use for:
- bounded bugfixes
- small multi-file work
- normal Aider execution
- packet-driven implementation
- structured refactors under explicit scope

This should be the default local execution tier.

#### Tier H — heavy local tier
Use for:
- framework/task decomposition
- control-window truth checks
- planning-heavy local work
- difficult debugging
- creation of bounded execution packets for Aider
- larger task layout before tactical execution

This tier should create the structure for complex tasks, then hand execution to Aider where possible.

### Framework-first rule for complex tasks
For complex tasks, the heavy local tier must first produce:
- objective
- bounded scope
- allowed files
- forbidden files
- likely affected systems
- validation order
- completion conditions
- blocker conditions

After that, Aider executes the bounded packet.

### Aider execution rule
Aider is the tactical execution engine, not the planner of record.

Aider should receive:
- a bounded task packet
- minimal necessary context
- explicit validations
- explicit stop conditions

### External escalation rule
Claude Code / Codex may be used only if:
- the heavy local tier cannot form a valid bounded execution packet, or
- repeated local execution attempts fail on the same blocker, or
- the task exceeds current local runtime capability in a proven way

Do not escalate because a task merely looks hard.

### Startup and readiness policy
The roadmap must record:
- canonical Ollama host/port
- canonical model names per tier
- startup command for Ollama
- startup/verification commands for each approved model
- Aider invocation pattern per tier
- readiness verification commands before execution begins

### Required recorded runbook fields
For each approved model tier, record:
- model name
- intended role
- task classes allowed
- minimum validation expectations
- startup command
- health check command
- default Aider or framework binding
- escalation threshold

## Anti-drift rule

Until the NOW tier is materially stable, do **not** let lower-priority feature work displace:

- `RM-UI-005`
- `RM-GOV-001`
- `RM-OPS-005`
- `RM-OPS-004`

These four items together are the operational gate to credible local development autonomy.

## Build-vs-integrate rule on the critical path

### Build now
- control surface
- routing/orchestration layer
- truthful completion/blocker/queue model
- governance/evidence/recovery substrate

### Integrate now
- GitHub
- Google Calendar
- Gmail
- OpenHands (governed execution surface)
- Aider (editing/execution engine)
- Ollama/local models

### Delay broad buildout until later
- broad personal-assistant branches
- general voice/ambient behavior beyond bounded first slices
- emulator/game-lab work

## Operating instruction to future planning/execution passes

When there is a conflict between:
- adding appealing new feature breadth, and
- completing the local-autonomy critical path,

prefer the critical path unless the new feature directly strengthens one of the critical-path items.

## Canonical item reminder

This document does not replace item files.
The authoritative details for each item remain in their canonical roadmap entries and status surfaces.
