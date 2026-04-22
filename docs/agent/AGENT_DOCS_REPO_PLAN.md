# Agent Docs Repo Plan

## Purpose

This document defines the highest-value persistent repo documentation layer for execution systems such as Claude Code and Codex CLI.

The purpose is to reduce token waste, reduce ambiguity, and reduce repeated reasoning by giving execution systems stable, high-signal repo memory.

## Primary design rules

1. Keep root operating files concise.
2. Move detailed content into modular docs.
3. Prefer structured rules and checklists over long narrative prose.
4. Point to canonical roadmap docs instead of duplicating them.
5. Record repeated mistakes and gotchas once in repo docs instead of restating them in prompts.

## Proposed file set

### Root execution-system files
- `CLAUDE.md`
- `AGENTS.md`

### Modular agent docs
- `docs/agent/project-overview.md`
- `docs/agent/architecture-summary.md`
- `docs/agent/commands.md`
- `docs/agent/file-scope-rules.md`
- `docs/agent/validation-order.md`
- `docs/agent/known-failures.md`
- `docs/agent/roadmap-canonical-paths.md`

### Optional scoped rules
- `.claude/rules/roadmap.md`
- `.claude/rules/runtime.md`
- `.claude/rules/docs.md`
- `.claude/rules/artifacts.md`

## Recommended content by file

### `CLAUDE.md`
Use for:
- project purpose
- top-level execution posture
- canonical docs to read first
- critical do/do-not rules
- imports to modular docs if supported

### `AGENTS.md`
Use for:
- local agent operating rules
- repo-specific workflow conventions
- validation expectations
- artifact and file-scope rules
- roadmap canonical-path references

### `docs/agent/project-overview.md`
Use for:
- short repo/system purpose
- main priorities
- high-level subsystem map

### `docs/agent/architecture-summary.md`
Use for:
- execution-facing architecture summary
- major subsystem boundaries
- trust boundaries
- key dependencies

### `docs/agent/commands.md`
Use for:
- build commands
- test commands
- lint/format commands
- schema/artifact checks
- frequently used targeted validations

### `docs/agent/file-scope-rules.md`
Use for:
- additive-first rule
- append-only preferences where relevant
- forbidden files or directories
- high-risk directories
- migration posture

### `docs/agent/validation-order.md`
Use for:
- changed-file checks first
- schema parse checks
- narrow tests next
- broader checks only when justified
- rollback threshold

### `docs/agent/known-failures.md`
Use for:
- repeated mistakes
- environment gotchas
- flaky commands
- wrong directories
- naming pitfalls
- anything annoying to repeat manually

### `docs/agent/roadmap-canonical-paths.md`
Use for:
- where `ROADMAP_MASTER.md` lives
- where `ROADMAP_INDEX.md` lives
- where `EXECUTION_PACK_INDEX.md` lives
- when to use execution packs
- what counts as incomplete roadmap intake

## Rollout order

### Phase 1
Create:
- `CLAUDE.md`
- `AGENTS.md`
- `docs/agent/project-overview.md`
- `docs/agent/commands.md`
- `docs/agent/roadmap-canonical-paths.md`

### Phase 2
Create:
- `docs/agent/architecture-summary.md`
- `docs/agent/file-scope-rules.md`
- `docs/agent/validation-order.md`
- `docs/agent/known-failures.md`

### Phase 3
Add:
- `.claude/rules/` scoped rules where proven useful
- maintenance process for keeping command docs and known-failures current

## Validation rules

Before treating this package as advanced:

- confirm all referenced files and repo paths actually exist
- confirm the docs do not conflict with canonical roadmap docs
- confirm command docs only include real commands
- confirm root files remain concise and do not duplicate large modular content

## Relationship to roadmap

This repo plan is the concrete implementation plan for:

- `RM-DEV-009` — Agent operating-docs and persistent execution-memory package

It also supports:

- `RM-DEV-005`
- `RM-DEV-008`
- `RM-CORE-003`
- `RM-GOV-004`
- `RM-AUTO-002`
