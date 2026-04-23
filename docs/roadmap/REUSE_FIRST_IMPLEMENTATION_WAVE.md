# Reuse-First Implementation Wave

## Purpose

This document defines the **first concrete implementation wave** for reuse-first OSS adoption intended to accelerate local AI coding capability.

It exists to convert the reuse policy into a bounded execution packet.

This wave is intentionally limited to systems that can improve local AI coding capability quickly without forcing a broad architectural rewrite.

## Current implementation closeout status

This wave is no longer planning-only. The bounded closeout implementation is present in-repo with wrappers, runbooks, and validation tooling.

OpenHands closeout status is:
- implemented
- validated headless execution
- model-dependent stability

Validation evidence surface:
- `python3 bin/oss_wave_openhands_validate.py --timeout-seconds 900`
- `docs/runbooks/OPENHANDS_REUSE_FIRST_RUNBOOK.md`

## Scope of this wave

Included now:
- OpenHands
- PR-Agent
- MarkItDown
- MCP reference servers
- optional bounded evaluation lane for n8n

Deferred from this wave:
- full n8n production rollout
- Dify rollout
- RAGFlow rollout
- LocalAI rollout
- Tabby rollout
- OpenClaw
- full multimodal document systems
- fine-tuning stacks

## Wave goals

1. improve bounded local dev-agent execution
2. improve code review / PR summarization and automation
3. improve document ingestion for local AI context and RAG workflows
4. improve governed tool/server reuse via MCP reference implementations
5. avoid greenfield implementation of subsystems that already exist upstream

## Governing rules

- all adopted systems remain subordinate to canonical roadmap, validation, and completion truth
- prefer install or thin-wrapper integration before forking
- do not vendor large upstream codebases into this repo unless there is a proven need
- every adopted system must have validation and rollback steps
- every adopted system must have a bounded role, not an open-ended mandate

## Wave inventory

### 1. OpenHands

#### Role
Selective installed dev-agent surface and bounded execution environment.

#### Why now
OpenHands provides a substantial local dev-agent surface with CLI/GUI/server options and sandboxing. It is the fastest path to add a richer bounded local execution interface without inventing a new general dev-agent shell.

#### Adoption posture
- mode: `wrap-and-integrate`
- role owner: `RM-UI-005`
- scope now:
  - local deployment notes
  - canonical launch modes
  - config capture
  - wrapper/integration boundary
  - validation smoke path

#### Required outputs
- canonical deployment runbook
- approved launch modes (`CLI`, `web`, `serve`, Docker-first posture)
- canonical env/config fields to capture
- workspace mount policy
- sandbox policy
- validation commands
- rollback and disablement steps

#### Implementation boundary
Do not rebuild OpenHands features locally.
Integrate it as a governed optional execution surface.

#### Closeout state
- implemented via `bin/oss_wave_openhands.sh`
- validated via `bin/oss_wave_openhands_validate.py`
- operational details documented in `docs/runbooks/OPENHANDS_REUSE_FIRST_RUNBOOK.md`
- stability remains model-dependent

### 2. PR-Agent

#### Role
Automated PR review / describe / summarize / bounded review automation surface.

#### Why now
This gives immediate value for review loops and PR summaries without building a custom review bot.

#### Adoption posture
- mode: `wrap-and-integrate-selective`
- role owner: `RM-GOV-009`
- scope now:
  - approved deployment modes
  - local/self-hosted posture
  - prompt/config boundary
  - GitHub integration notes
  - validation commands

#### Required outputs
- PR-Agent adoption note in governance docs
- approved local or repo workflow integration posture
- defined command or workflow entrypoints
- validation steps for PR description/review generation
- rollback/disable steps

#### Implementation boundary
Do not build first-pass PR review logic if PR-Agent satisfies the use case.

#### Closeout state
- bounded wrapper/config/workflow surfaces implemented
- remains governed and subordinate to canonical roadmap/completion authority

### 3. MarkItDown

