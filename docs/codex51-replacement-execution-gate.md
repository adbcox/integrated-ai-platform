# Codex 5.1 Replacement Execution Gate

This file is the concrete execution gate for declaring Codex 5.1 replacement readiness in this repository.  
It complements `docs/codex51-replacement-gate.md` with explicit version and threshold requirements.

## 1. Required Subsystem Versions

The gate is not eligible until all of the following are true in `config/promotion_manifest.json`:

- stage system: `current_version >= stage9-v1`
- manager/orchestration: `current_version >= manager9-v1`
- retrieval/RAG: `current_version >= rag9-v1`
- worker utilization: `current_version >= worker-routing-v3`
- regression/qualification: `current_version >= qualify-v3`
- promotion engine: `current_version >= level10-promote-v3`
- learning/training/attribution: `current_version >= learning-v10`

## 2. Required Task Classes

The benchmark task set must contain real tasks in each class:

1. multi-file orchestration changes
2. retrieval + orchestration changes
3. resumable/checkpointed execution work
4. safe contract handling across heterogeneous targets
5. bounded architecture/control-loop changes

No fixture-only evidence can satisfy the gate.

## 3. Required Metrics (Minimum)

The gate requires sustained metrics over the active benchmark window:

- `success_rate >= 0.70`
- `rescue_rate <= 0.45`
- `escalation_rate <= 0.35`
- `recurrence_rate <= 0.35`
- `first_attempt_quality_rate >= 0.50`
- `local_first_share >= 0.80` for in-scope benchmark task classes

`local_first_share` means completed tasks that executed locally as primary path without manual fallback.

## 4. First-Attempt Quality / Wrapper Dependence Constraints

The gate fails if quality is primarily wrapper-driven.  
At minimum all must be true:

- `first_attempt_success_rate_raw >= 0.55`
- `first_to_final_delta_rate <= 0.20`
- no class-level `escalation_rate > 0.50`
- no class-level repeated-failure signature dominates more than 40% of failures

## 5. Non-Maskable Failure Conditions

Gate is automatically blocked if any apply:

- manager or retrieval rescue dominates successful outcomes
- repeated deterministic failures continue without guard/rule conversion
- benchmark pass relies on cherry-picked classes or hidden failures
- safety boundaries are relaxed to produce apparent success

## 6. Evidence Bundle Required For PASS Claim

All are mandatory:

1. benchmark report (`artifacts/codex51/benchmark/latest.json`)
2. curation export (`artifacts/codex51/curation/latest.json`)
3. campaign run evidence (`artifacts/codex51/campaign/runs.jsonl`)
4. subsystem qualification evidence (`artifacts/promotion/qualification_history.jsonl`)
5. explicit attribution summary separating model vs manager vs retrieval vs guard gains
6. clean working tree at claim time

## 7. Tight Rule For Claiming “Model Improved”

A model-improvement claim is valid only when:

- first-attempt quality improves on fixed task classes,
- rescue/escalation do not increase to compensate,
- and the same improvement appears under constrained-assist slices.

If these are not true, classify as wrapper improvement and do not claim gate readiness.
