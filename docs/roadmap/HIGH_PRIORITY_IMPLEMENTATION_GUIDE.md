# High-Priority Roadmap Implementation Guide

This document enriches the critical and high-value roadmap items with implementation guidance, OSS candidates, best-practice posture, and handoff-friendly notes.

## Authority and use

- Read `docs/roadmap/ROADMAP_MASTER.md` first for strategic priority and pull order.
- Read `docs/roadmap/ROADMAP_INDEX.md` for normalized item IDs.
- Use this document as the implementation-oriented companion for high-priority work.
- When a roadmap item is promoted for execution, the selected task should cite both the roadmap ID and the relevant section in this guide.

## Primary enrichment rule

The most important enriched roadmap cluster is the local development assistant and local autonomy stack:

- `RM-DEV-005` — Local autonomy uplift, OSS intake, and Aider reliability hardening
- `RM-DEV-003` — Bounded autonomous code generation
- `RM-DEV-002` — Dual-model inline QC coding loop for the developer assistant
- `RM-INTEL-001` — Open-source watchtower with update alerts and adoption recommendations
- `RM-DEV-004` — Embedded firmware assistant for Nordic and ESP platforms
- `RM-DEV-001` — Add Xcode and Apple-platform coding capability to the developer assistant

These items should be treated as the highest-value implementation cluster in the roadmap.

## Dedicated execution packs

The following items now have dedicated execution packs and should use those first for deep execution handoffs:

- `RM-DEV-003` → `docs/roadmap/RM-DEV-003_EXECUTION_PACK.md`
- `RM-INTEL-001` → `docs/roadmap/RM-INTEL-001_EXECUTION_PACK.md`

---

## 1. RM-DEV-005 — Local autonomy uplift, OSS intake, and Aider reliability hardening

### Objective
Build the shortest safe path to a stronger local home developer assistant with reduced dependence on Claude Code and Codex.

### Adopt-first shortlist

#### Ollama
- Role: default local inference engine and model host
- Use for: local-first model serving, profile pinning, API-backed routing
- Official docs: https://docs.ollama.com/
- Notes:
  - keep Ollama as the default local model manager
  - pin named model profiles by task class
  - avoid untracked model churn between runs

#### Aider
- Role: repo-map-aware edit adapter inside the governed runtime
- Use for: bounded code editing, repo-aware context, patch generation
- Official docs: https://aider.chat/docs/repomap.html
- Notes:
  - use Aider for repo-aware edits, not as the system backbone
  - preserve narrow-file task boundaries
  - keep Aider behind canonical runtime contracts

#### Model Context Protocol (MCP)
- Role: standard protocol boundary for external tools and context sources
- Use for: tool exposure, context resources, prompt surfaces
- Official spec: https://modelcontextprotocol.io/specification/
- Notes:
  - prefer MCP over bespoke tool bindings where practical
  - version-pin the protocol revision used in the stack
  - design tools/resources/prompts with explicit capability boundaries

#### OpenHands Software Agent SDK
- Role: reference implementation source for agent runtime/tool/workspace patterns
- Use for: typed agent composition, tool organization, local or ephemeral workspace patterns
- Repo: https://github.com/OpenHands/software-agent-sdk
- SDK docs: https://docs.all-hands.dev/sdk
- Notes:
  - mine for patterns, not for architecture replacement
  - do not let OpenHands become a parallel backbone unless later explicitly adopted
  - local runtime mode should be treated as high-trust only and used carefully

#### Qdrant
- Role: semantic memory / retrieval layer
- Use for: task memory, failure memory, repo-pattern retrieval, embedding-backed recall
- Docs: https://qdrant.tech/documentation/
- Notes:
  - prefer structured metadata on top of vector storage
  - design collections by task class and provenance
  - preserve explicit links back to artifacts and repos