#### Role
Document-to-markdown conversion utility for local ingestion pipelines.

#### Why now
It is a high-leverage reusable utility for RAG/document ingestion and can support both coding and knowledge workflows.

#### Adoption posture
- mode: `reuse-as-library-or-cli`
- role owner: `RM-GOV-009`
- scope now:
  - install path
  - supported file categories
  - wrapper function boundary
  - validation samples

#### Required outputs
- approved install method
- thin-wrapper guidance for conversion use
- supported-input matrix (minimum required set)
- validation samples and expected outputs
- rollback/uninstall steps

#### Implementation boundary
Do not build a generic broad document conversion layer first.
Use MarkItDown where it fits.

#### Closeout state
- install/wrapper/smoke surfaces implemented for bounded local ingestion workflows

### 4. MCP reference servers

#### Role
Official reference implementations for tool/server boundaries such as filesystem, fetch, git, memory, sequential-thinking, and related tools.

#### Why now
They provide immediate official examples and reusable server surfaces for tool boundaries instead of inventing ad hoc local tools.

#### Adoption posture
- mode: `reference-implementation-thin-wrapper`
- role owner: `RM-GOV-009`
- scope now:
  - approved short list of servers to evaluate first
  - wrapper boundary
  - permission and security caveats
  - validation smoke tests

#### Initial short list
- filesystem
- fetch
- git
- memory
- sequential-thinking

#### Required outputs
- approved first server set
- installation or launch notes
- security notes per server
- wrapper/registration policy
- validation smoke commands
- rollback/disable steps

#### Implementation boundary
Treat them as reference implementations, not hidden production backbones.
Wrap them under repo governance.

#### Closeout state
- approved first-server shortlist and wrapper/smoke surfaces implemented
- explicitly retained as reference/test surfaces, not hidden production backbone

### 5. n8n (bounded evaluation lane)

#### Role
Visual workflow automation layer candidate.

#### Why only as evaluation now
n8n is powerful, but broad workflow rollout would expand scope too far for this first wave.

#### Adoption posture
- mode: `bounded-evaluation-only`
- role owner: `RM-GOV-009`
- scope now:
  - fit assessment
  - overlap analysis vs Dify / existing control model
  - minimal deployment note only if needed

#### Required outputs
- evaluation note
- explicit adopt/defer decision criteria
- overlap warning with Dify and custom control-plane logic

#### Implementation boundary
Do not start a full workflow-platform rollout in this wave.

#### Closeout state
- explicitly evaluation-only
- broad rollout deferred

## Execution sequence

### Phase A — documentation and runbook normalization
1. document exact role of each wave system
2. define install/wrap/reuse boundary for each
3. define validation and rollback steps
4. bind each system to the owning roadmap item

### Phase B — bounded deployment notes and thin-wrapper planning
1. OpenHands deployment runbook and config surface
2. PR-Agent deployment/integration posture
3. MarkItDown wrapper guidance and validation matrix
4. MCP first-server shortlist and wrapper/security posture
5. n8n evaluation note

### Phase C — implementation packet handoff
1. produce a bounded execution packet for actual installation/integration
2. keep each system scoped to its role
3. do not broaden into general platform rollout unless the first wave validates well

## Validation contract

The wave is only considered materially complete when:
- each system has a clear role and owner
- each system has install/wrap guidance
- each system has validation steps
- each system has rollback steps
- assistants no longer need to rethink whether to build these subsystems from scratch

## Rollback rule

If any adopted system causes role overlap, governance drift, or unclear operational posture:
- revert its active status to deferred or selective
- keep the documentation truth explicit
- do not leave ambiguous partial adoption state

## Relationship to roadmap items

Primary owners:
- `RM-UI-005`
- `RM-GOV-009`

Secondary relevance:
- `RM-AUTO-001`
- `RM-INTEL-003`

## Notes

This document is the first concrete bridge between reuse policy and implementation. It should be used to generate the next execution packet rather than sending assistants back into broad OSS exploration.
