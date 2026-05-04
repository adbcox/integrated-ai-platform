# Local model tier doctrine

**Status:** VERIFIED (2026-05-04, D-17-12 close)
**Origin:** D-17-12 — T3 model adoption gate (qwen3-coder + gemma2 benchmarks)
**Sibling chronicles:** `local-tool-calling.md`, `class-taxonomy.md`, `goose-capability-boundary.md`, `promotion-criteria.md`, `execution-surface-roles.md`

This doctrine captures the per-tier capability boundaries observed in the D-17-12 benchmark and the rules by which tier is selected for a given (class × surface) cell. It complements rather than supersedes `class-taxonomy.md`: the taxonomy says *what* the work is; this doctrine says *which model* runs it.

## What "tier" means in this repo

Tier is a `(model × host)` pairing. It is a *property of the model substrate*, not a property of the work. Tier sits on a different axis from:

- **Class** — work-shape (C1a/C1b/C2/.../C10) per `class-taxonomy.md`.
- **Surface** — execution runtime (Claude Code, Codex, Goose) per `execution-surface-roles.md`.
- **Cell** — `(surface × class)` per `promotion-criteria.md`.
- **Posture** — capability state of a cell (0/1/2/3) per `promotion-criteria.md`.

A tier choice answers: "given this class on this surface, which model runs the inference?" Tier and cell are independent — a Posture-1 cell may use any tier whose capability boundary admits the class; promotion-state lives on the cell, not on the tier.

## Tier inventory

| Tier | Model | Host | Hardware | Active params | Context window | Structured tool calls |
|---|---|---|---|---|---|---|
| **T1** | `qwen2.5-coder:32b` | Mac Mini Ollama | M4 Pro 48 GB | 32B (dense) | 32K | **No (inline JSON only)** |
| **T2** | `qwen2.5-coder:14b` | Mac Mini Ollama | M4 Pro 48 GB | 14B (dense) | 32K | **No (inline JSON only)** |
| **T3-A** | `gemma2:27b` | Mac Studio Ollama | M3 Ultra 96 GB | 27B (dense) | **8K** | **No (architecture-level)** |
| **T3-B** | `qwen3-coder:30b` | Mac Studio Ollama | M3 Ultra 96 GB | **3B active / 30B total (MoE)** | **256K** | **Yes** |

Mac Mini and Mac Studio host the Ollama daemons natively; no litellm hop, no Vault credential surface for these models (they are not external APIs).

## Capability boundaries by tier

### T1 — `qwen2.5-coder:32b` on Mac Mini

- **Strengths:** Most-trusted local baseline. Auto-grades: lc 0.86, refactor 1.00 (post-G1), tool-call correctness 0.91, agentic 0.62. Stable; behaves like a slow but reliable workhorse.
- **Limits:** Lowest agentic score among the four tiers. Tool-call output is *inline JSON in `response.message.content`*, not structured `response.message.tool_calls`. This boundary is qwen2.5-coder family-specific, NOT a generic Ollama issue (see `local-tool-calling.md` Finding 1.B).
- **Throughput band:** 9–14 tps.
- **Use when:** Conservative classes (C4 doctrine drafting where established baseline matters more than throughput); fallback for any class where T3-B is unavailable.

### T2 — `qwen2.5-coder:14b` on Mac Mini

- **Strengths:** Score parity with T1 on lc + refactor at ~2× T1 throughput. agentic materially better than T1 (0.71 vs 0.62) — likely because the smaller model is less prone to over-elaboration on agentic prompts.
- **Limits:** Same inline-JSON tool-call constraint as T1 (qwen2.5-coder family). 14B parameter ceiling shows up only on classes that don't appear in the benchmark (long-form synthesis, deep cross-file reasoning).
- **Throughput band:** 18–30 tps.
- **Use when:** C10 mechanical-script authoring; lightweight C1b/C2 work where round-trip latency matters.

### T3-A — `gemma2:27b` on Mac Studio

- **Strengths:** Strong agentic non-tool (0.79) at high tps (~35). Refactor 0.94 post-G1.
- **Limits:** Two hard limits.
  - **8K context ceiling.** Only 1/5 long-context benchmark tasks ran; the remaining 4 exceeded the window. Excludes T3-A from any class whose realistic input is multi-document or > 8K tokens.
  - **No tool support.** Ollama returns HTTP 400 `gemma2:27b does not support tools` — architecture-level limitation, not a serving stack issue.
- **Throughput band:** 24–35 tps.
- **Use when:** Short-input agentic work that does NOT need tool calls. Effectively a niche tier on this platform; T3-B dominates wherever both are eligible.

### T3-B — `qwen3-coder:30b` on Mac Studio

- **Strengths:** The platform's strongest local tier on every benchmarked workload. Auto-grades: lc 0.84, refactor 1.00 (post-G1), tool-call structured 0.93, agentic 0.83. **Only tier on this platform that emits structured `tool_calls`** (Finding 1.B). 256K native context window. MoE active-parameter ratio (3B active out of 30B) drives 3.4× T2 throughput at 30B-class capability.
- **Limits:** One hard limit, one observed limit.
  - **C1a SUSPENDED via the Goose surface (D-17-53).** This is a *cell* suspension (Goose × C1a), NOT a tier suspension. T3-B remains a candidate for non-Goose surfaces consuming it for C1a, subject to standard promotion-criteria gating from Posture 0.
  - **Source-fidelity loss in narrative-wrapped quotation tasks** observed in 4 of 5 post-remediation Goose sessions (D-17-53). Whether this is tier-bound or cell-bound has not been disambiguated; the benchmark refactor + tool-call cells did not exhibit it, and the failure-mode is class-specific to C1a.
