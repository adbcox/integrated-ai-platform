# System Gap Review and Roadmap Expansion — 2026-04-21

## Purpose

This document reviews the integrated AI platform as a whole system rather than as an ad hoc set of roadmap additions.

It identifies missing capability layers, architecture gaps, sequencing weaknesses, and new grouped roadmap additions needed to make the platform operable, governable, and scalable.

## Review posture

This review does **not** treat existing system architecture as immutable truth.
It treats existing docs and decisions as guidance, then asks:

- what is missing for the system to be fully functional,
- what is missing for it to be stable and verifiable,
- what is missing for the local development assistant to become the main execution engine,
- what is missing for the platform to support its broader goals in media, health, athlete awareness, home operations, procurement, fabrication, and domain assistants.

## High-level findings

### 1. The roadmap is stronger at capturing features than architecture closure
The current roadmap captures many useful feature areas, but several system-enabling layers are still under-specified.

### 2. The local development assistant is correctly the top priority
The repo is now correctly centered on `RM-DEV-005`, `RM-DEV-003`, `RM-DEV-002`, `RM-INTEL-001`, and `RM-INTEL-002` as the main path to autonomy.

### 3. The system still needs a more explicit operability backbone
Missing or under-expressed areas include:

- trust boundaries and secrets management
- event/job orchestration and state transitions
- dependency topology and CMDB graph depth
- backup / restore / disaster recovery
- telemetry / tracing / audit evidence
- roadmap-to-execution compilation and batch pull selection

### 4. Some domain packages lack foundational substrate beneath them
Several domain areas now exist in the roadmap, but their ingestion, consent, topology, or control foundations remain thin.
This is especially true for:

- athlete awareness / AI coaching
- personal health monitoring
- multi-surface control center expansion
- packaging / installability

### 5. Prioritization needed more realism
The roadmap has historically leaned too heavily on broad labels like `High`.
The standards now require richer sequencing fields and queueing logic to address this.

## Architecture gaps by layer

## A. Platform governance and execution selection gaps

### Gap A1 — no explicit roadmap dependency graph and pull engine
The system needs a way to determine not just what exists in the roadmap, but what should be pulled next automatically based on dependencies, readiness, ranking, and grouped execution opportunities.

### Gap A2 — no explicit cycle/release/cadence governance layer
The platform now has roadmap docs and execution packs, but it still needs a clean model for batching roadmap work into cycles or release trains.

### Gap A3 — no full architecture review baseline artifact
There is not yet a single canonical reference architecture document with subsystem boundaries, trust boundaries, and integration expectations made explicit.

## B. Runtime and operations gaps

### Gap B1 — trust boundaries, identity, secrets, and policy are under-specified
A local/private agent stack still needs strong handling for secrets, tokens, credentials, scope, and permission boundaries.

### Gap B2 — event/job orchestration and state transition backbone is under-specified
The system has many workflows, but no strongly explicit backbone for jobs, events, retries, state transitions, and orchestration across subsystems.

### Gap B3 — backup / restore / disaster recovery is not yet a first-class roadmap area
A platform with local data, CMDB, memory, and automation needs verifiable recovery posture.

### Gap B4 — telemetry / tracing / audit evidence is not yet deep enough
The system needs end-to-end observability not just for uptime, but for agent actions, tool calls, workflow decisions, and audit evidence.

## C. Information model / CMDB gaps

### Gap C1 — CMDB is present conceptually but needs deeper dependency topology
A useful CMDB for this system must model:

- services
- applications
- hardware
- toolchains
- data stores
- permissions
- dependencies
- capabilities
- roadmap linkage

### Gap C2 — no explicit capability graph linking assets, systems, and roadmap work
This is needed so the system can understand what owned things enable, what missing things block progress, and what roadmap items depend on them.

## D. Local development assistant intelligence gaps

### Gap D1 — structure-aware code intelligence is still not fully explicit in the roadmap
The local agent should likely adopt helpers such as:

- Tree-sitter
- LSP
- structural search/rewrite tools such as ast-grep
- fast indexed code search where justified

### Gap D2 — comparative evaluation of open-source coding-agent surfaces was missing
This is now partially addressed by `RM-INTEL-002`, but it needs follow-through.

## E. Domain-specific foundation gaps

