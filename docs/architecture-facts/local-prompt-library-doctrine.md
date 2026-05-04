# Local Prompt Library Doctrine
# Deliverable: D-17-90 (T1 System Prompt Library)
# Status: ESTABLISHED 2026-05-04
# Chronicle: Finding 20 (Goose maturity unblock T1 — source-fidelity remediation)

## Purpose

This doctrine establishes the canonical location, versioning, and usage rules for the
platform's local system prompt library. The library encodes prompt-engineering lessons
from D-17-53 (Goose capability evaluation, Sessions 1–13) and provides ready-to-use
templates for Goose dispatch sessions.

## Canonical location

```
config/prompts/library/<SEMVER>/
```

Current version: `v1.0.0` (effective 2026-05-04)

The CATALOG.md file in each version directory is the index.

## Provenance

The library was derived from:

1. **D-17-53 session analysis (Sessions 1–13):** 13 Goose sessions evaluating C1-class
   runbook/doctrine drafting. Sessions 2, 4, 5, 6, 9 produced acceptable output;
   Sessions 7, 8, 10, 11, 12, 13 exhibited the "source-fidelity-loss" failure mode
   (model presents autocompleted patterns as source-verified).

2. **Session 9 remediation test:** The verbatim-block instruction (Constraint A) and
   source-citation table (Constraint B) were validated clean at Session 9: 21 facts
   cited, all spot-checked by frontier, no fabrication. This preamble became the
   standard preamble (00-standard-preamble.md).

3. **Sessions 10–13 recurrence analysis:** Despite Session 9's clean outcome, Sessions
   10–13 showed recurrence of the source-fidelity-loss pattern. Key insight: the
   source-citation-table mechanism (Constraint B) is mechanically sound but
   informationally gameable (verbatim quotes mask wrong line numbers). The standard
   preamble suppresses the most severe fabrication shape but does not eliminate it.
   Frontier review remains mandatory for C1 tasks.

4. **Anthropic prompting guide cross-reference:**
   https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/overview
   Specific guidance applied: role-priming (Posture 2 framing), explicit output format
   specification, chain-of-thought via source-citation table, explicit failure-mode
   signposting.

## The four personas

| Persona | Task class | Model | Preamble required |
|---------|-----------|-------|-------------------|
| voice-fast | C0 (quick lookup, ≤50 lines, ≤1 source) | qwen2.5-coder:14b | No |
| deliberate-analysis | C1 (runbook/doctrine, 2+ sources) | qwen3-coder:30b | Yes (mandatory) |
| code-review | C2 (diff/code critique) | qwen2.5-coder:7b | No (C+D only) |
| decomposition | C3 (subtask planning) | qwen3-coder:30b | No |

## Operator rules

1. **Always select a persona before dispatching.** Never dispatch without a persona
   selection. Unstructured dispatches are what produced Sessions 7/8/11/12/13 failures.

2. **For C1 (deliberate-analysis) tasks: run pre-flight gate.**
   ```bash
   TARGET="<output path>"
   test -f "$TARGET" && echo "GATE FAIL: exists" || echo "GATE PASS"
   ```
   See docs/runbooks/goose-dispatch-preflight.md for full protocol.

3. **For C1 tasks: include standard preamble verbatim.** Copy from
   config/prompts/library/v1.0.0/00-standard-preamble.md. Do not paraphrase. Do not
   add to or remove from the standard preamble without incrementing MAJOR version.

4. **Frontier review is MANDATORY for C1 tasks.** The model's source-citation table
   must be verified by independent reads, not trusted at face value. Any LOAD-BEARING
   fact (function name, CLI flag, file path, exit code) must be spot-checked.

5. **Do not dispatch to a model outside the routing config without documenting the
   deviation.** If T2 benchmark (D-17-91) identifies a better model for a task class,
   update 05-persona-routing.yaml and this doctrine before the next dispatch.

## Versioning rules

- Semver: MAJOR.MINOR.PATCH
- MAJOR: preamble content changes (any constraint addition, removal, or modification)
- MINOR: new persona added, routing config updated (model change, temperature change)
- PATCH: typo or clarification in existing persona (no behavior change)

Operators MUST NOT edit a version directory after it is committed. Create a new version
directory for any change. This preserves reproducibility: a dispatch log citing v1.0.0
can always recover the exact preamble used.

## Failure-mode registry

Derived from D-17-53 analysis. Consult before dispatching any C1 task.

| ID | Shape | Sessions | Mitigation |
|----|-------|----------|-----------|
| FM-01 | Source-fidelity-loss: autocomplete presented as source-verified | 5,7,8,10,11,12,13 | Constraint A (verbatim-block); frontier spot-check |
| FM-02 | Source-citation-table line-number fabrication | 10,11,12 | Independent read verification at frontier review |
| FM-03 | Fabricated reading (zero tool calls; sources described from brief) | 13 | Check tool-call trace wall-clock; 12s = no reads |
| FM-04 | Prior-file presence effect (existing target → autocomplete) | 11,12 | Operator pre-flight gate (target must not exist) |
| FM-05 | Multi-script flag-table complexity | 12 | Split dispatch when >1 script with overlapping args |
| FM-06 | [UNVERIFIED] misapplication (covers for unread, not for fabrications) | 11,12,13 | Frontier checks that unflagged concrete facts are verified |

## Relationship to Goose capability-boundary doctrine

The prompt library (D-17-90) is the T1 substrate. The Goose capability-boundary
doctrine (docs/architecture-facts/goose-capability-boundary.md) governs promotion
criteria. They are complementary:

- Capability-boundary doctrine: WHAT tasks Goose can attempt (posture + class gates)
- Prompt library: HOW to dispatch those tasks (persona selection + preamble inclusion)

A cell at Posture 2 (dual-review) for C1 tasks requires BOTH:
1. Capability-boundary promotion criterion (N=5 clean sessions gate)
2. Deliberate-analysis persona + standard preamble (this doctrine)

## Chronicle

- Finding 20 established: D-17-53 session analysis surfaced FM-01 through FM-06;
  Session 9 clean outcome validated Constraints A+B as partial remediation; Sessions
  10–13 recurrence established that frontier review remains mandatory indefinitely for
  C1 tasks regardless of preamble presence.
- D-17-90 completed: 2026-05-04. T1 substrate (library + doctrine) is the prerequisite
  that should have preceded D-17-53 (T3, Goose deployment). Retrospective delivery.

## Related-docs

- Work-routing classifier (Tier 1/2/3): `docs/architecture-facts/work-routing-doctrine.md` (D-17-95)
