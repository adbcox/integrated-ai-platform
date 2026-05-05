# Codex 5.1 Replacement Doctrine

Status: active

## Finding 39

`recurrence_rate` requires at least 3 distinct failed tasks before the metric is considered meaningful. Below that floor, retry semantics on a single failed task dominate the ratio and the benchmark reports `recurrence_status=insufficient_data` instead of treating the value as a failure gate.

## Finding 40

Codex 5.x replacement benchmark is passing at the current observed position as of 2026-05-05: `success_rate=0.933`, `rescue_rate=0.067`, `escalation_rate=0.133`, `first_attempt_quality_rate=0.666`, and `recurrence_status=insufficient_data` on a 15-task sample. The recurrence threshold remains available once the run set is expanded to a sufficiently large task population.

## Finding 41

External parity validation is now instrumented through the Aider polyglot benchmark in D-17-133. The wrapper writes held-out results to `artifacts/polyglot_bench/` and records code-execution outcomes from real benchmark runs rather than internal plumbing tasks. Current local model samples on the shared beer-song exercise show `ollama_chat/qwen3-coder-next:coding` at 100% first-attempt pass, `ollama_chat/qwen3-coder:30b-coding` at 0% first-attempt / 100% eventual pass after one retry, and `ollama_chat/deepseek-coder-v2:16b-lite-instruct-q4_K_M` at 0% on the same sample. Internal codex51 remains the plumbing-health regression instrument; polyglot is the parity-validation instrument.
