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

The integrated AI platform is a **local-first AI development and operations platform** whose primary near-term purpose is to become a highly reliable home developer assistant that can increasingly operate through a local Ollama-first coding path while preserving strict governance, evidence, and anti-drift controls.

The most important architectural decision is:

> **Keep the existing control plane, add a shared runtime substrate, and make Ollama-first execution the default path for routine approved coding work.**

The system is therefore **not** being rebuilt as a generic chatbot shell, a pure PM tool, or a loose collection of domain apps.

It is being built as a layered platform with:

- a retained control plane
- a new shared runtime substrate
- a stable inference gateway
- standardized artifact and validation contracts
- a governance and roadmap system with explicit impact modeling
- domain branches that sit on top of the shared substrate instead of inventing their own backbones

## 4. System vision

### 4.1 Product-level vision

The intended end state is a unified, local-first, extensible AI platform that can:

- act as a highly capable home developer assistant
- manage and reason about code, systems, infrastructure, and assets
- provide dashboard- and tablet-based control surfaces
- integrate with external systems rather than rebuilding all commodity capabilities
- expand into domain branches such as media control, athlete analytics, environmental intelligence, inventory/capability mapping, repair/restoration, and specialized planning tools

### 4.2 Strategic vision

The system is intended to evolve from a local coding substrate into a broader operations and intelligence platform **without** changing architectural backbone each time a new feature branch is added.

That means:

- new branches must reuse the same runtime substrate
- execution evidence must remain comparable across branches
- external integrations must be cataloged and deliberate
- roadmap work must be architecture-led rather than idea-led

### 4.3 User experience vision

At the user-facing layer, the system is expected to mature into:

- a master control center
- a no-code or low-code tile/click-based interface
- room-aware ambient tablet dashboards
- specialized domain applications built on the same substrate
- a governance-aware development environment that can move from roadmap item to execution to validation with less manual churn

## 5. Primary program objective

The most important near-term objective remains:

> **Strengthen the local development assistant so the system becomes a highly reliable home developer assistant with minimal dependence on Claude Code or Codex for routine coding work.**

This priority outranks broadening feature count.

In practical terms, the platform should prioritize:

1. shared runtime completion
2. local Ollama-first coding reliability
3. artifact completeness and promotion evidence
4. developer assistant MVP through the shared substrate
5. self-sufficiency uplift
6. controlled expansion into domain branches

## 6. What the system is not

To prevent drift, it is important to say what the system is **not**.

It is not:

- a roadmap board with some AI features attached
- a loose collection of scripts and models
- a Claude Code wrapper with local tools on the side
- a custom rebuild of every commodity platform component
- a collection of domain apps each with its own execution loop
- a system that treats architecture handoffs, tactical packages, and roadmap execution as equivalent authority layers

## 7. Current architectural reading

Based on the revised target architecture handoffs and control-window adoption packet, the current platform has real strengths but also clear gaps.

### 7.1 Current strengths

The platform already has a credible control plane foundation, including:

- stage and manager orchestration
- checkpoint/resume behavior
- worker budget logic
- benchmark and qualification surfaces
- promotion surfaces
- learning-loop artifacts
- trusted external pattern intake

These are real assets and should be **kept and hardened**, not discarded.

### 7.2 Current weaknesses

The main architectural weakness is not the absence of orchestration.
It is the absence of a first-class runtime substrate with:

- canonical session/job schema
- typed tools
- explicit workspace model
- permission system
- stable artifact contract
- sandboxed execution discipline
- strong code-outcome telemetry completeness

### 7.3 Practical interpretation

The correct architectural move is therefore:

- retain the control plane
- add the shared runtime substrate beneath it
- normalize authority surfaces
- stop counting tactical pre-substrate work as proof of branch maturity

## 8. Non-negotiable architecture principles

The system architecture should continue to enforce the following principles.

### 8.1 Ollama-first execution

Ollama is the default code-generation engine for routine first-attempt coding work.

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
The correct first proof is the developer assistant on the shared runtime, not broad branch proliferation.

## 9. Architecture no-go rules

The following remain hard no-go rules.

- Do not replace the existing control plane before the new runtime substrate is proven.
- Do not allow branches to create their own custom execution loops, storage conventions, or policy engines.
- Do not make Claude Code or Codex the default coding engine.
- Do not use closed-source dependencies on the critical path where a strong open alternative already exists.
- Do not promote release candidates without consolidated validation evidence.
- Do not allow direct Aider-to-Ollama coupling to harden into a permanent architecture pattern.
- Do not allow tactical package completion to substitute for canonical architecture completion.

## 10. Target architecture overview

The platform target architecture is a six-layer model.

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

- this is the most important missing substrate
- must be implemented before broad domain expansion