### Gap E1 — athlete awareness / AI coach foundation is missing as a roadmap-first substrate
The user explicitly wants this long term. The platform needs a proper ingestion, consent, API, and signal model before “AI coach” becomes meaningful.

### Gap E2 — personal health monitoring and privacy-controlled signal ingestion is missing
If health data is part of the system, consent, data minimization, privacy, and role boundaries must be defined from the start.

### Gap E3 — multi-surface UI family lacks a fuller shell/module strategy
The control-center item exists, but broader multi-surface strategy still needs explicit shell/module decomposition and state consistency.

## Proposed roadmap additions

These additions are organized as grouped packages and parent/child relationships.

---

## Group 1 — Architecture closure and execution governance

### RM-CORE-003
- **Title:** Canonical reference architecture and subsystem contract baseline
- **Category:** CORE
- **Type:** Program
- **Priority band:** Critical
- **Priority class:** P0
- **Target horizon:** now
- **Why:** Needed to stop patching subsystems without an authoritative architecture baseline.

### RM-GOV-004
- **Title:** Roadmap dependency graph and next-pull planner
- **Category:** GOV
- **Type:** System
- **Priority band:** Critical
- **Priority class:** P0
- **Target horizon:** now
- **Why:** Needed so roadmap execution can be selected systematically rather than manually.

### RM-GOV-005
- **Title:** Cycle, release, and batch-governance model for roadmap execution
- **Category:** GOV
- **Type:** System
- **Priority band:** High
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed to convert roadmap backlog into repeatable execution cadence.

### RM-AUTO-002
- **Title:** Roadmap-to-execution compiler and batch prompt builder
- **Category:** AUTO
- **Type:** Program
- **Priority band:** Critical
- **Priority class:** P0
- **Target horizon:** now
- **Why:** Needed so the system can take selected roadmap items and generate governed execution prompts and packages automatically.

#### Grouping note
These four items should be treated as one architecture-governance package because they all contribute to turning the roadmap into an executable operating system for the project.

---

## Group 2 — Runtime trust, orchestration, and recoverability

### RM-CORE-004
- **Title:** Unified event, job, and state-transition orchestration backbone
- **Category:** CORE
- **Type:** Program
- **Priority band:** Critical
- **Priority class:** P0
- **Target horizon:** next
- **Why:** Needed for cross-subsystem automation, retries, workflow state, and safe orchestration.

### RM-CORE-005
- **Title:** Identity, secrets, permissions, and trust-boundary management
- **Category:** CORE
- **Type:** System
- **Priority band:** Critical
- **Priority class:** P0
- **Target horizon:** next
- **Why:** Needed for any serious local/private agent system that touches APIs, devices, and user data.

### RM-OPS-004
- **Title:** Backup, restore, disaster-recovery, and configuration export verification
- **Category:** OPS
- **Type:** System
- **Priority band:** High
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed so the system can survive failure and be reconstituted safely.

### RM-OPS-005
- **Title:** End-to-end telemetry, tracing, and audit evidence pipeline
- **Category:** OPS
- **Type:** System
- **Priority band:** High
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed for trust, debugging, validation, and regulated-style transparency.

#### Grouping note
These four items should be executed as a runtime-operability package.

---

## Group 3 — CMDB and capability graph deepening

### RM-INV-004
- **Title:** CMDB service/application/dependency topology and capability graph
- **Category:** INV
- **Type:** Program
- **Priority band:** Critical
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed to model what the platform is, what depends on what, and what capabilities are blocked or enabled.

### RM-INV-005
- **Title:** Asset-to-roadmap and asset-to-execution linkage layer
- **Category:** INV
- **Type:** System
- **Priority band:** High
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed so roadmap items can know what services, hosts, credentials, devices, and components they touch.

#### Grouping note
These should be treated as a CMDB expansion package and executed with `RM-GOV-001` lineage rules.

---

## Group 4 — Local development assistant intelligence expansion

### RM-DEV-006
- **Title:** Structure-aware code intelligence layer (Tree-sitter, LSP, structural search)
- **Category:** DEV
- **Type:** System
- **Priority band:** Critical
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed to materially raise local agent code understanding without greenfield parser work.

