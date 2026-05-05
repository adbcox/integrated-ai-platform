# Agent Trace Corpus Doctrine

Date: 2026-05-05
Deliverable: D-17-124 candidate

## Scope

The agent trace corpus is a local-only analysis substrate derived from
this repository's own execution telemetry:

- `artifacts/execution_metrics.jsonl`
- `artifacts/aider_runs/**/metadata.json`
- `artifacts/executions/*.json`
- `artifacts/aider_runs/verifier_events.jsonl`

It is used to study failure modes, improve routing/verifier prompts, and
guide future local-model tuning. It is not a redistribution artifact.

## Canonical schema

Each row carries:

- `prompt_text`
- `file_state_pre`
- `file_state_post`
- `model`
- `layer1_verdict`
- `layer1_5_verdict`
- `success_boolean`
- `failure_mode_class`

Helpful enrichments retained in v0:

- `source_type`
- `source_path`
- `requested_files`
- `changed_files`
- `failure_signatures`
- `label_confidence`
- `task_type`

## Labeling policy

The first-pass taxonomy is heuristic and source-aware:

- `success`
- `wrong_target`
- `no_change`
- `partial_diff`
- `target_ambiguous`
- `timeout`
- `runtime_error`

Rows with incomplete evidence keep lower `label_confidence`.

## Privacy rule

The corpus contains internal code and internal telemetry. Keep it local.
Do not commit the Parquet output or export it off-repo. If a downstream
analysis needs sharing, use aggregated statistics only.

## Operational note

This corpus is a candidate input for:

1. failure-mode taxonomy refinement
2. verifier few-shot hardening
3. prompt-engineering references
4. small-model fine-tuning experiments

The corpus does not replace live regression tests.
