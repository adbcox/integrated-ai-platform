# Codex 5.1 Replacement Ops

Operational entry points for the executable benchmark/attribution/curation loop:

1. Benchmark:
   - `make codex51-benchmark`
   - reads `config/codex51_replacement_benchmark.json`
   - emits `artifacts/codex51/benchmark/latest.{md,json}`

2. Local-first campaign scaffold:
   - `make codex51-campaign-list`
   - `TASK_ID=campaign-stage-resume make codex51-campaign-run`
   - `PROFILE=first_attempt_only make codex51-campaign-batch`
   - writes `artifacts/codex51/campaign/runs.jsonl`

3. Curation export:
   - `make codex51-curation-export`
   - emits:
     - `artifacts/codex51/curation/training_examples.jsonl`
     - `artifacts/codex51/curation/template_candidates.jsonl`
     - `artifacts/codex51/curation/guard_candidates.jsonl`
     - `artifacts/codex51/curation/benchmark_wins.jsonl`
     - `artifacts/codex51/curation/failures_for_training.jsonl`

Profiles used for model-vs-wrapper attribution:
- `normal`
- `first_attempt_only`
- `manager_reduced`
- `rag_reduced`

The benchmark compares profile outcomes and reports gain estimates without weakening safety controls.

First-attempt quality is now scored from concrete outcome deltas (not plan metadata only):
- first-attempt vs final per-subplan success rates,
- wrapper-dependence delta (`first_to_final_improvement`),
- rescue/escalation/guard signals,
- rollback verification + reconciliation coverage/outcome guarantees,
- return-code and no-dispatch evidence.
