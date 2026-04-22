# Integrated AI Platform — Roadmap Master

This file is the **human-readable roadmap summary and strategic interpretation view** for the repository.

It is **not** the canonical status source.

## Architecture anchor

The roadmap is downstream of the master architecture.

Read `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` first when you need to understand:

- what the system is trying to become
- what the shared runtime architecture is
- what the non-negotiable platform rules are
- why the roadmap is sequenced the way it is

Then use the roadmap files to understand planning, status, execution sequence, and grouped delivery.

## Authority rule

Read planning and roadmap files in this order:

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
4. `docs/roadmap/ROADMAP_MASTER.md`
5. `docs/roadmap/ROADMAP_INDEX.md`
6. `docs/roadmap/STANDARDS.md`
7. `docs/roadmap/EXECUTION_PACK_INDEX.md`
8. `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

## What this file does

This file explains:
- strategic priorities
- active initiative grouping
- interpretation of the backlog
- what should be emphasized next

This file does **not** control item completion/archive truth.

## Primary objective

The most important program objective remains to strengthen the **local development assistant** so the system becomes a highly reliable home developer assistant with minimal dependence on Claude Code or Codex for routine coding work.

This is an architectural objective before it is a roadmap objective.

The roadmap should therefore continue to prioritize:

1. shared runtime completion
2. local Ollama-first coding reliability
3. artifact and validation completeness
4. developer assistant proof on the shared substrate
5. governance, evidence, and anti-drift hardening
6. controlled expansion into broader domain branches

## Immediate priority promotion

The critical next implementation target is now:

- `RM-UI-005` — Local execution control dashboard, task-detection routing layer, Aider workload orchestration system, and OpenHands execution interface

This item is promoted because it directly improves the operator and local-system ability to:

- see real blocker state
- avoid context-window overflow failures
- distinguish patch success from bounded-slice completion
- see validation/artifact gaps before falsely treating work as done
- drive the local coding assistant at higher speed with less terminal-only ambiguity
- support future companion/overlay interaction without creating a second assistant backbone

## Newly captured direction from recent feature evaluation

The roadmap now explicitly captures additional high-value directions that were previously only implicit or scattered:

- `RM-HOME-005` — local voice and ambient assistant layer for Alexa/Google Home replacement using Home Assistant as the device bridge
- `RM-INTEL-003` — personalized real-news briefing with interest-aware ranking, source-quality controls, and anti-clickbait summarization
- `RM-OPS-006` — governed desktop computer-use and non-API automation layer for local operator tasks
- `RM-OPS-007` — emulator and governed BlueStacks automation lab for bounded computer-use experiments (conditional/later)

It also strengthens these already-existing items:

- `RM-GOV-009` now explicitly carries GitHub, Google Calendar, and Gmail connector posture as first-class control-plane priorities
- `RM-INV-003` now explicitly carries hardware upgrade-value and cost/performance justification logic
- `RM-UI-005` now explicitly carries companion/overlay interaction mode in addition to the dashboard/routing/Aider/OpenHands scope

## Completed / archived correction note

Several items previously shown as active in summary surfaces are now treated as closed in the visible roadmap system and must not be read as active from this file.

Use `ROADMAP_STATUS_SYNC.md` for status truth.

## Current active strategic cluster

The highest-value **active** roadmap cluster for the home developer assistant is now:

- `RM-UI-005` — local execution control dashboard, task-detection routing layer, Aider workload orchestration system, and OpenHands execution interface
- `RM-AUTO-001` — Plain-English goal-to-agent system
- `RM-GOV-001` — Integrated roadmap-to-development tracking system with CMDB linkage, standardized metrics, enforced naming, and impact transparency
- `RM-OPS-005` — End-to-end telemetry, tracing, and audit evidence pipeline
- `RM-OPS-004` — Backup, restore, disaster-recovery, and configuration export verification
- `RM-INV-002` — Photo-driven inventory capture and capability mapping system for assets, components, consumables, and tools

## Active governance alignment cluster

The governance branch now also includes active architecture-alignment and operations-layer items that support the roadmap itself:

- `RM-GOV-006` — Hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap
- `RM-GOV-007` — Plane deployment, roadmap field mapping, and repo-to-Plane sync implementation
- `RM-GOV-008` — External application and integration registry with phased adoption and interface guidance
- `RM-GOV-009` — External application connectivity and integration control plane

These items are not the architectural backbone, but they are now part of the active governance layer required to keep roadmap execution aligned with the architecture source of truth.

## High-value adjacent branch additions

### Home / ambient assistant expansion
- `RM-HOME-005` extends the home branch toward local voice/ambient assistant behavior built on Home Assistant as the device bridge.

### Intelligence / briefing expansion
- `RM-INTEL-003` adds a source-quality-aware, non-clickbait personalized news briefing capability.

### Computer-use expansion
- `RM-OPS-006` creates the governed desktop computer-use layer.
- `RM-OPS-007` captures emulator/BlueStacks automation as a conditional later-stage lab rather than as a current priority.

### Procurement / upgrade intelligence expansion
- `RM-INV-003` now explicitly covers justified hardware upgrade evaluation and cost/performance decision support rather than only product lookup.

## Closed items removed from active interpretation

These items are no longer to be treated as active from this summary surface:

### Archived / completed
- `RM-AUTO-002`
- `RM-CORE-004`
- `RM-DEV-002`
- `RM-DEV-003`
- `RM-DEV-004`
- `RM-DEV-006`
- `RM-DEV-007`
- `RM-GOV-004`
- `RM-GOV-005`
- `RM-INTEL-001`
- `RM-INTEL-002`
- `RM-INV-004`
- `RM-INV-005`
- `RM-CORE-005`

### Completed / closed
- `RM-CORE-003`
- `RM-DEV-005`
- `RM-DEV-008`
- `RM-DEV-009`

## Active roadmap families

### Governance / roadmap integrity
- `RM-GOV-001`
- `RM-GOV-002`
- `RM-GOV-003`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-GOV-008`
- `RM-GOV-009`

