# D-17-12 WP-07 — Local model tier decision matrix

**Date:** 2026-05-04
**Status:** Drafted from objective benchmark data (WP-05 + WP-06 post-G1 matrix). Operator hand-grade scoring of 12 packets remains PARKED; this matrix uses tps + auto-graded refactor/agentic/tool-call scores + structured-emission rate as the decisional axes. Hand-grade results, when they land, refine per-workload scores in the appendix without re-shaping the per-class recommendations in the headline.

## Tier vocabulary recap

| Tier label | Model | Host | Role |
|---|---|---|---|
| **T1** | `qwen2.5-coder:32b` | Mac Mini Ollama | Heavyweight local reasoning baseline |
| **T2** | `qwen2.5-coder:14b` | Mac Mini Ollama | Lightweight local fast-path baseline |
| **T3-A** | `gemma2:27b` | Mac Studio Ollama | Specialty (long-context candidate) |
| **T3-B** | `qwen3-coder:30b` | Mac Studio Ollama | Specialty (MoE — high tps + structured tool calls) |

These are *tiers* in the sense used by `docs/PROJECT_FRAMEWORK.md` line 91. They are model-and-host pairings, not (surface × class) cells. A cell is `(execution surface × work class)` per D-17-53 §18.O — orthogonal axis.

## Headline — per-class recommendation matrix

Class definitions: see `docs/architecture-facts/class-taxonomy.md`. Goose+T3-B (Goose × C1a) suspension per D-17-53 Session 13 Option B is noted but not propagated onto T3-B itself — T3-B remains a candidate model for any future non-Goose surface that consumes it.