### Layer 3 — Inference fabric

Responsibilities:

- internal inference gateway
- routing across Ollama and optional heavier backends
- typed profiles
- retry/time budget management
- backend abstraction and telemetry

Disposition:

- build the gateway locally in-repo
- Ollama remains mandatory as the default route
- vLLM remains optional for heavier shared runs or repeatable evals

### Layer 4 — Retrieval and memory

Responsibilities:

- RepoMap/repository understanding
- symbol extraction
- semantic retrieval
- trusted patterns
- failure memory
- run memory / execution context memory

Disposition:

- use adopted components where strong fit exists
- keep local ownership of policy and higher-level memory behavior

### Layer 5 — Evaluation and governance

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

### Layer 6 — Domain modules

Responsibilities:

- developer assistance
- media control and related media branches
- athlete analytics
- meetings/office automation
- environmental intelligence
- inventory and capability mapping
- repair/restoration and other specialist branches

Disposition:

- branches sit on top of the shared runtime
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

Primary objective:

- lock ADRs
- lock execution-control package
- lock autonomy scorecard
- define version truth
- define architecture/runtime authority surfaces

### Phase 1 — Local runtime hardening for Ollama-first execution

Primary objective:

- stabilize local route
- introduce inference gateway
- standardize workspace layout and artifact persistence
- eliminate implicit shell/profile dependencies in application logic

### Phase 2 — Shared agent runtime substrate

Primary objective:

- canonical session/job schema
- typed tools
- workspace controller
- permission engine
- sandbox execution
- artifact bundle and conformance tests

### Phase 3 — Developer assistant MVP

Primary objective:

- prove the shared substrate through repo intake, repo understanding, patch/test/retry flow, result packaging, and repeatable benchmark behavior

### Phase 4 — Ollama self-sufficiency uplift

Primary objective:

- task-class prompt packs
- failure memory
- success prediction
- repo-pattern memory
- critique injection
- routing improvements

### Phase 5 — Qualification, regression, and local-autonomy gate closure

Primary objective:

- close promotion-governance gaps
- raise code-outcome coverage
- emit unified validation artifact
- formalize exception handling
- begin CMDB pilot only after coding stability is real

### Phase 6 — Controlled expansion after local coding independence

Primary objective:

- add controlled adapters
- broaden into non-coding branches
- preserve Ollama-first local route and shared runtime contract

## 13. Migration map summary

The migration logic from current repository state to target architecture remains:

- keep and harden: stage manager, manager scripts, promotion manifest, checkpoint/resume orchestration
- keep then normalize: benchmark, qualification, and promotion surfaces
- keep then wrap later: learning-loop artifacts and priors
- wrap behind gateway: ad hoc local Ollama execution route
- replace: shell/profile-driven model selection with typed gateway profiles
- wrap and reconcile: current partial job metadata into canonical session/job schema
- formalize: slice handoff into machine-readable execution-control package
- replace: repo-local artifact writes with dedicated artifact root and artifact bundle
- wrap through runtime: direct patch/test flows through current local tooling
- keep temporarily, formal adapter later: Aider local router / transport
- defer: Codex adapter and broad domain branch expansion until the runtime contracts are stable

## 14. Authority surfaces and source-of-truth model

The architecture needs clear authority boundaries.

### 14.1 Promotion manifest

Role:

- release authority
- qualification / promotion truth

### 14.2 CMDB-lite and later CMDB authority

Role:

- architecture/runtime authority for phase, subsystem inventory, runtime contracts, migration map, model profiles, artifact root, adapter posture, waivers, and autonomy scorecard

Practical posture:

- begin with CMDB-lite / repo-owned registry
- do not let full CMDB adoption outrun runtime maturity
- transition to a broader authoritative CMDB only after the platform is stable enough to benefit from it

### 14.3 Handoff documents

Role:

- explanatory and planning support
- not final machine authority

### 14.4 Roadmap docs

Role:

- canonical planning and governance layer
- architecture-derived execution planning, item grouping, metrics, and impact analysis

## 15. Role policy for coding systems

### 15.1 Ollama

Allowed role:

- default first-attempt coding engine

Disallowed role:

- may not be casually bypassed on routine approved work

### 15.2 Aider

Allowed role:

- temporary transport now
- controlled edit adapter later

Disallowed role:

- may not become the backbone

### 15.3 Claude Code

Allowed role:

- architecture review
- policy enforcement
- critique
- planning
- explicit exceptional escalation

Disallowed role:

- must not silently author routine implementation code and have that counted as local autonomy

### 15.4 Codex

Allowed role:

- future optional adapter under the same runtime contracts

Disallowed role:

- may not create a parallel coding path

## 16. Core software adoption posture

The architecture follows an adopt/build/hybrid discipline.

