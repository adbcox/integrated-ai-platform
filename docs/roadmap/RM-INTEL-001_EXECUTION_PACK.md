# RM-INTEL-001 — Execution Pack

## Title

**RM-INTEL-001 — Open-source watchtower with update alerts and adoption recommendations**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- High-priority implementation guide: `docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md`
- Closely related items: `RM-DEV-005`, `RM-GOV-001`, `RM-GOV-002`

## Objective

Continuously discover, triage, score, and recommend open-source tools, repos, and ecosystem changes that can improve the integrated AI platform without creating architecture drift.

This is not a generic software-news feed. It is an **adoption-governance and technical-intelligence system** for strengthening the local stack.

## Why this matters

Without a structured OSS watchtower, adoption happens reactively and inconsistently.

With it, the system can:

- find viable OSS building blocks earlier,
- reduce redundant custom building,
- track which tools are mature enough to adopt,
- align recommendations with actual roadmap items,
- and support the local development assistant with fresher, evidence-backed options.

## Required outcome

The watchtower must produce:

- a scored candidate registry,
- update and release alerts for tracked tools,
- roadmap-linked adoption recommendations,
- removal and fallback posture for each candidate,
- and an evidence-backed shortlist for current implementation needs.

## Non-goals

Do not turn this item into:

- an unfiltered RSS/links collector,
- a “latest tool hype” dashboard with no roadmap relevance,
- a second roadmap system,
- or a source of unaudited changes entering the stack automatically.

## Primary tracked ecosystem for the local development assistant

The first watch list should strongly focus on the local-development-assistant stack:

- Ollama
- Aider
- MCP ecosystem
- OpenHands Software Agent SDK
- Qdrant
- gVisor
- SWE-bench ecosystem
- Continue

## Adopt-first software and patterns

### Ollama
- Docs: https://docs.ollama.com/
- API intro: https://docs.ollama.com/api
- Quickstart: https://docs.ollama.com/quickstart
- Modelfile reference: https://docs.ollama.com/modelfile

#### Why it is relevant here
Ollama is the default local model-serving layer for the roadmap. It supports local API usage, model customization with Modelfiles, and reports usage metrics that can support operational benchmarking. The watchtower should track version changes, new API features, model-management changes, and integration surfaces relevant to the local stack. citeturn280140search0turn280140search1turn280140search8

### Aider
- Repo map docs: https://aider.chat/docs/repomap.html

#### Why it is relevant here
Aider is a key edit adapter candidate. The watchtower should track meaningful changes in repo-map behavior, edit workflows, local-model support, and integration guidance that could affect local coding reliability. citeturn280140search4

### MCP
- Official spec: https://modelcontextprotocol.io/specification/

#### Why it is relevant here
MCP is a moving protocol surface. The watchtower should track protocol revision changes, capability model changes, and new ecosystem tools/servers that materially improve the local assistant or tool boundary design. citeturn280140search10turn280140search11

### OpenHands Software Agent SDK
- Repo: https://github.com/OpenHands/software-agent-sdk
- SDK docs: https://docs.all-hands.dev/sdk
- Local runtime caution: https://docs.all-hands.dev/openhands/usage/runtimes/local

#### Why it is relevant here
OpenHands SDK offers modular agent/runtime/tool/workspace patterns and supports local or ephemeral workspaces. The watchtower should track releases, examples, security posture, and pattern relevance, especially because the local runtime documentation explicitly warns that it lacks sandbox isolation. citeturn432185search1turn432185search3turn432185search0

### Qdrant
- Collections: https://qdrant.tech/documentation/concepts/collections/
- Payloads: https://qdrant.tech/documentation/concepts/payload/
- Vectors: https://qdrant.tech/documentation/manage-data/vectors/

#### Why it is relevant here
Qdrant supports vectors plus JSON payloads and payload indexing, which makes it useful for provenance-aware semantic memory. The watchtower should track feature changes that matter for metadata-rich memory and retrieval design. citeturn957525search0turn957525search1turn957525search3

### gVisor
- Docs: https://gvisor.dev/docs

#### Why it is relevant here
gVisor provides an isolation boundary for risky execution. The watchtower should track runtime compatibility, isolation model changes, and integration guidance for OCI/container usage. citeturn957525search2

### SWE-bench
- Overview: https://www.swebench.com/SWE-bench/
- FAQ: https://www.swebench.com/SWE-bench/faq/

