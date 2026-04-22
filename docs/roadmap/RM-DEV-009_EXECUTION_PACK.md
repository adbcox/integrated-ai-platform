# RM-DEV-009 — Execution Pack

## Title

**RM-DEV-009 — Agent operating-docs and persistent execution-memory package**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-DEV-008`, `RM-CORE-003`, `RM-GOV-004`, `RM-AUTO-002`

## Objective

Create the highest-value persistent repo documentation layer for execution systems so Claude Code, Codex CLI, and other agentic tools can operate with less ambiguity, less repeated reasoning, and lower token usage.

## Why this matters

A major source of waste in smaller execution models is repeated rediscovery of project purpose, commands, file-scope rules, validation order, and roadmap canonical paths. This package turns those repeated prompt costs into stable repo memory.

## Required outcome

- root execution-system control files
- imported or modular agent docs
- concise command reference
- architecture summary for execution systems
- file-scope and mutation rules
- validation-order rules
- known-failures / recurring gotchas document
- roadmap canonical-paths helper doc
- optional scoped rules or memory structure for execution systems where supported

## Grouped child outputs

This package should normally produce or govern files such as:

- `CLAUDE.md`
- `AGENTS.md`
- `docs/agent/project-overview.md`
- `docs/agent/architecture-summary.md`
- `docs/agent/commands.md`
- `docs/agent/file-scope-rules.md`
- `docs/agent/validation-order.md`
- `docs/agent/known-failures.md`
- `docs/agent/roadmap-canonical-paths.md`
- `.claude/rules/` entries where justified

## Recommended posture

- keep the root operating files concise
- move detailed content into imported or modular docs
- prefer structure and explicitness over narrative prose
- optimize for minimum ambiguity and minimum wasted tokens for smaller execution models
- do not duplicate canonical roadmap content; point to it cleanly

## Required artifacts

- agent-docs plan
- root control files or stubs
- modular agent-doc set
- scoped-rule plan where relevant
- validation that the docs are internally consistent and refer to live repo paths

## Best practices

- put only universal, always-relevant rules in root files
- split detailed content by topic
- keep command docs short and high-signal
- record repeated correction points in known-failures docs rather than re-prompting them every session
- preserve one canonical reference for roadmap paths and execution-pack usage

## Common failure modes

- giant root memory files that lower adherence
- duplicate instructions across many files
- architecture summaries that are too broad for execution use
- command docs that are outdated or incomplete
- agent docs that conflict with roadmap standards

## Recommended first milestone

Create the root control files, the modular `docs/agent/` package, and a minimal rules structure first, then validate that the files reference only live repo paths and canonical roadmap docs.
