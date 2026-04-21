# RM-DEV-005 — Execution Pack

## Title

**RM-DEV-005 — Local autonomy uplift, OSS intake, and Aider reliability hardening**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Implementation companion: `docs/roadmap/HIGH_PRIORITY_IMPLEMENTATION_GUIDE.md`
- Closely related items: `RM-DEV-003`, `RM-DEV-002`, `RM-INTEL-001`, `RM-AUTO-001`

## Objective

Continuously improve the local coding stack so the integrated AI platform becomes capable of handling routine coding and adjacent development work with minimal dependence on Claude Code or Codex.

This is the **program-critical, pull-first** roadmap item and the main force multiplier for the entire home developer assistant.

## Why this matters

Without `RM-DEV-005`, most other roadmap items remain harder to execute, slower to validate, and more dependent on outside systems.

With it, the platform can:

- improve local first-attempt coding quality,
- make Aider reliable as a governed adapter,
- systematize OSS adoption,
- preserve artifact-complete evidence,
- and reduce paid-agent dependence over time.

## Required outcome

The system must be able to:

- serve local coding tasks through a stable local inference path,
- route bounded work through governed execution adapters,
- preserve repo-pattern and failure memory,
- benchmark progress against fixed task cohorts,
- and show measurable burn-down of external-agent dependence.

## Non-goals

Do not treat this item as permission to:

- replace governance with ad hoc agent autonomy,
- let Aider become the backbone of the system,
- claim success without benchmark evidence,
- or broaden local execution faster than safety and validation support.

## Adopt-first stack

### Ollama
- Docs: https://docs.ollama.com/
- API: https://docs.ollama.com/api
- Modelfile: https://docs.ollama.com/modelfile

### Aider
- Repo-map docs: https://aider.chat/docs/repomap.html

### MCP
- Spec: https://modelcontextprotocol.io/specification/

### OpenHands Software Agent SDK
- Repo: https://github.com/OpenHands/software-agent-sdk
- SDK docs: https://docs.all-hands.dev/sdk
- Local runtime caution: https://docs.all-hands.dev/openhands/usage/runtimes/local

### Qdrant
- Docs: https://qdrant.tech/documentation/

### gVisor
- Docs: https://gvisor.dev/docs

### SWE-bench
- Overview: https://www.swebench.com/SWE-bench/
- FAQ: https://www.swebench.com/SWE-bench/faq/

### Continue
- Repo/org: https://github.com/continuedev
- Docs: https://docs.continue.dev/

## Architecture posture

### Core rule
Keep Ollama as the default local inference path and keep Aider inside the governed runtime as an edit adapter, not an independent side channel.

### Preferred flow
1. shortlist and version-pin candidate OSS components
2. harden inference gateway and profile registry
3. harden workspace and artifact-path rules
4. move edit execution behind governed contracts
5. add memory, replay, and critique layers
6. benchmark and score autonomy progress
7. widen local-first scope only when evidence supports it

## Mandatory workstreams

### 1. OSS intake and shortlist governance
Track candidates, licenses, maintenance, integration cost, removability, and roadmap linkage.

### 2. Inference gateway and profile hardening
Pin model profiles by task class and preserve measurable routing behavior.

### 3. Workspace and artifact-path hardening
Guarantee deterministic task directories, artifact outputs, and post-run evidence.

### 4. Aider adapter hardening
Keep repository-aware editing available, but under explicit runtime control and file-scope rules.

### 5. Failure memory and repo-pattern retrieval
Store repeated failures, successful fixes, and reusable repo patterns with provenance.

### 6. Benchmark and scorecard layer
Measure local progress against repeatable software-task cohorts and internal autonomy scorecards.

## Required artifacts

- adoption shortlist registry
- version pin registry
- model profile registry
- routing policy history
- failure-memory schema
- repo-pattern memory schema
- benchmark result snapshots
- autonomy scorecard
- external-dependence burn-down report

## Suggested artifact paths

- `artifacts/autonomy/shortlist/latest.yaml`
- `artifacts/autonomy/profiles/latest.yaml`
- `artifacts/autonomy/scorecards/latest.json`
- `artifacts/autonomy/benchmarks/latest.json`
- `artifacts/autonomy/memory/failures.jsonl`
- `artifacts/autonomy/memory/patterns.jsonl`

## Validation policy

### Required evidence
- local first-attempt success trend
- retry and rescue rates
- repeated-failure recurrence trend
- external-agent usage trend
- benchmark delta on fixed cohorts

### Rule
Do not claim system improvement based on qualitative impressions alone. Benchmark and artifact evidence are mandatory.

## Best practices

- Ollama-first by default
- Aider as adapter/transport, not backbone
- MCP for tool boundaries
- benchmark-driven promotion of autonomy
- gVisor or equivalent isolation for risky execution classes
- provenance-aware memory and retrieval
- explicit rollback, validation, and artifact rules for every execution path

## Common failure modes

- unpinned model churn
- weak artifact completeness
- Aider acting outside the runtime
- no distinction between wrapper gains and model gains
- over-expansion of local-first scope without evidence
- OSS adoption by hype instead of roadmap fit

## Immediate implementation sequence

### Phase 1 — shortlist and profile lock
Create the first adoption shortlist and pin initial local-model profiles.

### Phase 2 — governed runtime path
Harden workspace, artifact, and adapter boundaries.

### Phase 3 — memory and replay layer
Add failure memory, repo-pattern retrieval, and critique injection.

### Phase 4 — benchmark and scorecard closure
Measure local-first improvement and external dependence reduction.

### Phase 5 — task-class promotion
Promote additional task classes to local-first only when evidence supports it.

## Handoff rule

Every execution handoff for this item should include:

- roadmap ID: `RM-DEV-005`
- exact workstream being pulled
- allowed files / systems touched
- required artifacts
- validation order
- rollback rule
- benchmark/evidence update rule
- related roadmap IDs

## Recommended first milestone

Lock the shortlist and profile registry first, then produce the first governed execution path for bounded local coding with artifact-complete evidence.