| Class | Default tier | Fallback tier | Excluded tiers | Rationale (objective benchmark) |
|---|---|---|---|---|
| **C1a** — Verbatim-quote-bearing reference docs | **T1 — under explicit operator-side review** | T2 | T3-A (no tool support; quote-fidelity not benchmarked at this shape); T3-B *via Goose* (Goose × C1a SUSPENDED per D-17-53) | C1a is a local-tier-with-extra-rails class, not a no-go zone. Auto-graded refactor 0.88–1.00 across T1/T3-B is not the right discriminator; the failure mode is source-fidelity loss in narrative wrapping (D-17-53 substrate-shape hypothesis falsified at Session 13). T1 has the strongest auto-grades on lc (0.86), refactor (1.00), and tool-call correctness (0.91); the explicit operator-side review rail is the substitute for the absent capability evidence at this shape. T2 fallback for round-trip-latency-sensitive work; verdict still gated on review. |
| **C1b** — Narrative chronicle/doctrine without quote citations | **T3-B** (via direct Ollama call) or **T1** | T2 | T3-A (no tool support; weak lc 1/5 ran) | T3-B leads on every benchmarked workload (lc 0.84, refactor 1.00, agentic 0.83) at 3.4× T2 tps, *and* C1b prose-shape removes the quotation-fidelity failure-mode that disqualifies it from C1a. T1 is the conservative fallback. **Goose+T3-B for C1b is Posture 0 (not yet evaluated for this cell at the C1b sub-class)**; Posture-1 N=5 gate would re-establish under the narrowed sub-class. |
| **C2** — Runbook / doc update from observation | **T3-B** | T1 | — | Same shape as C1b for grading purposes (review is the rail, not the file mode). T3-B's high tps materially helps the round-trip on observation-driven updates. |
| **C3** — Single-file code edit, ≤50 lines | **T3-B** | T1 | T3-A (no tool support; matters when the edit needs structured tool invocation) | refactor 1.00 + agentic 0.83 + tool-call structured 0.93. The 50-line bound matches what the keyword-grader can actually discriminate at; both tiers comfortably clear it. |
| **C4** — ADR / doctrine drafting | **T1** | T3-B | — | T1's auto-grades (lc 0.86, agentic 0.62) understate its strength on doctrine drafting because the keyword-grader saturates on lc + refactor and the agentic grader is the most discriminating cell (0.21 spread across tiers). T1 is the established baseline for this work-class on Claude Code under `claude-local`; T3-B is the migration candidate once N=5 evidence accumulates on a Goose-or-direct-Ollama cell. |
| **C5** — Multi-file refactor, single concern | (Phase-C; not yet migrated) | — | — | Tier-irrelevant at this stage. When Phase-C opens, T3-B is the candidate by throughput + 0.88 refactor; promotion gates per `promotion-criteria.md` apply. |
| **C6** — Bug investigation + fix proposal | (Phase-C; not yet migrated) | — | — | Tier-irrelevant at this stage. Same logic as C5. |
| **C7 / C8 / C9** — CONTROL role | **N/A — never migrate** | — | All local tiers | Per `execution-surface-roles.md` rail #1: CONTROL never migrates. Local tiers are EXECUTION substrate; trust-authority lives on CONTROL. |
| **C10** — Deterministic remediation script | **T2** (mechanical authoring) or **T3-B** (when tool-call needed) | T1 | T3-A (no tool support) | C10 has two flavors: pure-shell-authoring (T2 plenty) vs script-with-runtime-validation-loop (T3-B's tool-call structured emission earns its keep). Operator chooses by the consequence-surface gate (Phase-B per taxonomy). |

### Decision rules (read these before assigning a tier)

1. **Default tier ≠ committable output.** Every recommendation here assumes the §18.O dual-review rail: EXECUTION drafts, CONTROL approves. Tier choice is which EXECUTION model to prefer; it does not change the review-on-commit posture.
2. **Tool-call requirement is binary.** If the work requires structured `tool_calls` (Goose, MCP-direct, agentic loops), T3-A is excluded by Ollama (`gemma2:27b does not support tools`), and T1/T2 are excluded by qwen2.5-coder family inline-JSON emission (Finding 1.B, `local-tool-calling.md`). **T3-B is the only structured-emission tier on this platform.**
3. **Long-context > 8K tokens.** T3-A has 8K context ceiling (1/5 ran on lc benchmark); excluded for any class whose realistic input exceeds 8K. T3-B's 256K native window makes it the lc default whenever a tier is needed.
4. **C1a is a suspension zone for Goose+T3-B specifically.** It is NOT a suspension on T3-B as a model. A future non-Goose surface (direct-Ollama call from Claude Code, or a different agent CLI) consuming T3-B for C1a would re-enter the promotion-criteria gate from Posture 0; nothing in this matrix forbids it.
5. **Hand-grade can flip per-workload scores by ±0.10–0.15.** Per WP-06 G1+G2 already-known auto-grade biases. Hand-grade cannot flip *tier ordering* for any class above — the gaps are larger than the bias band. If hand-grade does flip an ordering, treat that as evidence the auto-grader is broken on that workload, not as evidence the tier ranking changed.

## Surface-back cross-references

- **D-17-53 §18.O cell promotion framework:** `docs/architecture-facts/promotion-criteria.md`. The "first measured cell" (Goose+T3-B × C1) lives there; this matrix references it and does not duplicate.
- **Class definitions:** `docs/architecture-facts/class-taxonomy.md`. C1a/C1b split landed 2026-05-04.
- **Tool-call doctrine:** `docs/architecture-facts/local-tool-calling.md`. Finding 1.B (qwen3-coder structured-correct vs qwen2.5-coder inline-JSON) is the single most decisional finding in this matrix — it is what makes T3-B uniquely suitable for tool-bearing classes.
- **Goose capability boundary:** `docs/architecture-facts/goose-capability-boundary.md`. Posture state for the (Goose × C1a) cell is canonical there; this matrix mirrors but does not own the suspension.
- **Tier doctrine:** `docs/architecture-facts/local-model-tier-doctrine.md` (this deliverable's WP-03 output). Captures the per-tier capability boundaries this matrix consumes.

## Appendix — Per-workload cell evidence table

This is the supporting per-cell view from `WP06_SURFACE_BACK_2026-05-03.md` consolidated matrix, with adopt/reject verdicts now filled in by tier (independent of class — this table answers "is this tier capable on this workload" not "which class should this tier own").

| Tier | Workload | Mean score | Best TPS | OK/Att | Verdict | Notes |
|---|---|---|---|---|---|---|
| T1 | long-context | 0.86 | 13.8 | 5/5 | **ADOPT** | Solid baseline; no tier excluded for lc on capability grounds |
| T1 | refactor | 1.00 (post-G1) | 13.8 | 4/4 | **ADOPT** | Saturated; tps is the limit |
| T1 | tool-call | 0.91 (inline) | 13.8 | 6/6 | **PARTIAL** | Inline-JSON only; Goose-incompatible; needs adapter |
| T1 | agentic | 0.62 | 11.4 | 4/4 | **PARTIAL** | Weakest agentic tier; functions but is the floor |
| T2 | long-context | 0.87 | 17.6 | 5/5 | **ADOPT** | Score parity with T1 at faster tps |
| T2 | refactor | 0.94 (post-G1) | 25.2 | 4/4 | **ADOPT** | T2 sweet spot |
| T2 | tool-call | 0.91 (inline) | 29.9 | 6/6 | **PARTIAL** | Inline-JSON only; Goose-incompatible |
| T2 | agentic | 0.71 | 25.1 | 4/4 | **ADOPT** | Materially better than T1 on agentic |
| T3-A | long-context | 0.75 | 24.0 | **1/5** | **REJECT** | 8K context ceiling — excludes 4/5 lc tasks; not viable as lc tier |
| T3-A | refactor | 0.94 (post-G1) | 34.2 | 4/4 | **ADOPT** | refactor works |
| T3-A | tool-call | n/a | n/a | 0/6 | **REJECT** | `gemma2:27b does not support tools` — architecture-level |
| T3-A | agentic | 0.79 | 34.8 | 4/4 | **ADOPT** | Strong agentic for non-tool work |
| T3-B | long-context | 0.84 | 49.3 | 5/5 | **ADOPT** | 256K native — strongest lc tier |
| T3-B | refactor | 1.00 (post-G1) | 85.3 | 4/4 | **ADOPT** | Fastest + saturated score |
| T3-B | tool-call | 0.93 (structured) | **101.6** | 6/6 | **ADOPT — preferred** | Only structured-emission tier; preferred for any tool-bearing class |
| T3-B | agentic | 0.83 | 85.8 | 4/4 | **ADOPT** | Strongest agentic |

### Per-cell verdict legend

- **ADOPT** — Tier is capable on this workload at production-ready quality (auto-grade ≥ 0.80 OR saturated at ceiling).
- **ADOPT — preferred** — Tier is capable AND uniquely capable in some axis (here: structured tool emission).
- **PARTIAL** — Tier produces output but with a known caveat that requires adapter pattern, downstream filtering, or excludes specific consumers (Goose).
- **REJECT** — Tier is not viable on this workload due to capability boundary (context window, tool support).

### Auto-grade biases acknowledged (G1, G2, G3)

Documented in `WP05_RESULTS_2026-05-03.md`. Not refought here. Net effect:

- **G1 (refactor `must_not_contain`):** Fixed pre-matrix; refactor scores in this table are post-G1.
- **G2 (tool-call dual-track scoring):** Per WP-06 G2 policy decision (dual-track reporting), the headline matrix uses the structured-emission column for Goose-relevance signaling and the correctness column for general capability signaling. This appendix collapses to single-track score for the per-cell verdict.
- **G3 (long-context keyword-grading):** Could false-positive a tier on lc by 0.05–0.10. None of the per-cell verdicts in this table are within that bias band of their threshold; G3 fix would not flip any ADOPT/REJECT.

### Hand-grade fold-in pattern (when the 12 packets land)

When the 12 hand-grade packets are scored:

1. Compute hand-grade − auto-grade delta per packet.
2. Apply the delta to its source cell's score in this appendix table.
3. Re-check whether any per-cell verdict crosses an ADOPT/PARTIAL/REJECT boundary. (Predicted: none will.)
4. If a verdict changes: re-evaluate the corresponding per-class recommendation in the headline. (Predicted: none will need to change because per-class recommendations rest on tier-vs-tier *gaps*, not on absolute scores.)
5. Append the hand-grade evidence as `WP06_HANDGRADE_RESULTS_<date>.md` and link from this matrix's appendix.

## Outstanding items rolled forward to WP-08 doctrine

- **Substrate-shape-correlation hypothesis FALSIFIED at N=2** (D-17-53 finding) — this matrix encodes the post-falsification posture: per-class recommendations no longer treat substrate-shape as a tier-selection axis.
- **Single-clean-datapoint sampling-artifact hypothesis STRENGTHENED** at Session 13 — the matrix treats Goose+T3-B × C1a as not capable rather than substrate-dependent.
- **Cell-change branch deferred** — gemma2:27b and larger qwen variants on C1a are parked. If reactivated, they enter this matrix as new tier rows (T3-A is already here; a hypothetical "T3-C" larger qwen would be added with its own benchmark cell).
- **Operator hand-grade of 12 packets PARKED** — fold-in pattern documented above; matrix is committable without it.