#### gVisor
- Role: isolation/sandboxing layer for untrusted or model-generated execution
- Use for: defense-in-depth around code execution and tool runs
- Docs: https://gvisor.dev/docs
- Notes:
  - use for risky or untrusted code paths
  - avoid assuming all local execution is equally safe
  - pair with explicit workspace, permission, and artifact boundaries

#### SWE-bench
- Role: benchmark harness and external performance reference
- Use for: evaluation of local coding performance against real software tasks
- Site: https://www.swebench.com/SWE-bench/
- FAQ: https://www.swebench.com/SWE-bench/faq/
- Notes:
  - prefer SWE-bench Verified or a bounded internal subset for repeatable evaluation
  - track pass rate, retries, rescue/manual escalation, and repeated-failure recurrence
  - use it as evidence, not marketing

#### Continue
- Role: optional complementary surface for checks and CI-oriented enforcement
- Repo/org: https://github.com/continuedev
- Notes:
  - treat as complementary, not core
  - strongest use is source-controlled checks and workflow assistance
  - do not allow it to displace the core runtime roadmap

### Required best-practice posture
- Ollama-first local execution
- Aider as adapter/transport, not backbone
- MCP for tool boundaries
- benchmark-driven improvement, not anecdotal tuning
- sandbox risky execution with gVisor or equivalent isolation
- maintain artifact-complete runs with explicit input/output traces
- separate model improvement from wrapper/routing improvement

### Immediate implementation order
1. lock shortlist and version pins
2. harden inference gateway and profile registry
3. harden workspace/artifact path contracts
4. move Aider into governed adapter role
5. add repo-pattern memory + failure memory
6. benchmark with SWE-bench-style task set
7. burn down external-agent dependence with scorecards

### Key artifacts to require
- adoption shortlist registry
- model profile registry
- adapter policy doc
- autonomy scorecard
- failure-memory schema
- benchmark result snapshots
- routing-policy history

### Common failure modes to guard against
- local model churn with no pinned profile
- Aider operating as an ad hoc side channel
- no benchmark evidence for claimed improvements
- retrieval/memory with weak provenance
- unsafe local execution without sandbox or policy boundaries
- measuring wrapper gains but calling them model gains

---

## 2. RM-DEV-003 — Bounded autonomous code generation

### Objective
Allow the system to autonomously execute safe, bounded coding work with explicit scope and evidence rules.

### Recommended posture
- re-use the same runtime substrate as `RM-DEV-005`
- require bounded file scope, validation order, rollback rule, and artifact outputs
- default to additive-first changes where possible

### Best practices
- use repo-map context before proposing edits
- require explicit task anchors and allowed-file lists
- run changed-file validation first, then broader checks only when needed
- treat benchmark and regression evidence as promotion gates

### Dependencies
- `RM-DEV-005`
- governed runtime contracts
- artifact-complete execution and validation paths
- dedicated execution pack: `docs/roadmap/RM-DEV-003_EXECUTION_PACK.md`

---

## 3. RM-DEV-002 — Dual-model inline QC coding loop

### Objective
Use a secondary review/check path to catch failures early without reintroducing uncontrolled paid-agent dependence.

### Recommended posture
- QC layer should be optional, bounded, and measurable
- treat QC as evidence-producing review, not vague second opinion
- compare first-pass local result versus corrected result

### Best practices
- preserve machine-readable review outputs
- classify review findings by failure type
- store accepted QC fixes in failure-memory or prompt-pack inputs

### Suggested tools/patterns
- repo-map-aware editor on the primary path
- benchmark-backed review categories
- memory store for repeated QC findings

---

## 4. RM-INTEL-001 — Open-source watchtower with update alerts and adoption recommendations

### Objective
Continuously discover, triage, and score OSS candidates that can strengthen the local stack without creating drift.

### Recommended posture
- treat this as an adoption-governance service, not a generic news feed
- maintain a scored shortlist tied to roadmap IDs
- preserve removal strategy and integration cost for every candidate

### Best practices
- capture license, maintenance activity, release cadence, API stability, deployability, removability
- separate “interesting” from “adoptable now”
- tie recommendations back to specific roadmap needs

