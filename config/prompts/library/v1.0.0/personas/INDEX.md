# System Prompt Persona Library — v1.0.0 Index

Deliverable: D-17-121
Effective: 2026-05-05

## Persona Table

| ID | File | Intended Model | Task Class | Use Case |
|----|------|----------------|------------|----------|
| `voice-fast` | [voice-fast.md](voice-fast.md) | qwen2.5-coder:14b | C0 | Home Assistant voice; one-sentence answers; <2s budget |
| `deliberate-analysis` | [deliberate-analysis.md](deliberate-analysis.md) | qwen2.5-coder:32b | C1 | Architecture decisions; trade-off analysis; doctrine authoring |
| `code-review` | [code-review.md](code-review.md) | qwen2.5-coder:32b | C2 | Security + correctness review; severity-tagged findings; verdict |
| `decomposition-planner` | [decomposition-planner.md](decomposition-planner.md) | qwen2.5-coder:32b | C3 | WP-NN decomposition; PMP+ITIL labels; surface-back gates |

## Selection Guidance — When to Use Which

**Use `voice-fast` when:**
- The answer is a single fact, command, or status
- Response must arrive in under 2 seconds (voice pipeline, HA automation)
- No cross-file synthesis required

**Use `deliberate-analysis` when:**
- The decision has architectural consequences
- Multiple source files must be read and synthesized
- Trade-offs must be documented before a recommendation
- You are authoring a doctrine, runbook, or architecture-facts entry

**Use `code-review` when:**
- Reviewing a diff or patch before merge
- Auditing a script or service config for security issues
- You need a severity-classified finding list with a PASS/FAIL verdict

**Use `decomposition-planner` when:**
- A deliverable is too large to execute in a single step
- You need a sequenced WP plan with surface-back gates
- You want time estimates and dependency ordering before starting work

## Quick Decision Tree

```
Is the answer a single sentence?
  → YES → voice-fast
  → NO:
      Is the input code or a diff?
        → YES → code-review
        → NO:
            Is the goal a plan (not prose, not code review)?
              → YES → decomposition-planner
              → NO → deliberate-analysis
```

## Versioning Policy

This library uses semantic versioning. The version directory (`v1.0.0/`) is the source of truth.

| Change type | Version bump | Example |
|-------------|-------------|---------|
| New persona added | MINOR: `v1.0.0 → v1.1.0` | Add `debugging-specialist` persona |
| Persona behavior rules changed (non-breaking addition) | MINOR | Add new behavior rule to existing persona |
| Persona output format changed in a way that breaks existing callers | MAJOR: `v1.0.0 → v2.0.0` | Change front-matter schema, rename `id` field |
| Typo fix, clarification, example update | PATCH: `v1.0.0 → v1.0.1` | Fix example in code-review.md |

**How to add a persona (MINOR bump):**
1. Create `v1.1.0/personas/<new-id>.md` from the existing template (copy v1.0.0/personas/ contents)
2. Update `v1.1.0/personas/INDEX.md` with the new row
3. Update `bin/persona_loader.py` — the `"latest"` alias should point to the new version directory
4. Add a row to the `docs/architecture-facts/local-llm-stack-doctrine.md` persona table

**How to make a breaking change (MAJOR bump):**
- All consumers of `load_persona()` must be updated before retiring the old version directory
- Old version directory is retained for at least one phase before removal
- ADR required if breaking change affects litellm routing configuration

## Relationship to Existing Operator-Dispatch Personas

The files in `v1.0.0/personas/` (this directory) are **API-surface personas** — structured for injection via `bin/persona_loader.py` into litellm system prompt fields or Open WebUI custom personas.

The files at `v1.0.0/` root level (01-voice-fast.md, 02-deliberate-analysis.md, etc.) are **operator-dispatch templates** — human-readable Goose/Aider dispatch guides authored for D-17-90/D-17-53.

The two surfaces are complementary: the operator-dispatch files explain *how to use* each persona for manual dispatch; the API-surface files in `personas/` provide the *system prompt text* for programmatic injection.
