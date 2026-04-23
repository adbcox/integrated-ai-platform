# Current Operating Context

## Purpose

This document is the **single start-here operating brief** for coding assistants, control windows, and operators working in this repository.

Use it to determine:
- what the repo currently is
- where canonical truth lives
- what execution posture is currently active
- which tool/mode should be used
- what acceptance rules apply

This document is intentionally short.
It is not a replacement for canonical item truth.

## Current repo posture

The repository is operating as a **governed local-execution platform in post-convergence mode**.

Interpretation:
- the local-autonomy substrate is treated as materially closed unless canonical repo truth shows regression
- future work should extend the governed platform rather than re-litigate its foundation by default
- bounded execution, artifact evidence, validation, and truth-surface sync remain mandatory

## Canonical truth order

Read in this order:

1. `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. canonical item YAML under `docs/roadmap/items/`
4. derived planning/dependency/data surfaces
5. `docs/roadmap/ROADMAP_STATUS_SYNC.md`
6. `docs/roadmap/ROADMAP_MASTER.md`
7. `docs/roadmap/ROADMAP_INDEX.md`
8. `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`
9. `docs/governance/DOCUMENT_STATE_INDEX.md`
10. execution-mode docs under `docs/execution_modes/`

## Current execution posture

Default model:
- local-first execution
- framework-first decomposition for complex tasks
- Aider as tactical executor where applicable
- control-window truth checks for acceptance
- external coding systems only when the local path proves insufficient or tool/environment constraints require them

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
