# Local-Model Evaluation Harness

This harness provides a lightweight first-pass measurement layer over captured Codex escalation artifacts.

## Purpose
- summarize escalation behavior and outcomes
- identify candidate task classes for local-first handling
- identify classes still best suited for Codex escalation
- generate regular, machine-neutral outputs for future heuristic extraction and dataset curation

## Inputs
Default input root:
- `artifacts/escalations/`

Expected sources:
- `artifacts/escalations/<task_id>/summary.json`
- `artifacts/escalations/index.jsonl`

## Outputs
Console report sections:
- by workflow mode
- by escalation trigger
- by repo
- by outcome
- by fix/root-cause pattern
- local-first candidate classes
- codex-preferred classes

Optional report files (`--write-report`):
- `artifacts/evaluation/latest.md`
- `artifacts/evaluation/latest.json`
- timestamped snapshots in the same directory

## Usage
Run markdown summary + write reports:
```sh
make local-model-eval
```

Run JSON summary + write reports:
```sh
make local-model-eval-json
```

Direct script usage:
```sh
./bin/evaluate_escalations.py --write-report
./bin/evaluate_escalations.py --json-only --write-report
```

Override paths (machine-neutral):
```sh
ESCALATION_ROOT=/path/to/escalations EVAL_OUT_DIR=/path/to/out ./bin/evaluate_escalations.py --write-report
```
