# RM-UI-005

- **ID:** `RM-UI-005`
- **Title:** Local execution control dashboard for AI run control, context management, validation status, and truthful completion gating
- **Category:** `UI`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M3`
- **Priority:** `Critical`
- **Priority class:** `P1`
- **Queue rank:** `1`
- **Target horizon:** `now`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `now`

## Description

Build a web-first local execution control dashboard that sits in front of Aider, Codex, Ollama, and other local execution surfaces and gives the operator and the system a single truthful run-control interface. The dashboard must expose live objective state, blocker chain, repo/branch context, file-context load, token/context pressure, validations, artifacts, bounded-scope completion status, and the next governed target so the coding assistant can be driven safely at high speed without false-complete behavior or terminal-only ambiguity.

This item is explicitly intended to close the usability and control gap exposed by raw terminal workflows where the assistant can appear “done” because a small patch landed, a few tests passed, or context overflow warnings were missed. It is not a cosmetic UI item. It is an operational control surface for the local execution system.

## Why it matters

This is now a critical item because the repo already has normalized roadmap governance, autonomous pull policy, and active coding-assistant work, but the operator experience and local run-control experience remain too dependent on raw terminal output and manual interpretation. That creates three immediate risks:

1. false completion claims
2. missed context-limit / token-limit failure modes
3. poor visibility into whether a run achieved substep completion, bounded-slice completion, item completion, or actual blocker-chain clearance

A dedicated control dashboard materially improves the probability that the local system can replace Claude Code and Codex as the routine execution layer because it turns the current terminal-heavy execution workflow into a governed operator system with visible truth, visible blockers, visible validations, and visible completion semantics.

## Why this should be the next item implemented

This item should be treated as the next implementation target because it directly improves all of the following already-active strategic concerns:

- developer-assistant operability
- governed autonomous execution
- validation/evidence visibility
- completion-contract correctness
- blocker-awareness
- token/context management
- truthful promotion and closeout behavior

It also leverages work that is already present:

- roadmap normalization and active-item governance
- autonomous execution operating mode
- target-selection policy
- blocker and status surfaces
- telemetry/evidence direction from RM-OPS-005
- completion and operational-truth expectations from RM-OPS-004

This means it has unusually high leverage relative to effort. It does not require waiting for broad branch expansion. It helps the local system perform better immediately.

## Key requirements

### Core run-control requirements
- show current objective / lane / bounded closure scope
- show current blocker chain
- show current repo, branch, and working tree context
- show current model/provider/runtime in use
- show current token/context estimate and hard model limits
- show context-overflow risk before a run is submitted
- show files currently in model context
- show files changed in the current run
- show validations run and pass/fail state
- show emitted artifacts and their paths
- show completion-state ladder:
  - substep complete
  - bounded slice complete
  - item complete
  - blocker chain cleared
  - objective achieved
- show next best governed target from the roadmap queue
- show why the next target is eligible or blocked

### Governance integration requirements
- read roadmap truth from canonical repo surfaces rather than from chat memory
- read autonomous-eligibility and bounded-scope status from normalized item files or derived artifacts
- display blocked placeholders as ineligible work
- surface missing docs / missing validation / missing artifact requirements as blockers
- preserve the architecture rule that local autonomy may only operate through the canonical governance and roadmap system

### Context-management requirements
- highlight token/context pressure before execution
- identify largest files contributing to context load
- recommend context trimming candidates without requiring the operator to infer them manually
- distinguish between safe-to-drop context and must-retain context
- support per-run context snapshots so completion and failure can be analyzed after the run

### Validation and completion requirements
- show required validations for the current slice
- show required artifacts for the current slice
- show missing evidence preventing closure
- prevent the UI from presenting a task as complete if only a patch landed or a partial validation passed
- expose completion contract results clearly and separately from code-diff results

### Operator and local-system requirements
- web-first local dashboard
- can be used by a human operator immediately
- can later be consumed by an autonomous local agent as a truth surface
- should support multiple execution backends while preserving the local-first architecture
- should not become a second planning authority; it is a control surface over canonical repo truth

## Examples of what the dashboard must make visible

### Example 1 — context overflow prevention
Current terminal-only workflow:
- operator adds too many files to Aider
- model context exceeds limit
- warning appears late in terminal output
- operator either misses it or proceeds with degraded execution

Required dashboard behavior:
- show current estimated context load vs hard model limit before send
- display the top contributors to context usage
- display recommended files to drop
- display whether the run is still safe to proceed

### Example 2 — false completion prevention
Current failure mode:
- model edits one file
- one test passes
- assistant says “complete”
- roadmap item and blocker chain are not actually closed

Required dashboard behavior:
- separate patch success from bounded-slice completion
- show unmet validation requirements
- show unmet artifact requirements
- show unmet truth-surface update requirements
- show item status as not complete until completion contract is satisfied

### Example 3 — governed next-task pull
Current failure mode:
- operator must manually infer what to do next from scattered files and terminal logs

Required dashboard behavior:
- display next best governed target
- display score / reason for ranking
- display why competing items were not selected
- display whether the selected item is blocked, eligible_with_guardrails, or eligible

### Example 4 — closeout truth
Current failure mode:
- a run appears successful, but evidence or truth surfaces were not updated

Required dashboard behavior:
- show whether required artifacts were emitted
- show whether truth surfaces were updated
- show whether blocker chain is actually cleared
- do not allow the run to be represented as fully closed if those conditions are not met

## Affected systems

- UI/control surfaces
- developer assistant runtime/operator experience
- roadmap governance and active-item interpretation layer
- validation and artifact surfaces
- blocker registry / next-pull queue / derived planning surfaces
- telemetry/evidence display surfaces
- future autonomous local execution control loop

## Expected file families

- `docs/roadmap/*`
- `docs/architecture/*` where control-surface linkage needs documenting
- future local dashboard frontend files
- future local dashboard backend/orchestration files
- future run-state store or event stream files
- future integration adapters for Aider, Codex, Ollama, and validation tools
- future widget/panel/state model docs and tests

## Dependencies

- `RM-GOV-001` — integrated roadmap-to-development tracking system with CMDB linkage, standardized metrics, enforced naming, and impact transparency
- `RM-OPS-004` — backup, restore, disaster-recovery, and configuration export verification
- `RM-OPS-005` — end-to-end telemetry, tracing, and audit evidence pipeline
- `RM-AUTO-001` — plain-English goal-to-agent system
- `RM-UI-001` — master control center for the system with web-first UI, tablet support, and later app-based surfaces
- `RM-GOV-009` — external application connectivity and integration control plane

## Risks and issues

### Key risks
- building only a pretty dashboard without real governance/state linkage
- letting the dashboard become a second planning authority instead of a control surface over canonical truth
- overbuilding the first slice instead of shipping the minimum high-value operator interface
- weak event/state modeling causing the UI to display stale or misleading run status

### Known issues / blockers
- exact first slice must remain bounded so this can land in one aggressive pass
- must not drift into broad control-center scope that belongs to RM-UI-001 overall
- must respect the existing roadmap/autonomy truth surfaces rather than inventing a parallel queue

## CMDB / asset linkage

- should later expose host/runtime/device visibility for execution environments
- should remain linkable to systems, services, hosts, and tools represented in inventory/CMDB-related surfaces
- should eventually expose execution-environment capability state relevant to local run routing

## External dependency documentation pack

Complete this section whenever the roadmap item depends on an external product, service, API, protocol, OSS application, or major third-party integration.

- **Official docs home:** local-first implementation preferred; if OSS UI framework is adopted, record it here during implementation
- **Primary repo or vendor page:** TBD during implementation selection
- **API reference:** TBD during implementation selection
- **Auth / OAuth / permission docs:** local auth/session posture should remain bounded and explicitly documented
- **Installation / deployment docs:** should support local self-hosted deployment first
- **Configuration docs:** must capture runtime/backend configuration and per-model limit visibility
- **Webhook / event docs:** if event streaming is used, capture the boundary during implementation
- **Rate limits / quotas:** must capture model token/context ceilings and execution backend limits, even if local
- **Version / compatibility notes:** must explicitly capture model/backend compatibility matrix if more than one execution provider is supported
- **Known caveats / integration constraints:** avoid dependence on any non-local backend for normal operation
- **Adoption note:** `adopt-now`

## Grouping candidates

- `RM-UI-001`
- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-AUTO-001`
- `RM-GOV-009`

## Grouped execution notes

- Shared-touch rationale: this item intersects directly with the active strategic cluster and the active governance cluster. It consumes status truth, blocker truth, validation truth, and autonomous targeting truth, and presents them through a single operator surface.
- Repeated-touch reduction estimate: very high if done now, because it prevents repeated terminal-only diagnosis and repeated rework caused by hidden completion/validation/context failures.
- Grouping recommendation: `Bundle now` with adjacent execution-governance hardening surfaces, but keep the implementation slice bounded to the execution control dashboard itself.

## Recommended first milestone

Deliver a minimum viable local execution control dashboard that:

1. reads canonical roadmap truth and next-pull truth
2. displays current objective, current blocker chain, and eligible next target
3. displays file-context load, model limit, and overflow risk before execution
4. displays validations, artifacts, and completion-contract state for the current run
5. distinguishes patch success from bounded-slice completion and item completion
6. can be used immediately by a human operator while remaining machine-consumable later

## One-pass implementation package guidance

The first implementation pass should be bounded to a single useful slice. At minimum it should include:

### Required outputs
- local web UI shell for execution control
- run-status panel
- context/token pressure panel
- validation/artifact/completion panel
- next-target / blocker panel
- integration with current repo truth files and derived planning artifacts
- tests for core state parsing and panel behavior

### Suggested initial panel set
- Objective / lane / branch card
- Blocker chain card
- Next governed target card
- Context load and token pressure card
- Files in context / files changed card
- Validation results card
- Artifact outputs card
- Completion ladder card

### Minimum data sources the first slice should parse
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md`
- `docs/roadmap/AUTONOMOUS_EXECUTION_OPERATING_MODE.md`
- `docs/roadmap/TARGET_SELECTION_POLICY.md`
- derived queue / blocker artifacts if present
- current execution logs or run receipts if present

## Resources and implementation references

Use the repo’s own architecture and roadmap governance first. Then use these categories of implementation references while keeping the local-first architecture intact:

### Internal repo references
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`
- `docs/roadmap/ACTIVE_ITEM_NORMALIZATION_AUDIT.md`
- `docs/roadmap/AUTONOMOUS_EXECUTION_OPERATING_MODE.md`
- `docs/roadmap/TARGET_SELECTION_POLICY.md`
- `docs/roadmap/ITEMS/RM-GOV-001.md`
- `docs/roadmap/ITEMS/RM-OPS-004.md`
- `docs/roadmap/ITEMS/RM-OPS-005.md`
- `docs/roadmap/ITEMS/RM-AUTO-001.md`
- `docs/roadmap/ITEMS/RM-GOV-009.md`
- local evidence/run artifacts already present in the repo

### Implementation pattern references
- existing local control-center / dashboard patterns already intended under RM-UI-001
- existing next-pull / blocker / validation artifacts already generated in the repo
- existing local evidence-bundle and live-proof-chain outputs already produced by the runtime/evidence work

### UX guidance for the first slice
- prioritize truth visibility over visual polish
- use explicit red/yellow/green status semantics only when backed by real repo truth
- prevent hidden state; every “good” status should link back to a file/artifact or validation result
- separate informational panels from gating panels so the operator can see what blocks closure

## Status transition notes

- Expected next status: `Planned`
- Transition condition: implementation boundary, first slice, and required repo truth sources are explicitly accepted
- Validation / closeout condition: a working local execution control dashboard slice exists, reads canonical repo truth, and materially reduces false-complete / missed-context / hidden-blocker failures in real local runs

## Notes

This item is intentionally critical and next-to-implement. It is not merely a dashboard improvement. It is the missing operator/control surface that turns the current local coding workflow from terminal-heavy and ambiguity-prone into a governed local execution system.