### Developer assistant / local autonomy / execution
- `RM-DEV-001`
- `RM-AUTO-001`

### Core system / packaging / platform control
- `RM-CORE-001`
- `RM-CORE-002`
- `RM-OPS-001`
- `RM-OPS-002`
- `RM-OPS-003`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-OPS-006`
- `RM-OPS-007`
- `RM-UI-001`
- `RM-UI-002`
- `RM-UI-003`
- `RM-UI-004`
- `RM-UI-005`

### Inventory / procurement / asset understanding
- `RM-INV-001`
- `RM-INV-002`
- `RM-INV-003`

### Domain expansion packages
- `RM-DOCAPP-001`
- `RM-DOCAPP-002`
- `RM-HW-001`
- `RM-HW-002`
- `RM-LANG-001`
- `RM-HOME-001`
- `RM-HOME-002`
- `RM-HOME-003`
- `RM-HOME-004`
- `RM-HOME-005`
- `RM-MEDIA-001`
- `RM-MEDIA-002`
- `RM-MEDIA-003`
- `RM-MEDIA-004`
- `RM-MEDIA-005`
- `RM-INTEL-003`
- `RM-SHOP-001`
- `RM-SHOP-002`
- `RM-SHOP-003`
- `RM-SHOP-004`
- `RM-SHOP-005`
- `RM-AUTO-MECH-001`

## Durable storage rule

To prevent roadmap drift or split authority:

- Do not use this file as direct status truth.
- Update `ROADMAP_STATUS_SYNC.md` when item status changes on this branch.
- Keep this file aligned with the active/closed interpretation from the status sync.
- Use execution packs for detailed execution context, not for completion truth.
- Keep this file aligned with `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` when core platform direction changes.

## Reader rule

When in doubt:

1. use `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` for architecture truth
2. use `ROADMAP_STATUS_SYNC.md` for status truth
3. use this file for strategic interpretation
4. use `ROADMAP_INDEX.md` for backlog inventory
5. use execution packs for implementation depth
6. use `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` for external dependency and interface posture
