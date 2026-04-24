# RM-GOV-009

- **ID:** `RM-GOV-009`
- **Title:** External application connectivity and integration control plane
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Completed`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a single external-application connectivity and integration control plane that standardizes how the platform connects to outside applications, APIs, SaaS tools, local services, and adopted OSS systems. This layer should centralize adapter boundaries, auth handling, sync posture, webhook/event intake, rate-limit handling, capability registration, and policy/governance rules so the rest of the platform does not wire external systems ad hoc.

This item now explicitly includes first-class connector posture for:

- GitHub
- Google Calendar
- Gmail

These are not side notes. They are priority examples of why the control plane exists: the same connector surfaces should be consumable by the coding assistant, athlete/coach functions, personal-assistant functions, dashboard/control surfaces, and future agentic workflows without each branch inventing its own auth and sync model.

This item also now owns the **local AI platform adoption matrix** that decides which local AI systems are part of the preferred stack, which are selective additions, and which are deferred or rejected as current core-stack choices.

It also now owns the **reference-implementation and public-template reuse posture** for connector and tool surfaces, so assistants install, wrap, or lightly modify existing systems instead of re-creating broad categories of tooling from scratch.

## Why it matters

The platform already depends on or plans to depend on a growing set of external systems such as Home Assistant, Plex, Sonarr, Radarr, Plane, Strava, ChatGPT/OpenAI surfaces, GitHub, Google Calendar, Gmail, and future adopted tools. Without one governing connectivity layer, integrations will drift into one-off adapters, duplicate auth handling, inconsistent polling/sync behavior, and weak operational visibility. A control plane for external connections reduces that drift and makes future autonomous work safer.

GitHub, Google Calendar, and Gmail deserve explicit emphasis because they unlock immediate high-value workflows:

- GitHub for governed repo interaction, backup, updates, branch awareness, and code-state integration
- Google Calendar for schedule, travel, event, and time-awareness across assistant functions
- Gmail for inbox/context awareness, communication surfaces, and future assistant workflows

The same governance discipline is needed for local AI systems. Without one clear role matrix, the platform will drift into overlapping runtime, UI, RAG, workflow, and agent tools that waste time and token budget.

The same governance discipline is also needed for public repos and templates. Without one clear reuse posture, assistants will keep rebuilding weaker versions of mature OSS products, CLIs, MCP servers, workflow tools, and document-ingestion utilities.

## Key requirements

- define one standard adapter boundary for external applications and services
- centralize auth, credential reference posture, token refresh, and permission boundaries
- define standard patterns for pull sync, push/webhook intake, polling, and event normalization
- support capability registration so the platform knows what each external integration can do
- provide observability and failure handling for external connectors
- keep external systems subordinate to the platform architecture rather than allowing them to become hidden backbones
- remain compatible with MCP where MCP is the preferred boundary

### Explicit connector priorities now in scope

#### GitHub
- repo state visibility
- branch/commit/PR awareness where appropriate
- governed repo update workflows
- backup and restore-aware repo posture
- ability for coding/execution surfaces to use GitHub as a governed external system instead of ad hoc shell behavior alone

#### Google Calendar
- event and travel awareness
- schedule-aware planning and assistant workflows
- ability for coach/athlete and personal-assistant systems to consume calendar state through the same connector layer
- permissioned availability/intention surfaces rather than broad uncontrolled access

#### Gmail
- inbox/message metadata awareness
- governed read/send/use posture where later justified
- ability for multiple assistant branches to consume Gmail-derived context through the same connector layer
- permission and privacy boundaries explicit from the start

### Local AI platform role matrix now in scope

The control plane must preserve one explicit adoption posture for local AI systems.

#### Adopt now
- **Ollama** — primary local model runtime
- **Open WebUI** — primary general local chat UI
- **AnythingLLM** — primary practical document/RAG workspace
- **Home Assistant Assist** — primary local home/voice automation anchor

#### Adopt selectively
- **Aider** — primary local coding executor
- **OpenHands** — bounded dev-agent surface
- **LM Studio** — desktop/server local model serving alternative where host fit justifies it
- **Dify** — workflow and AI app builder above the governed substrate
- **RAGFlow** — advanced document understanding only when document extraction quality becomes the bottleneck
- **LocalAI** — compatibility API bridge only when concrete compatibility or multimodal breadth justifies the overlap

#### Defer
- **OpenClaw** — later messaging / assistant gateway candidate
- **LLaMA-Factory** — later fine-tuning and training stack
- **CrewAI** — later multi-agent experimentation
- **AutoGen** — later multi-agent experimentation
- **Nextcloud Hub AI** — later adjunct, not current core stack

#### Reject for current core stack
- **Libra Chat** — overlapping local chat UI role already covered by Open WebUI
- **BrowserOS** — overlapping browser/agent surface already better treated under computer-use branches
- **ADeus** — too specialized for the current core stack

### Reference implementation and public-template reuse posture now in scope

Assistants must prefer **install vs wrap vs targeted module reuse** before rebuilding.

#### High-value first-wave references
- **OpenHands** — selective installed dev-agent surface and sandbox model
- **OpenCode** — terminal-agent/TUI design and code reference, not current backbone
- **MCP reference servers** — official tool reference implementations for filesystem, fetch, git, memory, sequential-thinking, and related tool boundaries
- **PR-Agent** — PR review automation instead of first-pass custom PR reviewer logic
- **n8n** — workflow automation platform instead of first-pass visual workflow builder
- **MarkItDown** — document conversion utility instead of bespoke broad document-to-markdown conversion
- **Plandex concepts** — context slicing and change-set / rollback posture for context-safe and revert-safe execution

#### Reuse rules
- install the whole system when it already cleanly owns the role
- wrap and integrate when the system is strong but must remain subordinate to platform governance
- reuse targeted modules or templates when only a subsystem is needed
- do not vendor or fork large codebases casually when a thin adapter is sufficient
- do not rebuild broad categories of workflow, document-ingest, MCP-tool, or PR-review capability without checking the registered references first

The authoritative sources for this posture are:
- `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md`
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/architecture/REFERENCE_IMPLEMENTATIONS_AND_PUBLIC_TEMPLATES.md`
- `docs/roadmap/REUSE_FIRST_IMPLEMENTATION_WAVE.md`

