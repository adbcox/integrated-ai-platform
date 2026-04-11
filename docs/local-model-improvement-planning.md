# Local-Model Improvement Planning Layer

This planning layer turns escalation captures and evaluation summaries into explicit next-step guidance for local-model capability growth.

## Inputs
- `artifacts/escalations/<task_id>/summary.json`
- `artifacts/escalations/index.jsonl`
- latest evaluation outputs from `bin/evaluate_escalations.py`

## Decision categories
Task classes are categorized into:
1. `local-first candidate`
2. `local-with-codex-assist`
3. `codex-preferred`
4. `codex-required for now`

Class identity:
- `<escalation_trigger> | <fix_pattern_root_cause>`

Default thresholds:
- `local-first candidate`: `total>=3`, `fail_rate<=0.10`, `pass>=2`
- `local-with-codex-assist`: `fail_rate<=0.25` with at least one pass/partial sample
- `codex-preferred`: fallback when local stability evidence is limited
- `codex-required for now`: `fail_rate>=0.50` with `>=2` samples OR repeated `hard-failure-analysis` class with no pass

## Outputs
Console + optional files under `artifacts/planning/`:
- `latest.md`
- `latest.json`
- timestamped snapshots (`plan_<ts>.md`, `plan_<ts>.json`)

Plan includes:
- class categorization
- recommended default workflow mode per class
- candidate local heuristics
- next-cycle actions (small, bounded updates)

## Usage
Markdown planning report:
```sh
make local-model-plan
```

JSON planning report:
```sh
make local-model-plan-json
```

Direct script usage:
```sh
./bin/plan_local_model_improvements.py --write-plan
./bin/plan_local_model_improvements.py --json-only --write-plan
```

## Operational guidance
- Apply 1-2 heuristic/rule updates per cycle.
- Keep high-failure classes in Codex-heavy modes until evidence improves.
- Re-run evaluation and planning after each batch of meaningful escalations.
