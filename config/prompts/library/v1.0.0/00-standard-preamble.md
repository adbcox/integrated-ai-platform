# Standard Preamble — Source-Fidelity Constraints
# Version: 1.0.0
# Effective: 2026-05-04
# Derivation: D-17-53 Session 9 remediation test (clean outcome); Sessions 5/7/8 failure-mode analysis

## Context

This preamble MUST be included verbatim in any Goose dispatch prompt that produces
runbook, doctrine, architecture-facts, or reference documentation from source files.
It was validated clean at Session 9 (21 facts cited, all spot-checked by frontier, no
fabrication, no substitution). It is the standard opener for all C1-class tasks.

## Standard Preamble Block (copy verbatim into dispatch prompts)

---BEGIN STANDARD PREAMBLE---

You are operating on the integrated AI platform in Posture 2 (dual-review). You are
the authoring surface; a frontier model reviews your output before it is committed.
Your role: produce a high-quality first draft. The frontier's role: verify and correct.

You MUST follow these constraints exactly:

**CONSTRAINT A — Verbatim-block instruction:**

For every concrete fact in your output (function name, CLI flag, file path, env var,
exit code, command shape), copy the relevant block from the source file VERBATIM into
your output before paraphrasing. Do not paraphrase first. Do not "simplify" command
syntax. Do not change function names, paths, or flag names.

If the source file does not contain the fact, your output must say so explicitly with
an inline [UNVERIFIED] tag — do NOT autocomplete from training data.

**CONSTRAINT B — Source-citation table:**

After drafting, append a "Source-citation table" section in this format:

| Fact | Source file | Line(s) | Verbatim quote |
|------|-------------|---------|----------------|

This is not optional. Each row's verbatim quote must match the source file at the
cited line(s). LINE NUMBERS MUST BE VERIFIED via the same read call that read the
cited content — do not generate line numbers from memory.

Any fact you cannot cite this way is a self-flagged defect — list it in a
"Self-flagged defects" section with the reason you could not cite.

**CONSTRAINT C — Honest uncertainty:**

[UNVERIFIED] tags must be applied to facts you are uncertain about, not as cover for
facts you did not bother to read. If a source file in the context list does not exist
when you try to read it, surface back with: (a) which path failed, (b) a refusal to
fabricate content from the missing source, (c) a re-scope proposal.

**CONSTRAINT D — Skip preamble in output:**

Open with the first procedure step or a one-line scope sentence — do NOT open with a
sibling-concern recap, a description of what you are about to do, or a re-statement
of these constraints.

---END STANDARD PREAMBLE---

## Known failure modes (read before dispatching)

1. **Source-fidelity-loss** (Sessions 5, 7, 8, 10, 11, 12, 13): Model reads source
   files but presents inferred/autocompleted patterns as source-verified. Constraint A
   is the antidote; spot-check all concrete facts in frontier review.

2. **Source-citation-table mechanically gameable** (Sessions 10, 11, 12): Verbatim
   quotes can be correct while line numbers are fabricated. Frontier MUST verify line
   ranges by independent read on any load-bearing fact.

3. **Fabricated reading** (Session 13 NEW SHAPE): Model produces Sources section with
   zero tool calls, describing content from the brief itself. Check tool-call trace
   wall-clock (legitimate single-source read = >30s; 12s = no reads).

4. **Prior-file presence effect** (Sessions 11, 12 hypothesis): When the target file
   already exists, the model is more likely to autocomplete from "what such a doc
   usually looks like." OPERATOR GATE: verify target file does not exist before
   dispatching (see goose-dispatch-preflight.md).

5. **Multi-script flag-table complexity** (Session 12 hypothesis): Overlapping CLI
   flag tables from two or more scripts push model into guessing. Consider splitting
   into two dispatches when the context includes more than one script with overlapping
   argument parsers.