## Affected systems

- roadmap governance layer
- external application catalog and crosswalk surfaces
- local AI stack selection and deployment posture
- future runtime tool/adapter boundaries
- future sync/webhook/event normalization surfaces
- future dashboard and control-center surfaces that consume external integrations
- coding assistant / repo operations workflows
- future athlete/coach and personal-assistant branches
- OSS adoption and reference-implementation decision surfaces

## Expected file families

- `docs/roadmap/*`
- `docs/architecture/LOCAL_AI_STACK_ROLE_MATRIX.md`
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/architecture/REFERENCE_IMPLEMENTATIONS_AND_PUBLIC_TEMPLATES.md`
- future integration-control-plane architecture docs
- future adapter registry/config files
- future auth/connector policy files
- future sync/event handling surfaces
- future GitHub / Google connector binding/config docs
- future local AI stack deployment notes and configuration surfaces
- future wrapper/adapter files around adopted reference implementations

## Dependencies

- `RM-GOV-008` — external application and integration registry with phased adoption and interface guidance
- `RM-GOV-006` — hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap
- `RM-GOV-007` — Plane deployment, roadmap field mapping, and repo-to-Plane sync implementation
- shared runtime substrate and external-systems policy

## Risks and issues

### Key risks

- could become overengineered if built before enough common connector patterns are identified
- could accidentally become a second backbone if it tries to own platform logic instead of external connectivity concerns
- privacy/auth posture could drift if Gmail/Calendar are consumed directly by multiple branches without one governing control plane
- local AI tool sprawl could create duplicated runtime, UI, and workflow surfaces without a clear role matrix
- assistants could still rebuild subsystems unnecessarily if reference-implementation posture is not carried into execution packets

### Known issues / blockers

- exact first adapter boundary and connector registry model still need to be defined
- auth posture must remain consistent with local-first and governance rules
- GitHub / Google connectors should be implemented through the control plane, not as branch-specific one-offs
- local AI platform roles must remain synchronized with `LOCAL_AI_STACK_ROLE_MATRIX.md` and `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`
- reuse posture must remain synchronized with the OSS reuse register, reference-implementation register, and first-wave implementation packet

## CMDB / asset linkage

- should later link external systems to owned hosts, services, devices, accounts, and inventory/CMDB records where relevant
- should support capability-aware planning and impact analysis for integrated services
- should remain aware of hardware fit for local AI platform choices where those choices depend on known host capability

## Grouping candidates

- `RM-GOV-008`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-GOV-001`

## Grouped execution notes

- Shared-touch rationale: this item overlaps heavily with the external systems registry, operational roadmap layer, governance metadata, execution-control surfaces, and future runtime adapter design.
- Repeated-touch reduction estimate: high if built together with adjacent governance/integration work.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Define the external connector model for one or two representative systems, including capability registration, auth handling posture, sync/event intake mode, and normalized status/health reporting, then document the control-plane rules those connectors must follow.

In parallel, define the first stable local AI platform role set and deployment posture, including:

- which runtime is primary
- which UI is primary
- which RAG/document system is primary
- which tools are selective additions only
- which tools are explicitly deferred or rejected for the current core stack
- which public implementations should be installed whole
- which should be wrapped
- which should be reused as targeted modules/templates

The highest-value first concrete connector set should now strongly consider:

- GitHub
- Google Calendar
- Gmail

because those connectors will be reusable across the largest number of future assistant and execution workflows.

The first concrete reuse-first execution packet is now:
- `docs/roadmap/REUSE_FIRST_IMPLEMENTATION_WAVE.md`

## Status transition notes

- Expected next status: `Planned`
- Transition condition: first connector model, adapter boundary, auth/sync policy, local AI stack role matrix, and reference-implementation reuse posture are explicitly defined
- Validation / closeout condition: one bounded external connectivity slice exists and becomes the standard pattern for later integrations, and the local AI platform stack plus reference-implementation posture are documented clearly enough that future assistants do not need to re-derive adoption decisions

## Notes

This item should produce one governing connection model for external systems, one explicit role matrix for local AI platform tools, and one reuse-first posture for public implementations and templates. It should reduce one-off integrations, local AI tool sprawl, and unnecessary greenfield implementation.

## Reuse-wave closeout status sync

For current repo truth alignment, this item now carries the implemented bounded reuse-wave status:
- OpenHands implemented with validated headless execution and model-dependent stability
- MarkItDown, MCP reference-server wrappers, and PR-Agent wrappers implemented as bounded governed surfaces
- n8n remains evaluation-only in this wave
