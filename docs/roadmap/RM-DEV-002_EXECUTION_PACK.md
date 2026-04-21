# RM-DEV-002 — Execution Pack

## Title

**RM-DEV-002 — Dual-model inline QC coding loop for the developer assistant**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-DEV-003`

## Objective

Add a bounded, evidence-producing quality-control loop that reviews or challenges local coding outputs before promotion.

## Why this matters

This improves safety and correctness without making paid-agent dependence the default path. It helps convert review findings into reusable failure memory.

## Required outcome

- optional but measurable QC pass on bounded coding tasks
- machine-readable review findings
- classification of review failures by type
- storage of accepted corrections in memory or prompt-pack inputs

## Recommended posture

- keep QC bounded and explicit
- treat QC as evidence, not vague second opinion
- compare first-pass local result versus reviewed/corrected result
- prefer local or low-cost secondary review paths before paid escalation

## Suggested tools and patterns

- repo-aware primary edit path via Aider-like adapter
- benchmark-backed review categories
- structured finding schema with provenance
- optional MCP-exposed review tools/resources

## Required artifacts

- review result record
- finding classification output
- accepted correction summary
- memory update record

## Best practices

- review changed-on-disk results, not just proposed diffs
- keep review prompts/task specs narrow
- store repeated review failures as reusable patterns
- separate style issues from correctness/safety issues

## Common failure modes

- unbounded second-pass review scope
- no storage of accepted QC fixes
- paying for review on every task without measuring value
- review feedback that is not actionable or machine-readable

## Recommended first milestone

Implement a structured review result schema and memory write-back path for bounded coding tasks.