### Strong initial watch list
- Ollama
- Aider
- MCP ecosystem
- OpenHands SDK and related agent-runtime patterns
- Qdrant
- gVisor
- SWE-bench ecosystem
- Continue

### Dedicated execution pack
- `docs/roadmap/RM-INTEL-001_EXECUTION_PACK.md`

---

## 5. RM-DEV-004 — Embedded firmware assistant for Nordic and ESP platforms

### Objective
Extend the local development assistant into embedded and firmware workflows without breaking the core dev-assistant architecture.

### Recommended posture
- keep firmware work under the same runtime, artifact, and evaluation rules
- preserve target-board, SDK, and toolchain metadata in artifacts
- do not let firmware support create a parallel execution path

### Best practices
- split board support by family (Nordic vs ESP)
- treat flashing/build/test/probe steps as explicit tools
- capture hardware/board config in machine-readable form

### Dependencies
- `RM-DEV-005`
- hardware inventory and CMDB linkage where applicable

---

## 6. RM-DEV-001 — Add Xcode and Apple-platform coding capability to the developer assistant

### Objective
Support Apple-platform development tasks under the same bounded runtime model.

### Recommended posture
- preserve explicit platform/toolchain profiles
- keep builds, tests, simulator actions, and signing-sensitive actions clearly separated
- avoid hidden mutation of local Apple development state

### Best practices
- separate codegen from project-signing or release operations
- use explicit scheme/target selection in tasks
- treat simulator, test, and archive actions as separate execution classes

---

## 7. RM-GOV-001 / RM-GOV-002 / RM-GOV-003 — Roadmap governance and integrity system

### Objective
Preserve one canonical roadmap system with grouped execution logic, CMDB linkage, and anti-duplication control.

### Recommended posture
- all new items enter `ROADMAP_INDEX.md`
- `ROADMAP_MASTER.md` must change when ranking or pull order changes
- dated sync files are allowed for detailed normalization, but not as replacements for the index

### Best practices
- keep roadmap IDs stable
- prefer grouped execution when shared-touch work reduces churn
- preserve explicit lineage between roadmap IDs, issues, package docs, and PRs

---

## 8. RM-INV-002 / RM-INV-003 — Inventory and procurement intelligence

### Objective
Make the system understand owned assets and future purchases well enough to support smarter operations and procurement.

### Recommended posture
- tie inventory to capability mapping and procurement recommendations
- preserve product identity, compatibility, provenance, and confidence metadata
- use real availability and historical pricing evidence where possible

### Best practices
- separate owned-asset truth from market listing data
- keep human-reviewable procurement recommendations
- maintain compatibility linkage for hardware-specific purchasing

---

## 9. Domain expansion packages (high-value, but secondary to local dev assistant)

These remain important, but they should generally follow the local-development-assistant work unless they directly unlock it.

### Website generation (`RM-DOCAPP-002`)
Recommended posture:
- adopt OSS builder/editor surfaces rather than building a full page builder
- preserve deployable artifact bundles, SEO audits, and analytics configuration

### 3D capture and 3D asset library (`RM-SHOP-002`, `RM-SHOP-003`)
Recommended posture:
- separate capture/reconstruction from asset reuse/sourcing
- preserve geometry provenance and reuse lineage

### Media control extensions (`RM-MEDIA-003`, `RM-MEDIA-004`)
Recommended posture:
- keep advisory/reporting safe by default
- preserve explicit approval for destructive cleanup actions
- keep sports-event acquisition in the media-control branch, not as a separate architecture

---

## Handoff rule for execution systems

Whenever a roadmap item is handed off for execution, the handoff should include:

- roadmap ID
- title
- why it matters
- exact pull priority status
- adopt-first shortlist (if applicable)
- required best practices
- expected artifacts
- validation order
- rollback rule
- forbidden drift patterns

This guide exists to make those handoffs faster and more consistent.
