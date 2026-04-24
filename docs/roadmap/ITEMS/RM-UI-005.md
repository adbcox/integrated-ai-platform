# RM-UI-005

- **ID:** `RM-UI-005`
- **Title:** Local execution control dashboard, task-detection routing layer, Aider workload orchestration system, and OpenHands execution interface
- **Category:** `UI`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `Critical`
- **Priority class:** `P1`
- **Queue rank:** `1`
- **Target horizon:** `now`
- **LOE:** `XL`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `now`

## Description

Build a web-first local execution control dashboard that sits in front of Aider, Codex, Ollama, OpenHands, and other local execution surfaces and gives the operator and the system a single truthful run-control interface.

This item explicitly includes four tightly connected capabilities and should be implemented as one coherent system:

1. **local execution control dashboard**
2. **task-detection and routing layer**
3. **Aider workload orchestration layer**
4. **OpenHands local GUI / CLI integration layer**

The system must expose live objective state, blocker chain, repo/branch context, file-context load, token/context pressure, validations, artifacts, bounded-scope completion status, next governed target, and lane-specific execution routing so the coding assistant can be driven safely at high speed without false-complete behavior, terminal-only ambiguity, or one-size-fits-all prompting.

This is not a cosmetic UI item. It is the operational control and workload-routing surface for the local execution system.

## Why it matters

This is now the most important next implementation item because the repo already has normalized roadmap governance, autonomous pull policy, and active coding-assistant work, but the operator experience and local run-control experience remain too dependent on raw terminal output and manual interpretation. That creates six immediate risks:

1. false completion claims
2. missed context-limit / token-limit failure modes
3. poor visibility into whether a run achieved substep completion, bounded-slice completion, item completion, or actual blocker-chain clearance
4. performance loss from running every coding task through one generic Aider workflow
5. unnecessary context bloat, wrong-file inclusion, and weak task-specific validation behavior
6. poor visibility into parallel or alternative local execution surfaces such as OpenHands

A dedicated control-and-routing system materially improves the probability that the local system can replace Claude Code and Codex as the routine execution layer because it turns the current terminal-heavy execution workflow into a governed operator system with visible truth, visible blockers, visible validations, visible completion semantics, and task-specific workload routing.

## Why this should be the next item implemented

This item should be treated as the next implementation target because it directly improves all of the following already-active strategic concerns:

- developer-assistant operability
- governed autonomous execution
- validation/evidence visibility
- completion-contract correctness
- blocker-awareness
- token/context management
- truthful promotion and closeout behavior
- Aider performance through task-specific context selection and routing
- local-system ability to auto-detect what kind of coding task is being requested
- optional immediate usability uplift through OpenHands CLI / Web GUI / GUI server paths
- future macOS companion / overlay interaction for contextual operator help
- explicit local model runtime selection and framework-to-Aider handoff discipline
- explicit local AI stack role visibility so assistants do not re-derive runtime/UI/RAG/workflow choices repeatedly
- explicit reuse of mature coding-agent and subsystem implementations instead of rebuilding weak first-pass versions

It also leverages work that is already present:

- roadmap normalization and active-item governance
- autonomous execution operating mode
- target-selection policy
- blocker and status surfaces
- telemetry/evidence direction from RM-OPS-005
- completion and operational-truth expectations from RM-OPS-004
- local run/evidence bundle outputs already present in the repo
- the local AI stack role matrix and external integration catalog
- the OSS reuse and reference-implementation registers

This means it has unusually high leverage relative to effort. It does not require waiting for broad branch expansion. It helps the local system perform better immediately.

## Aider enhancement merge rule

This item is the canonical home for the major Aider-adjacent enhancements discussed for the local coding system. Do not treat those as separate loosely related ideas unless later evidence justifies splitting them out.

The following concepts are now merged into RM-UI-005:

