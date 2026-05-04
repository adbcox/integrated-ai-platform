# D-17-12 WP-06 — Quality grading + analysis (surface back)

**Date:** 2026-05-03
**Status:** WP-06 parked — D-17-12 yields execution thread to D-17-13
(Goose+T3-B production validation). WP-07 + WP-08 resume after D-17-13
closes.

## Run inventory

| Run ID | Purpose | Cells |
|---|---|---|
| `20260503T170223Z` | Primary run | T1+T2 all workloads; T3-A+T3-B agentic only (T3 lc/refactor/tool-call failed warmup pre-Studio-bind-fix) |
| `20260503T180613Z` | T3 re-run after Studio bind-fix | T3-A+T3-B for long-context, refactor, tool-call |
| `20260503T210101Z` | G1 grader fix re-run | All 4 models, refactor only, with `must_not_contain` cleared on refactor-add-logging |

## Final consolidated matrix (post-G1)

| Model | long-ctx | refactor | tool-call | agentic | Best TPS |
|---|---|---|---|---|---|
| T1 (qwen2.5-coder:32b) | 0.86 | **1.00** | 0.91 | 0.62 | 13.8 |
| T2 (qwen2.5-coder:14b) | 0.87 | **0.94** | 0.91 | 0.71 | 29.9 |
| T3-A (gemma2:27b) | 0.75 (1/5 — 8K limit) | **0.94** | n/a (no tool support) | 0.79 | 34.8 |
| T3-B (qwen3-coder:30b) | 0.84 | **1.00** | 0.93 | 0.83 | **101.6** |

## Tool-call dual-track table (G2 policy: report both)

Single-correctness column tracks "did the model identify the right tool with
right args" regardless of emission shape. Structured-emission column tracks
"did Ollama populate `response.message.tool_calls`" (the Goose / D-17-13
adoption requirement).

| Model | Single correctness (mean score) | Structured emission rate | Notes |
|---|---|---|---|
| T1 (qwen2.5-coder:32b) | 0.91 | **0/6 = 0%** | inline JSON only |
| T2 (qwen2.5-coder:14b) | 0.91 | **0/6 = 0%** | inline JSON only |
| T3-A (gemma2:27b) | n/a | n/a | Ollama: `gemma2:27b does not support tools` (HTTP 400) |
| T3-B (qwen3-coder:30b) | 0.93 | **5/6 ≈ 83%** | structured `tool_calls` populated |

(T3-B's 6th task was `tc-no-tool-needed`, where structured emission is
correctly absent — model recognized no tool was required. So functionally
T3-B is 100% correct on tool-or-no-tool decision; 5/5 structured-emission
when a tool was called.)

**Conclusion**: only T3-B is a viable native-tools backend for downstream
agentic tooling (Goose, D-17-13). T1/T2 inline-JSON output requires the
adapter pattern documented in `local-tool-calling.md` Findings 1+2.

## G1 fix — what changed and why

`refactor-add-logging` task spec had:

```json
"must_not_contain": ["print("]
```

But the input includes a legit caller:

```python
# file_d.py — caller
from file_c import greet
print(greet(42))
print(greet(99))
```

The task instructs "do not change function signatures or public API";
models correctly preserve the caller; grader penalized them.

**Fix landed:** `must_not_contain: []`. Re-run scores match expected
post-fix uniform lift (~+0.12 per model). All 4 models pass refactor cleanly.

Diff: single-line change in `task-sets/refactor.json` (must_not_contain
array cleared on refactor-add-logging task only; refactor-userrepo's
`open("/var/db/users.txt")` constraint preserved as it's correctly
flagging in-place direct-file-IO that the refactor *should* eliminate).

## G2 policy decision: dual-track reporting

Operator decision recorded: **report both single-correctness and
structured-emission separately**. Headline matrix uses single-correctness
(matches "is the model competent at tool-use" framing); WP-07 decision
matrix surfaces structured-emission as a separate column for D-17-13
adoption signaling.

## 12-record hand-grade sample

Built and ready for operator review at:

```
docs/phase-17/d-17-12/handgrade/01__T1__long-context__lc-cross-doc-synthesis.md
docs/phase-17/d-17-12/handgrade/02__T1__agentic__ag-debug-failing-test.md
docs/phase-17/d-17-12/handgrade/03__T2__long-context__lc-finding-CC-prior-art.md
docs/phase-17/d-17-12/handgrade/04__T2__agentic__ag-debug-failing-test.md
docs/phase-17/d-17-12/handgrade/05__T3-A__long-context__lc-short-gemma-friendly.md
docs/phase-17/d-17-12/handgrade/06__T3-A__agentic__ag-debug-failing-test.md
docs/phase-17/d-17-12/handgrade/07__T3-A__agentic__ag-incident-response.md
docs/phase-17/d-17-12/handgrade/08__T3-B__long-context__lc-cross-doc-synthesis.md
docs/phase-17/d-17-12/handgrade/09__T3-B__long-context__lc-finding-CC-prior-art.md
docs/phase-17/d-17-12/handgrade/10__T3-B__agentic__ag-debug-failing-test.md
docs/phase-17/d-17-12/handgrade/11__T3-B__tool-call__tc-search-event.md
docs/phase-17/d-17-12/handgrade/12__T3-B__refactor__refactor-add-logging.md
```

