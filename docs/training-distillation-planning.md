# Training/Distillation Planning Layer

This layer prepares captured Codex-assisted work for later local-model improvement without running training jobs yet.

## Purpose
- separate usable training candidates from records that need review
- keep exclusion decisions explicit and inspectable
- produce stable export manifests for later prompt/rule tuning, retrieval seeds, or distillation jobs

## Inputs
Primary input:
- `artifacts/escalations/<task_id>/summary.json`

Optional supporting inputs (linked from summary paths):
- `timeline.log`
- `patch-notes.md`

## Curation Rules
Candidate records must satisfy all:
- non-`tactical` workflow mode
- non-empty `problem_statement`
- non-empty `completion_summary`
- non-placeholder outcome/completion text (for example no `<item>` placeholders)
- at least one `commands_tests_run` entry
- outcome is `pass` or `partial`
- heuristic length is meaningful (`>=12` chars)

Needs-review examples:
- placeholder notes
- weak heuristic
- missing command/test trace

Excluded examples:
- tactical/non-escalated records
- failed outcomes
- missing core problem statement

## Export Record Schema (v1)
Each candidate/review/excluded row includes:
- `task_id`
- `reason`
- `record`

`record` contains:
- `schema_version`
- `record_id`
- `timestamp_utc`
- `repo`
- `branch`
- `workflow_mode`
- `task_class`
- `instruction`
- `context`: constraints, plan summary, commands/tests, trigger, root-cause
- `target`: completion summary, reusable heuristic, normalized outcome
- `source`: summary/timeline/patch-notes paths

## Outputs
Written under `artifacts/training-planning/`:
- `training-candidates.jsonl`
- `needs-review.jsonl`
- `excluded.jsonl`
- `latest.json`
- `latest.md`
- timestamped summaries (`summary_<ts>.json/.md`)

Readiness flags in summary:
- `prompt_rule_tuning`: ready when candidates >= 1
- `retrieval_seed_set`: ready when candidates >= 3
- `sft_distillation_seed`: ready when candidates >= 10

## Usage
Generate planning package:
```sh
make local-model-train-plan
```

JSON summary:
```sh
make local-model-train-plan-json
```

Direct script:
```sh
./bin/plan_training_distillation.py --write-plan
./bin/plan_training_distillation.py --json-only --write-plan
```

Machine-neutral path override:
```sh
ESCALATION_ROOT=/path/to/escalations TRAIN_PLAN_OUT_DIR=/path/to/out ./bin/plan_training_distillation.py --write-plan
```