### 16.1 Default build posture

Build locally in-repo when the capability is differentiating system logic, especially for:

- inference gateway
- permission system
- artifact contract
- validation and promotion packet generation
- autonomy scorecard and reporting
- higher-level governance logic

### 16.2 Default adopt posture

Adopt strong open-source components when the capability is commodity infrastructure and a good fit already exists.

### 16.3 Major adopted or conditionally adopted software

The current architecture direction recognizes the following major systems as part of the platform environment or approved adoption path:

- Ollama — primary local model lifecycle and execution surface
- vLLM — optional heavier serving backend
- OpenHands Software Agent SDK concepts/components — selective workspace/tool model inspiration or reuse
- Aider RepoMap and controlled edit workflows — adopted as adapter-level capability, never backbone
- MCP — standard external tool boundary
- Qdrant — semantic retrieval/vector store
- gVisor — first-line sandboxing
- Firecracker — optional later stronger isolation
- SWE-bench — benchmark harness
- Backstage — later developer portal/software catalog
- GLPI — preferred authoritative CMDB once phase maturity allows
- CloudQuery — read-only enrichment around the authoritative CMDB
- i-doit — conditional alternative if relationship-heavy ITIL needs dominate
- Temporal — deferred/conditional durable workflow backbone only if the current manager proves insufficient
- Plane — operational planning/execution layer on top of repo-doc canonical roadmap

These are now also tracked in `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`.

## 17. External system families the platform will integrate with

Beyond core platform software, the system is expected to integrate with major external application families rather than rebuild all of them.

### 17.1 Media and entertainment systems

- Plex
- Sonarr
- Radarr
- Prowlarr
- managed playback endpoints such as NVIDIA Shield, Samsung TV, and Apple TV classes
- later reference surfaces such as external streaming catalogs where legally supported integrations exist

### 17.2 Home and environment systems

- Home Assistant as the bridge for device/entity control
- environmental sensors and purifier integrations through Home Assistant where applicable
- later networking telemetry integrations where justified

### 17.3 Health and athlete systems

- Strava and future athlete-data or analytics systems
- unresolved athlete-data integrations should remain explicit until verified, rather than disappearing from planning

### 17.4 AI and coding surfaces

- ChatGPT/OpenAI surfaces for workflow support and optional API use
- Claude Code as controlled supervisory surface
- later optional Codex adapter under the shared runtime rules

## 18. Feature and branch vision

The system is intended to grow into multiple branch families once the coding substrate is mature.

### 18.1 Core platform family

- local-first developer assistant
- roadmap/governance control
- operational evidence and validation
- inventory/capability awareness
- control center and no-code interaction shells

### 18.2 Domain branch family

Potential or active branch families include:

- media control and media lab
- athlete analytics
- environmental monitoring and automation
- spreadsheet-to-webapp/document-to-app conversion
- embedded hardware and electrical design support
- language/translation tools
- woodworking/project-planning tools
- automotive repair/restoration intelligence
- meeting intelligence and office automation

### 18.3 UI and display family

The user-facing vision includes:

- master control center
- no-code primary interface
- tablet-specialized control dashboards
- ambient themed household dashboards

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

The immediate priorities remain:

1. freeze source-of-truth surfaces and clean authority boundaries
2. define or confirm ADR set for session/job schema, tool system, workspace contract, inference gateway, permission model, artifact bundle, and autonomy scorecard
3. stabilize internal inference gateway with Ollama-first policy
4. implement shared runtime substrate
5. prove the developer assistant MVP on the substrate
6. close telemetry/promotion/local-autonomy evidence gaps
7. only then broaden into non-coding branches and heavier governance/catalog systems

## 21. Current architecture-to-operations direction

The current practical direction for operations and governance is now:

- repo docs remain canonical for roadmap and architecture planning
- Plane becomes the operational roadmap/planning layer, not the canonical architecture source
- external systems are tracked in a dedicated integration catalog
- future CMDB adoption remains phase-gated and must not displace runtime work prematurely

## 22. Document maintenance rules

To prevent the architecture from becoming fragmented again:

1. update this document when the core platform direction changes
2. do not let branch-specific docs silently redefine core architecture
3. treat superseded handoffs as historical inputs once their durable content is folded here
4. keep the external-app catalog and roadmap docs aligned to this architecture master
5. when a new major subsystem is introduced, update this document first or in the same change set

## 23. Bottom-line shorthand

If the architecture needs to be summarized in one directive:

> Build the shared runtime first. Keep the existing control plane. Make Ollama the default coding engine behind a stable inference gateway. Implement typed tools, workspaces, permission enforcement, sandboxed execution, and artifact completeness before broadening the system. Prove the architecture with the developer assistant, then expand without changing the substrate.