Each packet contains: task summary, full model response, auto-grader
output, and an operator scoring rubric (coherent? addresses task?
ship-ready? auto-grade fair? hand-grade 0-1).

Estimated operator time: ~15 min (skim each response, check rubric).

The 12 cells were chosen for high information value — borderline
auto-grades on long-context and agentic where keyword-graders are most
likely to false-positive. Specifically:

- **Packets 1, 8, 9** — long-context cross-doc-synthesis comparisons
  where T3-B scored higher than T1 (0.80 vs 0.60); hand-grade tests whether
  T3-B is genuinely better or just keyword-spraying.
- **Packets 2, 4, 6, 10** — same agentic task across all models for
  side-by-side ordering quality comparison.
- **Packet 12** — refactor-add-logging confirmation that G1 fix was
  warranted (response visibly preserves the print() callers correctly).
- **Packet 11** — only T3-B tool-call grade < 1.0 (0.6 on tc-search-event);
  hand-grade tells us whether the partial credit was earned.

## WP-07 decision matrix template (drafted, blank verdicts pending)

| Model | Workload | Auto-grade | Adopt verdict | Reject verdict | Notes |
|---|---|---|---|---|---|
| T1 (32b @ Mini) | long-context | 0.86 | | | T1 baseline reference |
| T1 | refactor | 1.00 | | | |
| T1 | tool-call | 0.91 (inline) | | | Goose-incompatible |
| T1 | agentic | 0.62 | | | weakest agentic |
| T2 (14b @ Mini) | long-context | 0.87 | | | |
| T2 | refactor | 0.94 | | | |
| T2 | tool-call | 0.91 (inline) | | | Goose-incompatible |
| T2 | agentic | 0.71 | | | |
| T3-A (gemma2:27b @ Studio) | long-context | 0.75* | | | *only 7K-input task ran; 8K context ceiling |
| T3-A | refactor | 0.94 | | | |
| T3-A | tool-call | n/a | | | model architecture lacks tool support |
| T3-A | agentic | 0.79 | | | |
| T3-B (qwen3-coder:30b @ Studio) | long-context | 0.84 | | | 256K native window — strongest |
| T3-B | refactor | 1.00 | | | 85 tps — fastest |
| T3-B | tool-call | 0.93 (structured) | | | **only model with structured emission** |
| T3-B | agentic | 0.83 | | | strongest agentic |

Operator fills in adopt/reject verdicts per cell after hand-grading.

## Pre-park state — D-17-12 hand-off note

**Resume D-17-12 at:** WP-07 (decision matrix population from operator
hand-grade results), then WP-08 (chronicle update + IN PROGRESS → DONE
flip).

**Compute used so far:** ~3.0h of 6h hard cap.

**Remaining work estimate:**
- WP-07: ~30 min after operator returns hand-grades
- WP-08: ~45 min (chronicle + framework flip + OpenProject sync)

**D-17-13 dependencies satisfied by current D-17-12 state:**
- F1 finding (T3-B structured tool_calls) is documented and verifiable
- T3-B benchmark substrate exists (Studio Ollama nohup-managed PID 71160)
- Mac Studio addressable from Mini (192.168.10.142:11434)

D-17-13 will yield production verification of F1 in its WP-03; WP-08
chronicle benefits from referencing that worked example.

## Resume checklist (when D-17-13 closes)

1. Operator returns 12 hand-grade scores via packet markdown updates.
2. Synthesize hand-grade vs auto-grade table for each cell.
3. Fill WP-07 decision matrix verdicts.
4. Write WP-08 chronicle:
   - F1 (now production-validated via D-17-13)
   - F2 (gemma2 no tool support)
   - F3 (T3-B 3.4× T2 throughput, MoE active-param effect)
   - 100% provenance override rate (operator note 1)
   - 8K context = "n/a" not "truncate" (operator note 2)
   - Inline-JSON extends Finding 1 to non-streaming, model-side specific
     (operator note 3); now further refined by D-17-13: it is qwen2.5-coder
     family-specific, NOT qwen3-coder.
5. Flip D-17-12 IN PROGRESS → DONE in PROJECT_FRAMEWORK.md §9.
6. Run openproject-sync-from-framework.py.
