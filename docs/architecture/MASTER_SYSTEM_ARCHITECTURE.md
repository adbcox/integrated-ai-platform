# Integrated AI Platform — Master System Architecture

## 1. Document role

This document is the **master architecture source of truth** for the integrated AI platform.

It exists to consolidate architecture intent, technical design direction, program goals, platform boundaries, software-adoption decisions, and domain expansion strategy into one repo-owned document that can be read as the cornerstone of the roadmap.

This document is intentionally broader than a roadmap item list.

It explains:

- what the system is
- why it exists
- what technical architecture it is converging toward
- what the current and target operating models are
- what external systems are adopted versus built locally
- how future branches must be implemented without creating architectural drift

## 2. Canonicality and relationship to other documents

This document is the **architecture master**.

It should be treated as the primary narrative and structural source for:

- system vision
- architecture principles
- subsystem boundaries
- runtime model
- domain-branch rule
- software-adoption posture
- architecture-to-roadmap interpretation

This document does **not** replace every other document in the repository.

Instead, it sits above them as the explanatory master.

### 2.1 Supporting architecture documents

This master is supported by the following architecture-local detail documents:

- `docs/architecture/README.md` — architecture document index and reading order
- `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md` — explicit mission and scope statement
- `docs/architecture/AUTHORITY_SURFACES.md` — document/system authority by truth type
- `docs/architecture/RUNTIME_SUBSTRATE.md` — shared runtime substrate expectations and boundaries
- `docs/architecture/EXTERNAL_SYSTEMS_POLICY.md` — adopt/build/hybrid policy and external-system rules
- `docs/architecture/DOMAIN_BRANCH_RULES.md` — domain branch expansion constraints

### 2.2 Supporting authority surfaces outside the architecture directory

The system still relies on other documents for narrower authority functions:

