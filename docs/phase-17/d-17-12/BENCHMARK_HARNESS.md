# D-17-12 — Benchmark harness specification

**Authored:** 2026-05-03
**Status:** WP-04 done; smoke-tested against T2

## Overview

Single-script harness at `harness/bench.py`. Reads task sets from
`task-sets/<workload>.json`, runs (model × workload) pairs against
direct Ollama HTTP, writes per-pair JSON results +
`summary.json` per run.

```
python3 docs/phase-17/d-17-12/harness/bench.py \
  [--models T1,T2,T3-A,T3-B] \
  [--workloads long-context,refactor,tool-call,agentic] \
  [--samples 4] [--dry-run]
```

## Models under test

| Key | Name | Host | Tier | Context |
|---|---|---|---|---|
| T1 | qwen2.5-coder:32b | mac-mini | T1 | 32768 |
| T2 | qwen2.5-coder:14b | mac-mini | T2 | 32768 |
| T3-A | gemma2:27b | mac-studio | T3 candidate | 8192 |
| T3-B | qwen3-coder:30b | mac-studio | T3 candidate | 262144 |

## Workloads

### long-context (5 tasks)

Concatenates two real platform docs (`exo-cluster.md` +
`integration-audit-doctrine.md`) ~16K tokens; asks recall +
synthesis questions whose answers are buried mid- and late-doc.

Held-out by construction: these docs are platform-internal,
written 2026-05-02 and 2026-05-03 — outside any model's training
cutoff.

Tasks include 1 short variant (~7K input) for Gemma 2 fairness
since `gemma2:27b` has only 8K context — running 16K against it
would measure truncation, not reasoning. The harness auto-skips
tasks whose `approx_input_tokens` exceeds the model's context
limit.

Scoring: `expected_facts` array (case-insensitive substring
search). Pass threshold 70%.

### refactor (4 tasks)

5 small Python files supplied in the prompt; model must produce
all 5 rewritten files demonstrating a coherent transformation:

- `refactor-userrepo` — extract module-level state to injected class
- `refactor-add-logging` — add structured logging while preserving API
- `refactor-error-handling` — introduce custom exception across chain
- `refactor-async` — convert call chain to async/await

Scoring: `must_contain` array (all required strings present) +
`must_not_contain` (none of these strings appear). Pass threshold:
all must-contains AND zero must-not-contains.

### tool-call (6 tasks)

Direct API with `stream:false` per `local-tool-calling.md`
Findings 1+2 (streaming drops `tool_calls`; exo emits Qwen native
markers as text). 4 fictional tools (weather, search, calc,
read_file). Tasks span:

- Right tool selection (weather/calc/search/read_file)
- Schema adherence (enum-valued args, types)
- "No tool needed" recognition

Scoring: structured `tool_calls` emission preferred (`pass=True`
requires it). Inline-JSON emission (`<tools>{...}</tools>` Qwen-
native, fenced JSON, bare JSON in content) gets partial credit
via `_try_parse_inline_tool_call`. Empirical: qwen2.5-coder via
Ollama 0.20.7 emits inline JSON not structured `tool_calls` even
with `stream:false` — recorded as a serving-stack finding (NEW;
extends `local-tool-calling.md` Finding 1).

### agentic (4 tasks)

Multi-step planning prompts: "produce a numbered plan with
verification steps." Tasks:

- Debug failing test
- Deploy + rollback
- Data migration with checkpoints
- Incident response

Scoring: `expected_steps` array of step keywords (case-
insensitive). Half-credit for keyword presence; half-credit for
keywords appearing in expected order. Pass threshold 70%.

## Output schema

Per-pair JSON record at `results/<run-id>/<model>__<workload>.json`:

```json
{
  "model_key": "T2",
  "model_name": "qwen2.5-coder:14b",
  "model_tier": "T2",
  "model_host": "mac-mini",
  "context_limit": 32768,
  "workload": "tool-call",
  "samples": [
    {
      "task_id": "tc-weather-paris",
      "task_summary": "...",
      "status": "ok",
      "wall_s": 4.13,
      "total_duration": 4131000000,
      "load_duration": 24000000,
      "prompt_eval_count": 254,
      "prompt_eval_duration": 80000000,
      "eval_count": 105,
      "eval_duration": 4020000000,
      "tokens_per_sec": 26.1,
      "response_role": "assistant",
      "response_content": "...",
      "tool_calls": [],
      "finish_reason": "stop",
      "grade": {"pass": false, "score": 1.0, "notes": "..."}
    }
  ],
  "peak_runner_rss_bytes": 8400000000,
  "started_utc": "2026-05-03T16:56:32Z",
  "n_samples_attempted": 6,
  "n_samples_ok": 6,
  "n_samples_skipped": 0,
  "n_samples_error": 0
}
```

Per-run summary at `results/<run-id>/summary.json` aggregates
mean_score, mean_tps, peak_rss_gb per (model, workload).

## Memory measurement

`measure_runner_rss` polls Ollama runner subprocess RSS via `ps`
after the workload's last sample. Captured at workload end as a
peak proxy (Ollama keeps the runner resident; RSS at end reflects
cumulative pressure). Recorded in bytes; reported in GB.

## Held-out content guarantees

- Long-context docs authored after Qwen2.5/Gemma 2/Qwen3-Coder
  training cutoffs — recall failures cannot be hidden by training-
  data leakage.
- Refactor source files: synthetic, written for this harness.
- Tool-call tools: fictional schemas (no real API behavior).
- Agentic prompts: synthesis tasks with no canonical answer.

## Auto-grading limitations (drives WP-06 surface-back)

Auto-grading is keyword-based, not semantic:

- `long-context` may false-positive if the model spits keywords
  without coherent reasoning.
- `refactor` may false-pass syntactically-correct-but-broken code
  (e.g., new methods that compile but mis-thread the inject).
- `agentic` may false-pass plans that name all the right step
  keywords without coherent ordering or actual verification logic.

WP-06 surface-back will request operator hand-grading on a sample
across all 16 (model × workload) cells before WP-07 decision.

## Reproducibility

- Temperature pinned at 0.1 (long-context, refactor, tool-call) or
  0.2 (agentic).
- `num_predict` capped per workload (see task-sets).
- Random seed not pinnable in Ollama 0.20.7/0.22.1 API.
- Each run gets a UTC-timestamp-based run_id directory.
- Re-runs with same harness + same task sets ARE NOT bit-identical
  (model nondeterminism even at low temp); aim is rank-stability
  not score-equality.

## Open caveats (recorded for the report)

1. **Ollama version drift** — Mini 0.20.7, Studio 0.22.1.
2. **Quant drift** — gemma2:27b is Q4_0; qwen-family is Q4_K_M.
3. **Hardware drift** — Mac Mini 48GB vs Mac Studio 96GB. T3
   candidates run on better hardware regardless of model quality.
4. **Tool-call serving-stack effect** — qwen-family models emit
   inline JSON not structured `tool_calls` via Ollama. Grader
   credits inline emission; pass-rate reflects structured-only.
5. **Long-context Gemma fairness** — tasks gated to 7K input only
   for Gemma 2; not directly comparable to other models'
   16K performance.