#### Why it is relevant here
SWE-bench is the external benchmark reference for software engineering tasks. The watchtower should track dataset changes, new subsets, evaluation guidance, and benchmark methodology changes that affect local-model measurement. citeturn280140search2turn280140search7

### Continue
- Product site: https://www.continue.dev/
- Docs: https://docs.continue.dev/

#### Why it is relevant here
Continue is useful as a complementary checks and workflow surface, particularly around source-controlled AI checks on pull requests. The watchtower should track capabilities that matter for enforcement, CI, and quality-control integration without letting it replace the core runtime plan. citeturn957525search4turn957525search5

## Recommended architecture posture

### Core rule
The watchtower should recommend adoption **only in the context of roadmap needs**.

### Preferred flow
1. collect candidate or update signals
2. normalize source metadata
3. score candidate or change
4. map to relevant roadmap IDs
5. produce recommendation class
6. record decision and rationale
7. surface alerts or next actions

## Candidate record schema

Every tracked candidate should have at least:

- name
- category
- source URL / repo URL
- license
- maintenance activity signal
- release cadence signal
- integration role
- roadmap linkage
- adoption class (`adopt-now`, `evaluate`, `watch`, `reject`)
- removal/fallback posture
- security/sandbox sensitivity
- notes

## Suggested output artifacts

- `artifacts/watchtower/candidates/latest.json`
- `artifacts/watchtower/alerts/latest.json`
- `artifacts/watchtower/recommendations/latest.md`
- `artifacts/watchtower/decisions/history.jsonl`

## Scoring dimensions

### Required
- license fit
- maintenance activity
- API/protocol stability
- local deployability
- integration cost
- removability
- architecture fit
- security/sandbox risk
- benchmark or evidence relevance

### Optional but recommended
- community depth
- documentation quality
- CI/test maturity
- upgrade churn risk
- vendor/control risk

## Recommendation classes

### Adopt now
Use when a candidate is mature, clearly roadmap-aligned, and low enough risk to move into shortlist or execution planning.

### Evaluate
Use when promising but not ready for direct adoption. Requires bounded spike or comparison work.

### Watch
Use when relevant but not urgent, immature, or not yet evidence-backed enough.

### Reject
Use when misaligned, too risky, too unstable, or clearly redundant.

## Alert types

The watchtower should be able to emit at least:

- major release alert
- security/reliability concern alert
- new relevant OSS project alert
- benchmark/dataset methodology change alert
- protocol/spec revision alert
- adoption shortlist change recommendation

## Best practices
- tie every recommendation to a roadmap ID
- record why a candidate was accepted or rejected
- preserve removal strategy before adopting
- separate “interesting” from “should enter stack now”
- prefer official docs and primary repos for facts
- avoid broad adoption based on hype, stars, or trend alone

## Common failure modes
- too many tracked projects with no ranking discipline
- recommendations that are not tied to roadmap needs
- adopting tools that bypass the canonical runtime
- losing history of why a tool was rejected or deferred
- mixing release alerts with adoption decisions without scoring

## Immediate implementation sequence

### Phase 1 — candidate registry
Build the candidate record schema and initial shortlist registry.

### Phase 2 — roadmap linkage
Require every candidate to map to one or more roadmap IDs.

### Phase 3 — update/alert collection
Add a feed or polling layer for tracked sources and releases.

### Phase 4 — recommendation engine
Score candidate changes and emit adoption/watch/reject recommendations.

### Phase 5 — decision memory and audit trail
Store final decisions, rationale, and fallback posture.

## Required governance rules

- no tool enters the critical path without a recorded decision
- every recommendation must include integration role and removal posture
- protocol and runtime candidates must be checked for architecture drift
- local-runtime or unsandboxed execution options require explicit caution labels

## Handoff rule

When this item is pulled for execution, the handoff should include:

- roadmap ID: `RM-INTEL-001`
- initial watch list
- candidate schema
- scoring dimensions
- output artifacts
- alert types
- decision classes
- roadmap linkage rule
- anti-drift constraints

## Recommended first milestone

Create the first version of the candidate registry and populate it with the local-development-assistant shortlist:

- Ollama
- Aider
- MCP
- OpenHands SDK
- Qdrant
- gVisor
- SWE-bench
- Continue

Then add decision classes and roadmap linkage before building broader alerting.
