# System Prompt Library — Catalog
# Version: 1.0.0
# Effective: 2026-05-04
# Derivation: D-17-90 (T1 system prompt library); D-17-53 session analysis (Sessions 1–13)

## Library layout

config/prompts/library/
└── v1.0.0/
    ├── CATALOG.md                  ← this file (index + routing guide)
    ├── 00-standard-preamble.md     ← verbatim preamble for C1 tasks
    ├── 01-voice-fast.md            ← Persona: voice-fast (C0 tasks)
    ├── 02-deliberate-analysis.md   ← Persona: deliberate-analysis (C1 tasks)
    ├── 03-code-review.md           ← Persona: code-review (C2 tasks)
    ├── 04-decomposition.md         ← Persona: decomposition (C3 tasks)
    ├── 05-persona-routing.yaml     ← Litellm/Open WebUI routing config
    └── 06-aider-tier1-presets.md   ← Tier 1 routing presets + Claude Code/Codex refusal preamble (D-17-95)

## Persona selection guide

| If the task is… | Persona | File |
|----------------|---------|------|
| Quick lookup / one-liner / ≤50 lines, ≤1 source | voice-fast | 01-voice-fast.md |
| Runbook / doctrine / architecture-facts from 2+ sources | deliberate-analysis | 02-deliberate-analysis.md |
| Code review / diff analysis / security audit | code-review | 03-code-review.md |
| Breaking a large deliverable into subtask specs | decomposition | 04-decomposition.md |

## Task class mapping

| Class | Description | Persona |
|-------|-------------|---------|
| C0 | Short-answer, single-source lookup | voice-fast |
| C1 | Multi-source synthesis → prose output | deliberate-analysis |
| C2 | Code/diff as input → structured critique | code-review |
| C3 | Complex planning → subtask specs | decomposition |

## Standard preamble usage

The standard preamble (00-standard-preamble.md) is MANDATORY for C1 tasks.
It is the verbatim text validated clean at D-17-53 Session 9.

Quick inclusion rule:
- C0 (voice-fast): do NOT include standard preamble (adds overhead without benefit)
- C1 (deliberate-analysis): ALWAYS include preamble verbatim (Constraints A+B+C+D)
- C2 (code-review): include Constraints C+D only (optional; see 03-code-review.md)
- C3 (decomposition): do NOT include standard preamble

## Versioning convention

- Semver: MAJOR.MINOR.PATCH
- MAJOR: preamble content changes (new constraints, removed constraints)
- MINOR: new persona added, routing config updated
- PATCH: typo/clarification in existing persona, no behavior change
- Version directory is the source of truth; symlink latest/ → latest version if
  tooling requires stable paths

## Cross-references

- Doctrine: docs/architecture-facts/local-prompt-library-doctrine.md
- Work-routing classifier: docs/architecture-facts/work-routing-doctrine.md (D-17-95)
- Failure-mode analysis source: docs/phase-17/d-17-53/ (sessions 1–13)
- Goose capability boundary: docs/architecture-facts/goose-capability-boundary.md
- Anthropic prompting guide: https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
- Pre-flight gate: docs/runbooks/goose-dispatch-preflight.md
- Tier 1 presets + Claude Code/Codex refusal preamble: 06-aider-tier1-presets.md