### RM-DEV-007
- **Title:** Indexed code search and multi-repo retrieval backend
- **Category:** DEV
- **Type:** System
- **Priority band:** High
- **Priority class:** P2
- **Target horizon:** soon
- **Why:** Needed if repo or multi-repo scale exceeds simple grep and repo maps.

### RM-DEV-008
- **Title:** Memory governance, summarization, and provenance policy for the local agent
- **Category:** DEV
- **Type:** System
- **Priority band:** High
- **Priority class:** P1
- **Target horizon:** next
- **Why:** Needed so the local agent’s memory does not become noisy, unsafe, or weakly traceable.

#### Grouping note
These should be treated as the next intelligence-uplift package after `RM-INTEL-002` and `RM-DEV-005` progress.

---

## Group 5 — Athlete and health foundations

### RM-HOME-002
- **Title:** Athlete awareness and training-data ingestion substrate
- **Category:** HOME
- **Type:** Program
- **Priority band:** High
- **Priority class:** P2
- **Target horizon:** soon
- **Why:** Needed to support the long-term AI coach objective using structured training data ingestion rather than ad hoc integrations.

### RM-HOME-003
- **Title:** Personal health signal ingestion, consent, and privacy-controlled data policy
- **Category:** HOME
- **Type:** Program
- **Priority band:** High
- **Priority class:** P2
- **Target horizon:** soon
- **Why:** Needed before any serious health or readiness intelligence can be trusted.

### RM-HOME-004
- **Title:** Athlete readiness and coaching inference layer
- **Category:** HOME
- **Type:** Feature
- **Priority band:** Medium
- **Priority class:** P3
- **Target horizon:** later
- **Why:** This should follow after the athlete and health substrates exist.

#### Grouping note
`RM-HOME-004` should not be pulled before `RM-HOME-002` and `RM-HOME-003`.

---

## Group 6 — UI family and operator experience

### RM-UI-005
- **Title:** Multi-surface shell/module architecture and shared state model
- **Category:** UI
- **Type:** System
- **Priority band:** High
- **Priority class:** P2
- **Target horizon:** soon
- **Why:** Needed to keep control-center, tablet, ambient, and later app surfaces coherent.

### RM-UI-006
- **Title:** Role-aware action surfaces and operator safety controls
- **Category:** UI
- **Type:** Feature
- **Priority band:** High
- **Priority class:** P2
- **Target horizon:** soon
- **Why:** Needed so control surfaces reflect safe operations, trust levels, and approval classes.

---

## Group 7 — Media and domain-specific hardening

### RM-MEDIA-005
- **Title:** Media service topology, storage policy, and retention-state model
- **Category:** MEDIA
- **Type:** System
- **Priority band:** Medium
- **Priority class:** P3
- **Target horizon:** later
- **Why:** Needed to bring media workflows under stronger storage and service governance.

### RM-SHOP-005
- **Title:** Design-to-fabrication handoff normalization for 3D and woodworking workflows
- **Category:** SHOP
- **Type:** System
- **Priority band:** Medium
- **Priority class:** P3
- **Target horizon:** later
- **Why:** Needed once 3D/model workflows and structure-design workflows begin to produce more outputs.

## Strategic sequencing recommendation

### P0 now
- `RM-DEV-005`
- `RM-INTEL-002`
- `RM-CORE-003`
- `RM-GOV-004`
- `RM-AUTO-002`

### P0/P1 next
- `RM-CORE-004`
- `RM-CORE-005`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-INV-004`
- `RM-DEV-006`
- `RM-DEV-008`

### P2 soon
- `RM-GOV-005`
- `RM-INV-005`
- `RM-UI-005`
- `RM-UI-006`
- `RM-HOME-002`
- `RM-HOME-003`
- `RM-DEV-007`

### P3 later
- `RM-HOME-004`
- `RM-MEDIA-005`
- `RM-SHOP-005`

## Review conclusion

The platform does not primarily suffer from a lack of ideas.
It suffers from an incomplete bridge between:

- roadmap and execution,
- architecture and features,
- local agent intelligence and safe operational substrate,
- CMDB awareness and actual dependency reasoning.

The most important correction is therefore **not** to stop adding features, but to add the missing architectural and governance items that let the local development assistant safely become the system’s primary implementation engine.
