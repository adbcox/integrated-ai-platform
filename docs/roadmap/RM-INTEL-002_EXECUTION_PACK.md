# RM-INTEL-002 — Execution Pack

## Title

**RM-INTEL-002 — Verified OSS capability harvest and compatibility validation for the local development assistant**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-DEV-003`, `RM-INTEL-001`

## Objective

Aggressively identify, verify, classify, and integrate open-source codebases, helper repos, protocols, code-intelligence substrates, structural-search tools, memory layers, sandboxing layers, and evaluation harnesses that can materially improve the local development assistant without rebuilding those capabilities from scratch.

## Why this matters

This item exists because there is already a large amount of public work that can improve the local agent. The goal is to stop treating local-agent intelligence uplift as if every capability must be built greenfield.

## Required outcome

- verified candidate matrix for the local development assistant stack
- explicit adopt-now / evaluate / watch / reject classes
- comparison against current architecture and already-adopted shortlist
- compatibility notes and likely integration roles
- rejection notes for tools likely to cause duplication, lock-in, or drift

## Non-goals

Do not turn this into:

- a hype list,
- a duplicate of `RM-INTEL-001` without deeper validation,
- or a generic “cool tools” tracker with no direct linkage to the local development assistant.

## Candidate classes to evaluate

- coding-agent runtimes and CLIs
- repo/context intelligence layers
- structural search and codemod tools
- memory/retrieval layers
- sandboxing and controlled-execution layers
- benchmarks/evaluation harnesses
- code search/indexing engines
- static analysis/fix engines

## Mandatory evaluation method

For every candidate, record at least:

- name
- category
- official docs or repo
- license
- core capability
- direct relevance to `RM-DEV-005` / `RM-DEV-003`
- overlap with already-tracked tools
- integration risks
- recommendation class (`adopt-now`, `evaluate`, `watch`, `reject`)
- why

## Already-central stack to compare against

The repo is already centered on a shortlist that includes:

- Ollama
- Aider
- MCP
- OpenHands Software Agent SDK
- Qdrant
- gVisor
- SWE-bench
- Continue

New candidates should be measured against this baseline rather than discussed in isolation.

## Recommended posture

- prefer official docs and primary repositories
- reject tools that would replace the architecture without strong evidence
- favor components that can be inserted as helpers or focused subsystems
- preserve one local-first, privacy-aware stack rather than a pile of partially overlapping agents

## Required artifacts

- candidate matrix
- recommendation report
- compatibility/conflict report
- follow-on shortlist for actual implementation work

## Suggested artifact paths

- `artifacts/watchtower/verified-candidates/latest.json`
- `artifacts/watchtower/verified-candidates/latest.md`
- `artifacts/watchtower/compatibility/latest.md`

## Best practices

- score candidates against real roadmap needs
- explicitly reject shiny but duplicative tools
- separate “better primitive” from “replace the backbone”
- preserve evidence for why something was rejected
- prefer components that can raise intelligence, context quality, search quality, safety, or evaluation coverage without architecture drift

## Common failure modes

- recommending whole new agent stacks when a smaller helper would do
- duplicating existing memory/search/eval plans
- ignoring privacy or local-execution constraints
- failing to distinguish mature tools from archived or moved projects
- letting research sprawl without producing a usable shortlist

## Recommended first milestone

Produce the first verified candidate matrix and recommendation report focused on the local development assistant, then feed the adopt-now and evaluate classes back into `RM-DEV-005`, `RM-DEV-003`, and `RM-INTEL-001`.