- task-specific coding interfaces over Aider
- automatic task detection and routing
- context-selection optimization for Aider runs
- model-limit / token-pressure visibility
- lane-specific validation policies
- lane-specific completion gates
- lane-specific allowed-file / forbidden-file behavior
- orchestration packets that convert high-level intent into bounded Aider runs
- a future macOS companion/overlay mode for contextual operator assistance
- explicit local model tier runbook and startup policy
- framework-first complex-task handling with Aider as bounded tactical executor
- explicit local AI stack role awareness across runtime, UI, RAG, workflow, and dev-agent surfaces

## OpenHands merge rule

This item is also the canonical near-term home for a practical local OpenHands implementation that supports the same local execution goal without becoming a second architecture.

OpenHands must be integrated as:
- a local CLI / Web GUI / GUI-server execution surface
- a complementary task-execution and monitoring interface
- a governed consumer of the same roadmap truth, blocker truth, validation truth, and completion truth
- an optional operator-facing execution surface, not a replacement planning authority

Do not let OpenHands create a parallel roadmap or parallel completion standard.

## Reference implementation and public-template rule

This item must not default to greenfield implementation when mature coding-agent and subsystem references already exist.

Before writing new code, assistants should check:
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/architecture/REFERENCE_IMPLEMENTATIONS_AND_PUBLIC_TEMPLATES.md`

### High-value references now relevant to this item
- **OpenHands** — bounded dev-agent execution surface and sandbox/UI model
- **OpenCode** — terminal-agent/TUI/session/tool integration reference
- **Plandex** — context trimming and change-set/rollback concepts
- **Aider** — editblock, diff, repo-map, commit, and auto-test logic
- **PR-Agent** — PR review automation surface
- **MCP reference servers** — official filesystem/fetch/git/memory/sequential-thinking tool examples
- **MarkItDown** — document conversion module where document ingest is needed for assistant context or RAG workflows
- **n8n** — visual workflow automation layer if workflow breadth grows beyond hand-authored packets

### Reuse posture
- install or wrap mature systems where they already solve the role well
- port or reuse focused modules where a subsystem is needed
- do not recreate a generic terminal agent, patch engine, PR reviewer, or workflow builder if a strong public implementation already exists and can be adapted with light modification
- keep all reused systems subordinate to canonical roadmap, validation, and completion truth

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

### Local AI stack role visibility now in scope
The control surface must make the preferred local AI stack legible.

At minimum it should show:
- active local runtime (`Ollama`, or an explicitly justified alternative such as `LM Studio` or `LocalAI`)
- active coding executor (`Aider` by default, `OpenHands` only when selected as bounded dev surface)
- active chat UI / operator surface (`Open WebUI` when relevant)
- active document/RAG workspace (`AnythingLLM` by default, `RAGFlow` only when specifically justified)
- active workflow/app layer (`Dify` only when selected)
- warnings when overlapping tools are being treated as simultaneous primaries for the same role
- references back to `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md` when the operator needs the authoritative stack-role decision

### Task-detection and routing requirements
- infer the likely task type from operator input and repo state
- support at minimum these routing classes:
  - `bugfix`
  - `bounded_feature`
  - `refactor`
  - `test_repair`
  - `repo_audit`
  - `control_window`
  - `blocker_closure`
- route work to the appropriate lane without requiring the user to manually construct a giant custom prompt each time
- prefer deterministic/rule-based routing first; model-assisted routing may be added later for ambiguous cases
- expose why a route was chosen
- expose why other routes were not chosen when useful

### Aider workload orchestration requirements
- use Aider as the primary editing/execution engine for coding assistance where appropriate
- generate task-specific run packets for Aider instead of one generic coding prompt
- each run packet must define at minimum:
  - selected lane
  - objective
  - bounded scope
  - allowed files
  - forbidden files
  - preload files
  - drop candidates
  - validations to run
  - completion criteria
  - truth surfaces to update
  - stop conditions
- support task-specific context minimization so Aider does not over-consume context on bounded tasks
- support task-specific repo-map / file-load behavior where feasible
- support lane-specific model/profile selection if the local system uses more than one model class
- prefer reuse of proven editblock/patch, auto-test, and repo-map logic before building weaker custom variants

### Local model runtime policy now in scope
- explicitly support local model tier selection and display it in the control surface
- treat local development as local-first by default
- define and expose three local execution tiers:
  - `Tier S` — small/tactical tier
  - `Tier M` — mid/default execution tier
  - `Tier H` — heavy/framework-planning tier
- support a framework-first rule for complex tasks where the heavy local tier lays out bounded execution packets before Aider tactical execution
- record and surface canonical startup/runbook fields for each approved local model tier:
  - model name
  - intended role
  - allowed task classes
  - startup command
  - health-check command
  - default binding into framework/Aider path
  - escalation threshold
- do not escalate to Claude Code or Codex by default for complex tasks if the local heavy tier can still produce a valid bounded execution packet

### Explicit model-tier runbook requirements
The item must define and surface a canonical local runbook for model startup and readiness.

#### Tier S — small/tactical tier
Use for:
- one-file edits
- literal replacements
- small patch corrections
- narrow validation-driven repair

Not for:
- planning-heavy tasks
- broad refactors
- architecture decisions

#### Tier M — mid/default execution tier
Use for:
- bounded bugfixes
- small multi-file work
- normal Aider execution
- packet-driven implementation
- structured refactors under explicit scope

This should be the default local execution tier.

#### Tier H — heavy/framework-planning tier
Use for:
- framework/task decomposition
- control-window truth checks
- planning-heavy local work
- difficult debugging
- creation of bounded execution packets for Aider
- larger task layout before tactical execution

This tier should create the structure for complex tasks, then hand execution to Aider where possible.

#### Canonical runbook fields to record per tier
For each approved local tier, the runbook must record:
- canonical model name
- intended role
- allowed task classes
- minimum validation expectations
- startup command
- health-check command
- default binding into framework-first vs Aider execution flow
- escalation threshold
- default context-length policy where relevant

#### Canonical startup and readiness policy
The roadmap item must require the local control system to record and surface:
- canonical Ollama host/port
- canonical model names per tier
- startup command for Ollama
- startup/verification commands for each approved model
- Aider invocation pattern per tier
- readiness verification commands before execution begins

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

### OpenHands integration requirements
- support a local OpenHands deployment path that can be executed soon
- support at minimum these OpenHands modes where useful:
  - CLI / terminal mode
  - browser-accessible web terminal mode
  - local GUI server mode
- support Docker sandbox as the preferred isolated mode
- allow controlled process/local execution mode only with explicit safety posture where needed
- support mounting the working repo into the OpenHands environment for bounded tasks
- allow OpenHands runs to consume the same repo truth and execution contracts as Aider-driven runs
- surface OpenHands run status, selected task, validation state, artifacts, and completion state back into the dashboard
- keep OpenHands subordinate to the same completion contract and blocker logic
- prefer reuse of existing OpenHands deployment/runtime patterns before inventing a weaker custom dev-agent shell

### Companion / overlay mode requirements now in scope
- support a future macOS companion or overlay interaction mode that can be summoned contextually
- support cursor-adjacent or screen-aware operator assistance where the interaction remains governed by the same routing and completion model
- do not let companion behavior bypass the main control/dashboard truth surfaces
- treat this as an alternate interaction mode over the same execution/control system, not a separate assistant

### Performance requirements
- reduce unnecessary file inclusion for bounded tasks
- reduce terminal-only context management burden
- highlight when a run should be narrowed before execution
- support identifying largest context contributors
- recommend which files to drop first
- distinguish must-retain context from safe-to-drop context
- make performance optimization an explicit design goal, not a byproduct
- reuse proven context slicing and trimming patterns before inventing brittle local heuristics

### Governance integration requirements
- read roadmap truth from canonical repo surfaces rather than from chat memory
- read autonomous-eligibility and bounded-scope status from normalized item files or derived artifacts
- display blocked placeholders as ineligible work
- surface missing docs / missing validation / missing artifact requirements as blockers
- preserve the architecture rule that local autonomy may only operate through the canonical governance and roadmap system
- preserve the local AI stack role matrix so overlapping tools are not adopted ad hoc

### Validation and completion requirements
- show required validations for the current slice
- show required artifacts for the current slice
- show missing evidence preventing closure
- prevent the UI or routing layer from presenting a task as complete if only a patch landed or a partial validation passed
- expose completion contract results clearly and separately from code-diff results
- lane-specific completion semantics must still obey the canonical execution/completion contracts

### Operator and local-system requirements
- web-first local dashboard
- can be used by a human operator immediately
- can later be consumed by an autonomous local agent as a truth surface
- should support multiple execution backends while preserving the local-first architecture
- should not become a second planning authority; it is a control surface over canonical repo truth

## Task-specific lane definitions that must be supported

### Lane 1 — bugfix
Use for:
- failing tests
- regressions
- tracebacks
- broken seams

Expected behavior:
- smallest relevant context
- strong failure-first validation
- stop only when failure is fixed or a true blocker is proven

### Lane 2 — bounded_feature
Use for:
- a single roadmap slice
- one bounded subsystem enhancement
- clearly scoped implementation work

Expected behavior:
- explicit allowed/forbidden file boundaries
- exact validation sequence
- explicit truth-surface update requirement

### Lane 3 — refactor
Use for:
- cleanup
- rename
- deduplication
- structure improvement without intended new behavior

Expected behavior:
- behavior preservation bias
- before/after validation
- no silent scope growth

### Lane 4 — test_repair
Use for:
- harness issues
- flaky validations
- local-vs-CI mismatches
- test breakage

Expected behavior:
- prefer test/harness fixes before product-code expansion
- clearly separate product bug from test bug when possible

### Lane 5 — repo_audit
Use for:
- drift scanning
- naming mismatch detection
- duplicate logic detection
- code/roadmap mismatch review

Expected behavior:
- read-heavy, write-light
- summary and blocker output prioritized

### Lane 6 — control_window
Use for:
- truth verification
- “is this actually complete?”
- blocker-chain review
- closure validation

Expected behavior:
- strict truthfulness
- no narrative-only closeout
- no over-crediting partial progress

### Lane 7 — blocker_closure
Use for:
- explicit gating issue removal
- local sovereignty blockers
- promotion/validation blockers
- active-cluster blocking defects

Expected behavior:
- bounded chain repair
- continue through adjacent blocker work if directly connected and safe

## OpenHands execution role examples

### Example 1 — local GUI monitoring surface
Use OpenHands GUI server as a richer local execution surface when the operator wants browser-based interaction and monitoring, but continue to show roadmap/blocker/completion truth in the main control layer.

### Example 2 — task handoff for bounded implementation
The routing layer may decide that a bounded feature slice should be executed in OpenHands rather than raw Aider if the task benefits from a longer interactive planning/execution loop, but only if the same run packet, validations, and completion contract are preserved.

### Example 3 — remote browser access to local terminal lane
Use OpenHands web mode when a browser-accessible terminal session is useful, while keeping the same governed task packet and truth reporting.

## Examples of what the system must make visible or decide

### Example 1 — context overflow prevention
Current terminal-only workflow:
- operator adds too many files to Aider
- model context exceeds limit
- warning appears late in terminal output
- operator either misses it or proceeds with degraded execution

Required system behavior:
- show current estimated context load vs hard model limit before send
- display the top contributors to context usage
- display recommended files to drop
- display whether the run is still safe to proceed
- if possible, recommend a narrower lane-specific packet automatically

### Example 2 — false completion prevention
Current failure mode:
- model edits one file
- one test passes
- assistant says “complete”
- roadmap item and blocker chain are not actually closed

Required system behavior:
- separate patch success from bounded-slice completion
- show unmet validation requirements
- show unmet artifact requirements
- show unmet truth-surface update requirements
- show item status as not complete until completion contract is satisfied

### Example 3 — governed next-task pull
Current failure mode:
- operator must manually infer what to do next from scattered files and terminal logs

Required system behavior:
- display next best governed target
- display score / reason for ranking
- display why competing items were not selected
- display whether the selected item is blocked, eligible_with_guardrails, or eligible

### Example 4 — auto-route to correct coding lane
Current failure mode:
- every task enters a generic coding flow
- too much irrelevant context is loaded
- validations are not task-specific

Required system behavior:
- infer likely task class from prompt + repo state
- produce a route such as `bugfix` or `bounded_feature`
- generate the correct Aider/OpenHands run packet
- show why that route was chosen

### Example 5 — terminal-heavy ambiguity reduction
Current failure mode:
- operator sees raw terminal lines, token warnings, and file additions without a strong synthesized control view

Required system behavior:
- synthesize terminal/run truth into structured operator panels
- make hidden blockers obvious
- reduce reliance on manual interpretation of long terminal output

### Example 6 — companion/overlay contextual help
Current future target mode:
- operator wants context-sensitive guidance near the cursor or in a lightweight overlay
- the system should help without requiring a full dashboard context switch

Required system behavior:
- route companion/overlay interactions back into the same governed lanes
- preserve blocker/completion/validation truth
- avoid creating a second unsupervised assistant surface

### Example 7 — framework-first complex-task handling
Current desired target mode:
- the operator wants one initial local prompt to produce the task layout/framework and the minimum bounded structure needed for completion
- Aider should then execute the bounded packet rather than requiring immediate external escalation

Required system behavior:
- heavy local tier produces the bounded framework packet first
- Aider executes the packet second
- validation/control-window truth checks closure third
- external escalation occurs only after the local path proves insufficient

### Example 8 — local AI stack role preservation
Current desired target mode:
- the operator wants the system to use the right local AI components without rethinking the whole stack every time

Required system behavior:
- default runtime is `Ollama`
- default coding executor is `Aider`
- `OpenHands` is visible as bounded dev surface, not equal co-primary by default
- `Open WebUI` is treated as the general local chat UI when that role is needed
- `AnythingLLM` is treated as the practical default document/RAG workspace
- `Dify`, `RAGFlow`, `LM Studio`, and `LocalAI` are surfaced only when the use case specifically justifies them
- overlapping tools in the same role trigger a warning or explicit justification requirement

### Example 9 — reuse-first implementation selection
Current desired target mode:
- the operator wants future assistants to install, wrap, or lightly modify mature public systems instead of re-creating generic subsystems

Required system behavior:
- OpenHands is treated as the primary substantial dev-agent surface to integrate, not a cue to build a new broad dev-agent shell
- OpenCode is treated as a TUI/design reference rather than a new second backbone
- Aider patch, repo-map, and auto-test logic are reused before writing fragile local replacements
- Plandex-style context slicing and rollback concepts are reused before building bespoke context and revert systems
- PR-Agent, MarkItDown, MCP reference servers, and n8n are considered before building new PR-review, document-conversion, tool-server, or workflow-builder logic
- the control surface can point back to the authoritative reuse registers so assistants do not re-derive these choices

## Affected systems

- UI/control surfaces
- developer assistant runtime/operator experience
- roadmap governance and active-item interpretation layer
- validation and artifact surfaces
- blocker registry / next-pull queue / derived planning surfaces
- telemetry/evidence display surfaces
- future autonomous local execution control loop
- Aider orchestration and task-lane selection layer
- OpenHands local execution interface layer
- future macOS companion/overlay interface layer
- local model runtime/runbook surfaces
- local AI stack role matrix surfaces
- OSS reuse/reference-implementation selection surfaces

## Expected file families

- `docs/roadmap/*`
- `docs/architecture/*` where control-surface linkage needs documenting
- future local dashboard frontend files
- future local dashboard backend/orchestration files
- future task-routing / run-packet generation files
- future run-state store or event stream files
- future integration adapters for Aider, Codex, Ollama, OpenHands, and validation tools
- future widget/panel/state model docs and tests
- future local deployment/config files for OpenHands integration
- future companion/overlay interaction files
- future local model/runbook configs and health-check surfaces
- future local AI stack selection and warning surfaces
- future thin wrappers/adapters around selected public implementations

## Dependencies

- `RM-GOV-001` — integrated roadmap-to-development tracking system with CMDB linkage, standardized metrics, enforced naming, and impact transparency
- `RM-OPS-004` — backup, restore, disaster-recovery, and configuration export verification
- `RM-OPS-005` — end-to-end telemetry, tracing, and audit evidence pipeline
- `RM-AUTO-001` — plain-English goal-to-agent system
- `RM-UI-001` — master control center for the system with web-first UI, tablet support, and later app-based surfaces
- `RM-GOV-009` — external application connectivity and integration control plane
- `RM-OPS-006` — governed desktop computer-use and non-API automation layer for local operator tasks

## Risks and issues

### Key risks
- building only a pretty dashboard without real governance/state linkage
- letting the system become a second planning authority instead of a control surface over canonical truth
- overbuilding the first slice instead of shipping the minimum high-value operator interface
- weak event/state modeling causing stale or misleading run status
- weak routing causing the wrong lane to be chosen repeatedly
- letting OpenHands become a parallel execution authority instead of a governed execution surface
- letting companion/overlay behavior bypass the same governance model as the main dashboard
- letting local model selection become ad hoc rather than runbook-driven
- letting local AI stack choices drift into overlapping defaults without role clarity
- rebuilding mature coding-agent and workflow subsystems unnecessarily

### Known issues / blockers
- exact first slice must remain bounded so this can land in one aggressive pass
- must not drift into broad control-center scope that belongs to RM-UI-001 overall
- must respect the existing roadmap/autonomy truth surfaces rather than inventing a parallel queue
- must keep OpenHands integrated under the same local-first and completion-contract rules as other execution surfaces
- companion/overlay mode should be added only as a governed extension, not as a freeform assistant surface
- framework-first handoff must remain bounded so it does not become a vague planning loop
- local AI stack role choices must stay synchronized with `LOCAL_AI_STACK_ROLE_MATRIX.md`
- reference-implementation posture must remain synchronized with the OSS reuse and template registers

## CMDB / asset linkage

- should later expose host/runtime/device visibility for execution environments
- should remain linkable to systems, services, hosts, and tools represented in inventory/CMDB-related surfaces
- should eventually expose execution-environment capability state relevant to local run routing

## External dependency documentation pack

### OpenHands
- **Official docs home:** https://docs.openhands.dev/
- **Primary repo or vendor page:** https://openhands.dev/ and official OpenHands repos/docs
- **Primary local setup path:** support local installation and `openhands serve` GUI deployment
- **Supported execution surfaces to consider:** CLI / terminal mode, `openhands web` browser terminal mode, `openhands serve` full GUI server mode
- **Sandbox posture:** prefer Docker sandbox as default isolated mode; use process/local mode only under explicit controlled conditions
- **Workspace posture:** support mounting the working repo into OpenHands for bounded tasks
- **Configuration capture:** record model/backend configuration, port bindings, sandbox mode, and repo mount behavior
- **Known caveats / integration constraints:** OpenHands must not become a parallel planning authority or bypass the canonical completion and blocker model
- **Adoption note:** `adopt-selective`

### OpenCode
- **Primary role in this item:** terminal-agent/TUI reference and design/code source
- **Adoption note:** `reference-only-selective`
- **Integration constraint:** do not let it become a second backbone; use as reference for TUI/session/tool ideas only

### Aider
- **Official docs home:** https://aider.chat/
- **Primary role in this item:** bounded editing/execution engine behind task-specific orchestration packets
- **Configuration capture:** model selection, repo-map behavior, context policies, drop candidates, and lane-specific validation bindings
- **Known caveats / integration constraints:** do not use one generic coding flow for all task types; lane-specific orchestration is required
- **Adoption note:** `adopt-now`

### Ollama / local models
- **Official docs home:** local model runtime runbook must record the canonical local endpoint and approved model tiers
- **Primary role in this item:** local-first execution substrate
- **Configuration capture:** host/port, context-length policy, approved model names, health checks, and tier bindings
- **Known caveats / integration constraints:** model context size and startup behavior must be explicit, not assumed
- **Adoption note:** `adopt-now`

### Open WebUI
- **Primary role in this item:** general local conversational UI when a chat/operator surface is needed
- **Adoption note:** `adopt-now`

### AnythingLLM
- **Primary role in this item:** practical local document/RAG workspace
- **Adoption note:** `adopt-now`

### PR-Agent / n8n / MarkItDown / MCP reference servers
- **Primary role in this item:** selectively reused supporting subsystems for PR review, workflows, doc conversion, and tool servers
- **Adoption note:** `selective-reuse`
- **Integration constraint:** prefer thin wrappers or installation over bespoke first-pass replacements

## Grouping candidates

- `RM-UI-001`
- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-AUTO-001`
- `RM-GOV-009`
- `RM-OPS-006`

## Grouped execution notes

- Shared-touch rationale: this item intersects directly with the active strategic cluster and the active governance cluster. It consumes status truth, blocker truth, validation truth, autonomous targeting truth, execution-run truth, the preferred local AI stack posture, and the reuse-first implementation posture, and presents them through a single operator surface.
- Repeated-touch reduction estimate: very high if done now, because it prevents repeated terminal-only diagnosis and repeated rework caused by hidden completion/validation/context failures, unnecessary greenfield subsystem work, and repeated stack-choice re-derivation.
- Grouping recommendation: `Bundle now` with adjacent execution-governance hardening surfaces, but keep the implementation slice bounded to the execution control and routing system itself.

## Recommended first milestone

Deliver a minimum viable local execution control and routing system that:

1. reads canonical roadmap truth and next-pull truth
2. displays current objective, current blocker chain, and eligible next target
3. displays file-context load, model limit, and overflow risk before execution
4. displays validations, artifacts, and completion-contract state for the current run
5. distinguishes patch success from bounded-slice completion and item completion
6. auto-routes simple task classes into the correct lane
7. uses Aider as the default editing engine for bounded code work
8. supports an immediately usable local OpenHands execution surface for operator monitoring and bounded execution handoff
9. records and surfaces the canonical local model runtime/startup policy used for each lane
10. records and surfaces the local AI stack role matrix so assistants know what is primary, selective, deferred, or rejected
11. records and surfaces the reuse-first implementation posture so assistants know what to install, wrap, or reuse before writing new generic subsystem code

## Status transition notes

- Expected next status: `Planned`
- Transition condition: implementation boundary, first slice, required repo truth sources, initial Aider/OpenHands integration posture, local model runbook policy, local AI stack role posture, and reference-implementation reuse posture are explicitly accepted
- Validation / closeout condition: a working local execution control and routing slice exists, reads canonical repo truth, supports Aider task-specific routing, provides an OpenHands local execution path, uses an explicit local model tier policy, and materially reduces false-complete / missed-context / hidden-blocker failures, unnecessary subsystem re-creation, and stack re-derivation in real local runs

## Reuse-wave closeout status sync

Bounded OpenHands integration work is implemented under this item's scope:
- wrapper/config/runbook surfaces are in-repo
- canonical headless validation surface is in-repo (`python3 bin/oss_wave_openhands_validate.py --timeout-seconds 900`)
- OpenHands status is: implemented / validated headless execution / model-dependent stability

This status sync does not declare full RM-UI-005 completion.

## Notes

This item is intentionally the most important next implementation target. It is not merely a dashboard improvement. It is the missing operator, routing, runtime-selection, stack-role-preservation, reuse-first, and execution surface that turns the current local coding workflow from terminal-heavy and ambiguity-prone into a governed local execution system.