- **Throughput band:** 49–102 tps.
- **Use when:** Default for any class where structured tool calls are needed (C3, C10-with-runtime-validation), or where high-throughput EXECUTION pays for itself (C1b, C2). Any future Phase-C migration on a benchmarked work-class would default here.

## Tier selection rules

The recommended-tier-by-class table is canonical in `docs/phase-17/d-17-12/WP07_DECISION_MATRIX_2026-05-04.md`. The rules below explain the *why* and how to apply them to classes not yet in the matrix.

### Rule 1 — Tool-call requirement is binary

If the class needs structured `tool_calls` (Goose dispatch, MCP-direct invocation, agentic loops with tool selection), only **T3-B** is eligible. T1/T2 emit inline JSON; T3-A doesn't tool-call. Adapter patterns exist for T1/T2 inline JSON (see `local-tool-calling.md`) but are EXECUTION-surface complexity, not capability — prefer T3-B when the surface permits.

### Rule 2 — Long-context is binary at 8K

If realistic input exceeds 8K tokens, **T3-A is excluded** by context window. T1/T2 (32K) and T3-B (256K) are eligible. For >32K inputs, T3-B is the only tier.

### Rule 3 — Capability-surface boundaries are not tier-selectable

Per `class-taxonomy.md` boundary clause, certain capabilities (Vault credential surface, SSH cross-host, root-equivalent shell exec) are excluded *regardless of tier*. Choosing a more capable tier does not unlock these — they are surface-level rails.

### Rule 4 — Throughput is a tiebreaker, never a primary axis

When two tiers are both eligible and both score-parity within auto-grade noise, prefer the higher-throughput tier (T3-B over T1/T2; T2 over T1). Throughput differences below 2× are not material — pick by other axes (established baseline, hand-grade trust, reviewer familiarity).

### Rule 5 — Cell suspensions don't propagate to tier exclusions

A cell suspension (e.g., Goose × C1a) excludes that *cell*, not the underlying tier from other cells. T3-B is suspended-via-Goose for C1a but available-via-Claude-Code-direct for any class where Claude Code dispatches to a local Ollama. The doctrine separates surface-bound failures from model-bound failures.

### Rule 6 — Auto-grade biases (G1/G2/G3) cannot flip tier ordering

Per `WP07_DECISION_MATRIX_2026-05-04.md` Decision Rule 5: hand-grade can shift per-workload scores by ±0.10–0.15 but the tier-vs-tier gaps in the matrix are larger than the bias band. If hand-grade *does* flip an ordering, that's evidence the auto-grader is broken on that workload, not evidence the tier ranking changed. Update the grader, re-run, then update tier doctrine — not the other way around.

## Falsified hypotheses (do not re-litigate without new evidence)

### Substrate-shape-correlation hypothesis — FALSIFIED at N=2

D-17-53 Sessions 9 + 12 produced opposite outcomes (clean / severe) on identical-shape substrate (Python + argparse, single-source, narrative). The hypothesis that "clean line-aligned blocks → clean output, structured-document substrate → severe-shape recurrence" cannot be reconciled with these two datapoints. Tier selection therefore does not include substrate-shape as an axis. Do not write tier rules of the form "T3-B for shape-X, T1 for shape-Y" without N≥3 evidence under the strengthened preamble.

### Single-clean-datapoint sampling-artifact hypothesis — STRENGTHENED

D-17-53 Session 13 deliberately matched Session 9's substrate shape and still produced severe-shape failure. The current best-explanation for the 4-of-5 post-remediation hit-rate on (Goose × C1a) is **sampling artifact** — Session 9 was a lucky draw. This is the basis for treating C1a as not-capable on the (Goose × T3-B) cell rather than substrate-dependent.

### qwen2.5-coder structured-tool-call regression — DISPROVEN as serving-stack issue

`local-tool-calling.md` Finding 1.B refines the original Finding 1: qwen3-coder:30b emits structured `tool_calls` cleanly under streaming on the same Ollama 0.22.1 daemon that returns inline JSON for qwen2.5-coder. The boundary is *model-side*, family-specific. Do not write tier rules of the form "newer Ollama version will fix T1 tool-call" — that hypothesis has been tested and refuted.

## Future-tier additions

When a new model lands a benchmark cell (e.g., a hypothetical larger qwen variant or post-cutoff gemma release):

1. Run the D-17-12 harness against the new cell. The harness lives at `docs/phase-17/d-17-12/harness/` and is reusable.
2. Add a row to the tier inventory above with the same column shape (active params, context window, structured tool calls).
3. Map per-workload verdicts (ADOPT / PARTIAL / REJECT) into the WP-07 matrix appendix.
4. Update per-class recommendations only if the new tier's gap-vs-incumbent exceeds the auto-grade noise floor.

The "T3-C" slot is available for the deferred cell-change branch (gemma2:27b on C1a, larger qwen variants on C1a) once that work-package opens.

## Cross-references

- **D-17-12 benchmark results:** `docs/phase-17/d-17-12/WP05_RESULTS_2026-05-03.md`, `WP06_SURFACE_BACK_2026-05-03.md`.
- **Per-class recommendation matrix (consumer-facing):** `docs/phase-17/d-17-12/WP07_DECISION_MATRIX_2026-05-04.md`.
- **Tool-call structured-emission boundary:** `local-tool-calling.md` Finding 1.B.
- **Class definitions + Phase tier:** `class-taxonomy.md`.
- **Cell promotion gating:** `promotion-criteria.md`.
- **Goose-specific cell state:** `goose-capability-boundary.md`.
- **Surface vs class vs cell axis separation:** `execution-surface-roles.md`.
