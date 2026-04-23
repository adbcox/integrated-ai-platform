# Document State Index

## Purpose

This document classifies major repository documents so humans and coding assistants can quickly determine:
- whether a document is canonical, derived, operating, execution, historical, or archived
- whether the document should be read first, later, or only for history
- what other document supersedes or depends on it

Use this file to reduce search cost, prevent split authority, and guide retention/archival decisions.

## State model

### Canonical
Direct source of truth for state or architecture.

### Derived
Generated or synchronized from canonical truth.
Must not override canonical sources.

### Operating
Current posture, process, routing, or governance instructions.

### Execution
Prompting, implementer-mode, or work-packet guidance.

### Historical
Preserved for audit/history/transition understanding.
Not the default current-state planning source.

### Archive
Retained only for history/compliance/reference.
Should not be read by default.

## Index

| Path | Type | Authority level | Current state | Audience | Read when | Superseded by / notes |
|---|---|---:|---|---|---|---|
| `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md` | Canonical/Operating | 1 | active | human + machine | first when system identity or mission is in question | explicit mission and scope statement |
| `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` | Canonical | 1 | active | human + machine | always for architecture truth | core architecture anchor |
| `docs/roadmap/ROADMAP_AUTHORITY.md` | Canonical/Operating | 1 | active | human + machine | always for roadmap truth model | defines authority layers |
| `docs/roadmap/items/RM-*.yaml` | Canonical | 1 | active | human + machine | always for item truth | canonical item-state layer |
| `artifacts/planning/next_pull.json` | Derived | 2 | active | machine + human | when queue/selection matters | regenerate from canonical truth |
| `artifacts/planning/blocker_registry.json` | Derived | 2 | active | machine + human | when blocker state matters | regenerate from canonical truth |
| `governance/roadmap_dependency_graph.v1.yaml` | Derived | 2 | active | machine + human | when dependency state matters | regenerate from canonical truth |
| `docs/roadmap/data/roadmap_registry.yaml` | Derived | 2 | active | machine + human | when projections matter | mirrored from canonical truth |
| `docs/roadmap/data/sync_state.yaml` | Derived | 2 | active | machine + human | when projections matter | mirrored from canonical truth |
| `docs/roadmap/ROADMAP_STATUS_SYNC.md` | Derived/Summary | 3 | active | human | for synced visible status rollup | must not override item YAML |
| `docs/roadmap/ROADMAP_MASTER.md` | Summary | 3 | active | human | for strategic interpretation | must not override item YAML |
| `docs/roadmap/ROADMAP_INDEX.md` | Summary/Inventory | 3 | active | human | for backlog inventory | must not override item YAML |
| `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md` | Operating | 2 | active | human + machine | to understand current repo posture | current default operating-mode doc |
| `docs/governance/CURRENT_OPERATING_CONTEXT.md` | Operating | 2 | active | human + machine | first short start-here brief | concise current-state entry point |
| `docs/governance/HARDWARE_CAPABILITY_AND_CONSTRAINTS.md` | Operating/Reference | 2 | active | human + machine | when work depends on hardware capacity, limits, firmware, or host roles | hardware source of truth for capability and constraints |
| `docs/governance/hardware_inventory_registry.yaml` | Derived/Operating | 2 | active | machine + human | when machine-readable hardware state is needed | registry companion to hardware capability doc |
| `docs/governance/HARDWARE_CAPTURE_AND_VALIDATION_RUNBOOK.md` | Operating | 2 | active | human + machine | when updating or validating hardware facts | hardware capture and maintenance process |
| `docs/execution_modes/EXECUTION_ROUTER.md` | Operating/Execution | 2 | active | human + machine | when choosing tool/mode | maps task types to implementers |
| `docs/execution_modes/CODEX_CONTROL_MODE.md` | Execution | 2 | active | human + machine | when using Codex for review/control | tool-specific mode doc |
| `docs/execution_modes/CODEX_EXEC_MODE.md` | Execution | 2 | active | human + machine | when using Codex for implementation | tool-specific mode doc |
| `docs/execution_modes/CLAUDE_CODE_EXEC_MODE.md` | Execution | 2 | active | human + machine | when using Claude Code for implementation | tool-specific mode doc |
| `docs/execution_modes/LOCAL_AIDER_EXEC_MODE.md` | Execution | 2 | active | human + machine | when using local Aider | tool-specific mode doc |
| `docs/execution_modes/LOCAL_CONTROL_WINDOW_MODE.md` | Execution | 2 | active | human + machine | when doing local audits/truth checks | tool-specific mode doc |
| `docs/governance/PROMPT_PACKET_STANDARD.md` | Operating/Execution | 2 | active | human + machine | when drafting prompts | standard packet contract |
| `docs/governance/DOCUMENT_RETENTION_POLICY.md` | Operating | 2 | active | human + machine | when archiving/retiring docs | retention/archival rules |
| `docs/roadmap/LOCAL_AUTONOMY_CRITICAL_PATH.md` | Historical | 4 | historical | human + machine | only to understand transition history | superseded by post-convergence mode |
| `docs/roadmap/EXECUTION_PACK_INDEX.md` | Execution support | 4 | active where relevant | human + machine | only when execution-pack detail is needed | not status authority |
| `docs/roadmap/*_EXECUTION_PACK.md` | Execution support | 4 | mixed | human + machine | only when working that item or auditing history | not status authority |
| `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` | Operating/Reference | 3 | active | human + machine | when working integrations/connectors | reference surface |

## Use rules

1. Read canonical before derived.
2. Read derived before summary when machine state matters.
3. Read operating docs before execution docs when selecting a mode.
4. Do not use historical docs as current-state authority.
5. If a document is superseded, mark it historical or archive it.

## Retention note

This index should be updated whenever:
- a new canonical or operating doc is created
- a historical transition doc is demoted
- a redundant doc is archived or retired
- an execution-mode doc is added or removed
