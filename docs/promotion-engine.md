# Promotion Engine

The repository now distinguishes **production**, **candidate**, and **manual**
lanes using `config/promotion_manifest.json`. Each lane declares the stage,
manager, and Stage RAG helper version plus the regression pack that must stay
green.

## Lanes at a glance

| Lane       | Stage version | Manager version | RAG version | Description |
|------------|---------------|-----------------|-------------|-------------|
| production | `stage3-v1`   | `manager4-v1`   | `rag1-v1`   | Stage-3 literal/comment jobs remain the default production lane. |
| candidate  | `stage5-v1`   | `manager4-v1`   | `rag3-v1`   | Stage-5 dual-file batches gathering telemetry ahead of promotion. |
| manual     | `stage4-v1`   | `manager4-v1`   | `rag2-v1`   | Use Codex/manual workflows for out-of-policy or harness edits. |

The manifest also records the current promotion policy (`candidate_success_threshold`,
`candidate_failure_budget`, and the required regression pack).

## Manager-4 routing

- `bin/manager4.py` now accepts `--lane {auto,production,candidate,manual}`.
  - `auto` infers production vs candidate based on the manifest and Stage-5 flags.
  - If a target falls outside the lane’s `allowed_targets`, the job is rerouted
    to the manual lane with guidance.
- Each dispatch exports `PROMOTION_*` environment variables so downstream
  managers inherit lane metadata.
- Manager traces (`artifacts/manager4/traces.jsonl`) now record lane, stage
  version, manager version, RAG version, manifest path/version, and the
  regression pack tied to the lane.

## Running candidate work safely

1. Edit `config/promotion_manifest.json` if you need to change lane versions.
2. Use Manager-4 with `--lane candidate` or supply Stage-5 parameters (`--stage stage5`
   or the secondary literal flags). The dispatcher enforces candidate target
   scopes before invoking Stage-5.
3. Stage-5 manager traces now include the promotion metadata, so each commit is
   attributable to a specific lane/version combo.

## Promotion qualification

`bin/promotion_qualify.py` summarizes whether the candidate lane meets the
manifest policy:

```sh
python3 bin/promotion_qualify.py \
  --manifest config/promotion_manifest.json
```

The script reports:

- total candidate successes/failures from the Manager-4 trace,
- the most recent Stage-5 commits,
- whether success/failure targets are satisfied, and
- the last recorded promotion decision.

Use the summary plus the required regression pack (`bin/micro_lane_stage5.sh`)
to decide whether the candidate lane is ready to promote. Once promoted, update
the manifest so the production lane points at the new stage/manager/RAG
versions and reset the candidate lane to the next class of work.
