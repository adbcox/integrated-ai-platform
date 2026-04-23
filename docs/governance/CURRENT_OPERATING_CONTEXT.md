# Current Operating Context

## Purpose

This document is the **single start-here operating brief** for coding assistants, control windows, and operators working in this repository.

Use it to determine:
- what the repo currently is
- where canonical truth lives
- what execution posture is currently active
- which tool/mode should be used
- what acceptance rules apply
- where hardware capability and constraint truth lives
- where local AI stack and OSS reuse truth lives

This document is intentionally short.
It is not a replacement for canonical item truth.

## Current repo posture

The repository is operating as a **governed local-execution platform in post-convergence mode**.

Interpretation:
- the local-autonomy substrate is treated as materially closed unless canonical repo truth shows regression
- future work should extend the governed platform rather than re-litigate its foundation by default
- bounded execution, artifact evidence, validation, and truth-surface sync remain mandatory

## Mission posture

The system’s mission is broader than coding autonomy.

The platform should be understood as:
- a governed AI operating system and control plane
- for autonomous and semi-autonomous business, personal, operational, and development workflows
- with local coding autonomy as a **foundational enabling capability**, not the sole mission

Use these first when mission or identity is in question:
- `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md`
- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`

## Canonical truth order

Read in this order:

1. `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md`
2. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
3. `docs/roadmap/ROADMAP_AUTHORITY.md`
4. `docs/governance/DOCUMENT_STATE_INDEX.md`
5. canonical item YAML under `docs/roadmap/items/`
6. derived planning/dependency/data surfaces
7. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
8. `docs/roadmap/ROADMAP_MASTER.md`
9. `docs/roadmap/ROADMAP_INDEX.md`
10. `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
11. execution-mode docs under `docs/execution_modes/`

## Current execution posture

Default model:
- local-first execution
- framework-first decomposition for complex tasks
- Aider as tactical executor where applicable
- control-window truth checks for acceptance
- external coding systems only when the local path proves insufficient or tool/environment constraints require them

This execution posture exists to support the broader platform mission, not to redefine the platform as only a coding system.

## Local AI stack and OSS reuse posture

Before proposing new local AI tooling or rebuilding a capability, use these first:
- `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md`
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

Default rules:
- do not install multiple overlapping tools for the same role without explicit justification
- prefer mature OSS products, SDKs, CLIs, and modules before rebuilding a weaker in-repo first pass
- prefer thin adapters/wrappers over large forks

## Hardware truth posture

When work depends on hardware realities such as:
- GPU/VRAM fit
- local model hosting capacity
- Apple/Xcode host readiness
- firmware, BIOS, or driver state
- storage and backup posture
- remote operator continuity

use these first:
- `docs/governance/HARDWARE_CAPABILITY_AND_CONSTRAINTS.md`
- `docs/governance/hardware_inventory_registry.yaml`
- `docs/governance/HARDWARE_CAPTURE_AND_VALIDATION_RUNBOOK.md`

Do not silently assume hardware capacity when those sources are incomplete.

## Current acceptance rules

No roadmap closeout is accepted until the change is:
1. committed
2. pushed
3. remote-visible

Additional rules:
- patch success is not item completion
- summary docs do not override canonical item YAML
- derived planning surfaces must be regenerated, not narrated into agreement
- accepted passes should end in a clean reconciled branch state

## Current work-selection posture

Do not treat the autonomy substrate as the default active build queue.
Future work should generally be selected from:
- governed platform extensions
- ingress/connector/workflow expansion
- business and operational workflows
- domain expansions on top of the governed runtime
- governance-preservation and anti-drift work

## Current tool posture

### Local Aider
Default for:
- bounded code edits
- validator-driven repair
- tactical local execution
- smaller multi-file implementation work

### Codex control
Default for:
- truth audits
- completion validation
- contradiction detection
- repo-visible governance review

### Codex execution
Default for:
- bounded structured implementation
- repo-wide documentation or governance normalization
- explicit execution-package work

### Claude Code execution
Use when:
- Apple/Xcode/macOS-specific work requires it
- tool/environment access is stronger than the local path
- the local path cannot yet complete the task within current capability limits

## Current document-governance posture

Use:
- `docs/governance/DOCUMENT_STATE_INDEX.md` to identify document role and authority level
- `docs/execution_modes/EXECUTION_ROUTER.md` to choose the correct implementer/mode
- `docs/governance/PROMPT_PACKET_STANDARD.md` to structure prompts consistently
- `docs/governance/DOCUMENT_RETENTION_POLICY.md` to decide keep/archive/delete posture

## Notes

If any summary or operating doc conflicts with canonical item YAML, canonical item YAML wins.
If any closeout is only locally visible, it is not yet accepted closeout.