- `docs/roadmap/ROADMAP_AUTHORITY.md` — roadmap status authority
- `docs/roadmap/ROADMAP_STATUS_SYNC.md` — roadmap state truth
- `docs/roadmap/ROADMAP_MASTER.md` — roadmap interpretation and strategic backlog view
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` — external software and integration catalog
- promotion manifest and validation artifacts — release and promotion truth
- future CMDB-lite or later CMDB authority surface — architecture/runtime inventory truth

### 2.3 Practical rule

Use this document when asking:

- what is this system trying to become?
- what architecture are we actually building toward?
- what are the non-negotiable platform rules?
- what belongs in the shared runtime versus a branch-specific tool?
- what external systems are part of the architecture?
- how should roadmap items be interpreted against the target architecture?

Then use the architecture-local detail documents when you need narrower rules without overloading the master.

## 3. Executive architecture summary

The integrated AI platform is a **governed local-first AI operating system and control plane** whose broader mission is to support autonomous and semi-autonomous execution across business, personal, operational, and development workflows.

Its most important near-term architectural reality has been the completion of a local-execution and coding-autonomy substrate, because that substrate is the enabling foundation that allows the broader platform to extend and govern itself locally.

The most important architectural decision remains:

> **Keep the existing control plane, add a shared runtime substrate, preserve governed local execution, and treat local coding autonomy as a foundational capability inside a broader autonomous-function platform.**

The system is therefore **not** being built only as a coding assistant, a generic chatbot shell, a pure PM tool, or a loose collection of domain apps.

It is being built as a layered platform with:

- a retained control plane
- a shared runtime substrate
- a stable inference and execution fabric
- standardized artifact and validation contracts
- a governance and roadmap system with explicit impact modeling
- a connector and workflow fabric
- domain branches that sit on top of the shared substrate instead of inventing their own backbones

## 4. System vision

### 4.1 Product-level vision

The intended end state is a unified, local-first, extensible AI platform that can:

- act as a central governed AI brain and control plane
- support autonomous and semi-autonomous business workflows
- support personal and operational workflows
- manage and reason about code, systems, infrastructure, and assets
- provide dashboard-, tablet-, chat-, voice-, and remote-access control surfaces
- integrate with external systems rather than rebuilding all commodity capabilities
- expand into domain branches such as media control, athlete analytics, environmental intelligence, inventory/capability mapping, repair/restoration, communication workflows, and specialized planning tools

### 4.2 Strategic vision

The system is intended to evolve into a broader operations and intelligence platform **without** changing architectural backbone each time a new feature branch is added.

That means:

- new branches must reuse the same runtime substrate
- execution evidence must remain comparable across branches
- external integrations must be cataloged and deliberate
- roadmap work must be architecture-led rather than idea-led
- coding autonomy must remain an enabling foundation, not a mission-narrowing identity trap

### 4.3 User experience vision

At the user-facing layer, the system is expected to mature into:

- a master control center
- a no-code or low-code tile/click-based interface
- room-aware ambient tablet dashboards
- message/voice/chat ingress channels
- specialized domain applications built on the same substrate
- a governance-aware environment that can move from idea to roadmap item to execution to validation with less manual churn

## 5. Primary program objective

The most important near-term objective has been:

> **Strengthen the local development and execution substrate so the system can improve, maintain, and extend itself locally with minimal dependence on Claude Code or Codex for routine coding work.**

That objective has mattered because it enables the broader platform mission.
It should not be misread as meaning the platform is only a coding assistant.

In practical terms, the platform has needed to prioritize:

1. shared runtime completion
2. local governed execution reliability
3. artifact completeness and promotion evidence
4. developer assistant proof on the shared substrate
5. self-sufficiency uplift
6. controlled expansion into broader autonomous-function branches

## 6. What the system is not

To prevent drift, it is important to say what the system is **not**.

It is not:

- only a roadmap board with some AI features attached
- only a loose collection of scripts and models
- only a Claude Code wrapper with local tools on the side
- only a custom rebuild of every commodity platform component
- only a collection of domain apps each with its own execution loop
- only a system that treats local coding autonomy as the whole mission
- a system that treats architecture handoffs, tactical packages, and roadmap execution as equivalent authority layers

## 7. Current architectural reading

Based on the revised target architecture handoffs and control-window adoption packet, the current platform has real strengths but also clear gaps.

### 7.1 Current strengths

The platform already has a credible governed-platform foundation, including:

- stage and manager orchestration
- checkpoint/resume behavior
- worker budget logic
- benchmark and qualification surfaces
- promotion surfaces
- learning-loop artifacts
- trusted external pattern intake
- roadmap/governance discipline
- local execution and validation posture

These are real assets and should be **kept and hardened**, not discarded.

### 7.2 Current weaknesses

The main architectural weakness is not the absence of orchestration.
It is the continued risk of identity drift and incomplete shared substrate hardening across all future branches.

The platform still depends on strong discipline around:

- canonical session/job schema
- typed tools
- explicit workspace model
- permission system
- stable artifact contract
- sandboxed execution discipline
- strong code-outcome telemetry completeness
- connector and ingress standardization
- mission clarity across repo-facing documents

### 7.3 Practical interpretation

The correct architectural move is therefore:

- retain the control plane
- preserve and extend the shared runtime substrate
- normalize authority surfaces
- treat the completed local-autonomy work as foundation
- expand into broader autonomous-function branches without changing the backbone

## 8. Non-negotiable architecture principles

The system architecture should continue to enforce the following principles.

### 8.1 Local-first governed execution

Local execution is the default route for routine approved work whenever the current capability envelope allows it.

Other systems may:

- critique
- route
- benchmark
- supervise
- act as explicit escalation paths

But they may not silently displace the default local route.

### 8.2 Single substrate, many branches

Every subsystem must use the same:

- session/job schema
- tool model
- workspace rules
- permission system
- artifact contract
- validation/promotion posture

Branches may vary in tools, workflows, prompts, adapters, or domain logic.
They may **not** create new infrastructure backbones.

### 8.3 Open-source-first

Core runtime, orchestration, storage, retrieval, benchmarking, and platform services should be open-source-first unless a closed component adds narrow supervisory value without creating lock-in.

### 8.4 Evidence-gated evolution

Architectural claims must be backed by:

- artifacts
- benchmark evidence
- validation reports
- promotion gates
- runtime telemetry

### 8.5 Replaceability by design

No layer may assume permanent dependence on:

- a specific model provider
- a specific UI surface
- a specific tool protocol implementation
- a specific external service where a stable local abstraction can be preserved

### 8.6 Thin vertical slices

Usability and reliability outrank breadth.
The correct foundation proof was the developer assistant and local execution substrate on the shared runtime, not broad branch proliferation before governance maturity.

## 9. Architecture no-go rules

The following remain hard no-go rules.

- Do not replace the existing control plane before the shared runtime substrate is proven.
- Do not allow branches to create their own custom execution loops, storage conventions, or policy engines.
- Do not make Claude Code or Codex the default coding engine.
- Do not use closed-source dependencies on the critical path where a strong open alternative already exists.
- Do not promote release candidates without consolidated validation evidence.
- Do not allow tactical package completion to substitute for canonical architecture completion.
- Do not let the repo’s public or internal identity collapse back into “just a coding assistant repo.”

## 10. Target architecture overview

The platform target architecture is a seven-layer model.

### Layer 1 — Control plane

Responsibilities:

- stage manager
- qualification gates
- worker budget logic
- learning-loop integration
- benchmark governance
- high-level orchestration and release/progression logic

Disposition:

- keep existing control plane
- harden and normalize
- do not replace prematurely

### Layer 2 — Agent runtime

Responsibilities:

- typed tool system
- workspace controller
- permission engine
- sandbox executor
- session state
- retry loop discipline
- canonical command/execution interfaces

Disposition:

- this is the substrate that made the broader platform credible
- must remain the shared base for future branches

### Layer 3 — Inference and execution fabric

Responsibilities:

- internal inference gateway
- routing across local and optional heavier backends
- typed profiles
- retry/time budget management
- backend abstraction and telemetry
- local coding and execution support

Disposition:

- preserve the local-first path
- keep heavier external routes subordinate and explicit

### Layer 4 — Connector and action fabric

Responsibilities:

- reusable connector boundaries
- internal and external system integration
- event intake
- action dispatch
- MCP-compatible tool boundaries where appropriate

Disposition:

- this is required for the broader autonomous-function mission
- future branches should consume this layer rather than inventing one-off connectors

### Layer 5 — Retrieval and memory

Responsibilities:

- repository understanding
- semantic retrieval
- trusted patterns
- failure memory
- run memory / execution context memory
- future broader state and capability memory

Disposition:

- use adopted components where strong fit exists
- keep local ownership of policy and higher-level memory behavior

### Layer 6 — Evaluation and governance

Responsibilities:

- validation matrix
- benchmark suite
- run reports
- promotion decisions
- autonomy scorecard
- regression and readiness evidence

Disposition:

- must remain repo-owned as a differentiating governance capability
- do not outsource release/promotion evidence as a black box

### Layer 7 — Domain modules and user-facing surfaces

Responsibilities:

- developer assistance
- business workflows
- media control and related media branches
- athlete analytics
- meetings/office automation
- environmental intelligence
- inventory and capability mapping
- communication workflows
- repair/restoration and other specialist branches
- dashboard, voice, chat, and remote operator surfaces

Disposition:

- branches sit on top of the shared runtime and connector fabric
- domain behavior belongs in tools, workflows, prompts, adapters, and branch logic
- domain branches may not introduce new backbone infrastructure

## 11. Domain branch rule

Documented domain branches may adopt external libraries, APIs, or services where useful, but they may not create their own:

- execution loop
- permission model
- artifact schema
- promotion process
- storage convention where the shared substrate already has the correct layer

This rule is what keeps the architecture from fragmenting as the roadmap grows.

## 12. Authoritative phase scheme

The reconciled phase numbering from the architecture handoff remains the authoritative architecture progression.

### Phase 0 — Governance freeze and source-of-truth cleanup
### Phase 1 — Local runtime hardening for governed local execution
### Phase 2 — Shared agent runtime substrate
### Phase 3 — Developer assistant and local execution MVP
### Phase 4 — Self-sufficiency uplift and workflow reuse
### Phase 5 — Qualification, regression, and local-autonomy gate closure
### Phase 6 — Controlled expansion after local platform convergence

## 13. Migration map summary

The migration logic from earlier repository state to target architecture remains:

- keep and harden: stage manager, manager scripts, promotion manifest, checkpoint/resume orchestration
- keep then normalize: benchmark, qualification, and promotion surfaces
- keep then wrap later: learning-loop artifacts and priors
- wrap behind gateway: ad hoc local execution route
- replace: shell/profile-driven model selection with typed gateway profiles
- wrap and reconcile: current partial job metadata into canonical session/job schema
- formalize: slice handoff into machine-readable execution-control package
- replace: repo-local artifact writes with dedicated artifact root and artifact bundle
- formalize: connector/workflow boundaries so future domain branches do not drift
- defer: broad external escalation and branch proliferation until runtime and governance contracts are stable

## 14. Authority surfaces and source-of-truth model

The architecture needs clear authority boundaries.

### 14.1 Promotion manifest
Role: release authority and qualification / promotion truth

### 14.2 CMDB-lite and later CMDB authority
Role: architecture/runtime authority for phase, subsystem inventory, runtime contracts, migration map, model profiles, artifact root, adapter posture, waivers, autonomy scorecard, and hardware capability posture

### 14.3 Handoff documents
Role: explanatory and planning support, not final machine authority

### 14.4 Roadmap docs
Role: canonical planning and governance layer for execution planning, item grouping, metrics, and impact analysis

## 15. Role policy for coding systems

### 15.1 Local coding path
Allowed role:
- default first-attempt implementation path for routine approved work where current capability allows

Disallowed role:
- must not redefine the broader platform mission as purely coding-focused

### 15.2 Aider
Allowed role:
- tactical execution engine and controlled edit adapter

Disallowed role:
- may not become the architecture backbone

### 15.3 Claude Code
Allowed role:
- architecture review
- policy enforcement
- critique
- planning
- explicit exceptional escalation
- Apple/Xcode or environment-constrained execution where appropriate

Disallowed role:
- must not silently author routine implementation code and have that counted as local autonomy

### 15.4 Codex
Allowed role:
- control-window review
- bounded execution under the same runtime/governance rules

Disallowed role:
- may not create a parallel planning or execution backbone

## 16. Core software adoption posture

The architecture follows an adopt/build/hybrid discipline.

### 16.1 Default build posture
Build locally in-repo when the capability is differentiating system logic, especially for:
- inference and execution control
- permission system
- artifact contract
- validation and promotion packet generation
- autonomy scorecard and reporting
- higher-level governance logic
- shared connector and workflow policy

### 16.2 Default adopt posture
Adopt strong open-source components when the capability is commodity infrastructure and a good fit already exists.

### 16.3 Major adopted or conditionally adopted software
The current architecture direction recognizes major systems such as:
- Ollama
- OpenHands
- Aider
- MCP
- Plane
- future storage, retrieval, sandboxing, and catalog systems where justified

These are tracked in `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`.

## 17. External system families the platform will integrate with

Beyond core platform software, the system is expected to integrate with major external application families rather than rebuild all of them.

Examples include:
- media and entertainment systems
- home and environment systems
- health and athlete systems
- AI and coding surfaces
- communication and scheduling systems
- business workflow and screening systems

## 18. Feature and branch vision

The system is intended to grow into multiple branch families on top of the closed governed substrate.

### 18.1 Core platform family
- local execution and governance substrate
- roadmap/governance control
- operational evidence and validation
- inventory/capability awareness
- control center and no-code interaction shells
- connector and ingress fabric

### 18.2 Domain branch family
Potential or active branch families include:
- media control and media lab
- athlete analytics
- environmental monitoring and automation
- spreadsheet/document-to-app conversion
- embedded hardware and electrical design support
- language/translation tools
- woodworking/project-planning tools
- automotive repair/restoration intelligence
- meeting intelligence and office automation
- communication screening and business operations workflows

### 18.3 UI and display family
The user-facing vision includes:
- master control center
- no-code primary interface
- tablet-specialized control dashboards
- ambient themed household dashboards
- voice/chat/text ingress surfaces
- remote operator continuity surfaces

These should all be served from the same architecture, not from disconnected mini-systems.

## 19. Architecture relationship to roadmap

The roadmap exists to drive this architecture toward completion.

That means:
- roadmap items should map back to this architecture master
- grouped execution should favor shared architectural touch surfaces
- roadmap metrics should be architecture-aware
- impact analysis should refer to affected systems and file families
- external integrations should be cataloged and phase-aware

The roadmap is therefore downstream of the architecture, even though it governs execution planning.

## 20. Immediate architectural priorities

The immediate priorities after post-convergence are:

1. preserve source-of-truth surfaces and clean authority boundaries
2. preserve the governed local-execution substrate
3. standardize connector and ingress/action fabric
4. expand into business, personal, operational, and domain workflows without architectural drift
5. keep hardware capability, validation, and operating posture explicit

## 21. Current architecture-to-operations direction

The current practical direction for operations and governance is now:

- repo docs remain canonical for architecture, governance, and roadmap planning
- the platform is operated as a governed local-execution system in post-convergence mode
- external systems are tracked in a dedicated integration catalog
- hardware capability and constraints are treated as a first-class operating truth surface
- future CMDB adoption remains phase-gated and must not displace practical governed execution work prematurely

## 22. Document maintenance rules

To prevent the architecture from becoming fragmented again:

1. update this document when the core platform direction changes
2. do not let branch-specific docs silently redefine core architecture
3. treat superseded handoffs as historical inputs once their durable content is folded here
4. keep the external-app catalog and roadmap docs aligned to this architecture master
5. keep mission/scope and operating-context docs aligned to this architecture master
6. when a new major subsystem is introduced, update this document first or in the same change set

## 23. Bottom-line shorthand

If the architecture needs to be summarized in one directive:

> Build and preserve the governed shared runtime first. Keep the existing control plane. Use local coding autonomy as an enabling substrate, not the whole mission. Reuse one connector and execution fabric across business, personal, operational, and development workflows. Expand without changing the backbone.
