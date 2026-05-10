# System Prompt Library — Catalog
# Version: 1.0.0
# Effective: 2026-05-04 (initial); 2026-05-11 (consolidation merge from D-17-11)

## Provenance note (2026-05-11)

Presets 01-04 updated 2026-05-11 per the consolidation audit §14 —
instructional content is the union of original (D-17-90) and Library
A's `docs/system-prompts/modes/` (D-17-11) with operator-arbitrated
conflict resolutions baked in (deliberate-analysis opening posture,
code-review severity taxonomy with nuance note, decomposition
output-path cardinality with coupling exception). Preset 08
(capability-permission) is new — migrated from
`docs/system-prompts/modes/capability-permission.md` (D-17-23) as
part of the same consolidation. See
`docs/_audit/system-prompts-consolidation-audit-2026-05-11.md` for
the full merge provenance + per-pair semantic comparison.

Library A's `docs/system-prompts/tiers/` (T1-T4 capability classes)
and `consumers/` (descriptive integration prose) remain canonical at
their original location — this catalog covers the runtime preset
layer only. The two libraries together form the system-prompt
substrate; modes/personas live here, tiers/consumer-prose live there.

# Original derivation: D-17-90 (T1 system prompt library); D-17-53 session analysis (Sessions 1–13)

## Library layout

config/prompts/library/
└── v1.0.0/
    ├── CATALOG.md                  ← this file (index + routing guide)
    ├── 00-standard-preamble.md     ← verbatim preamble for C1 tasks
    ├── 01-voice-fast.md            ← Persona: voice-fast (C0 tasks; merged with D-17-11 2026-05-11)
    ├── 02-deliberate-analysis.md   ← Persona: deliberate-analysis (C1 tasks; merged with D-17-11 2026-05-11)
    ├── 03-code-review.md           ← Persona: code-review (C2 tasks; merged with D-17-11 2026-05-11)
    ├── 04-decomposition.md         ← Persona: decomposition (C3 tasks; merged with D-17-11 2026-05-11)
    ├── 05-persona-routing.yaml     ← Litellm/Open WebUI routing config
    ├── 06-aider-tier1-presets.md   ← Tier 1 routing presets + Claude Code/Codex refusal preamble (D-17-95)
    ├── 07-deepseek-verifier-prompt.md ← DeepSeek dual-loop verifier prompt (D-17-110)
    └── 08-capability-permission.md ← Persona: capability-permission (META; D-17-23 slot, migrated 2026-05-11)

## Persona selection guide

| If the task is… | Persona | File |
|----------------|---------|------|
| Quick lookup / one-liner / ≤50 lines, ≤1 source | voice-fast | 01-voice-fast.md |
| Runbook / doctrine / architecture-facts from 2+ sources | deliberate-analysis | 02-deliberate-analysis.md |
| Code review / diff analysis / security audit | code-review | 03-code-review.md |
| Breaking a large deliverable into subtask specs | decomposition | 04-decomposition.md |
| Pre-grant Flavor C/D permissions (META composition) | capability-permission | 08-capability-permission.md |

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
