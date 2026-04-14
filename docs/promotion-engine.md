# Promotion Engine

The repository now distinguishes **production**, **candidate**, and **manual**
lanes using `config/promotion_manifest.json`. Each lane declares the stage,
manager, and Stage RAG helper version plus the regression pack that must stay
green. The manifest also defines lane rules, policy criteria, and the last
promotion decision so the rest of the tooling can enforce the next sensible
stage.

## Lanes at a glance

| Lane       | Stage version | Manager version | RAG version | Description |
|------------|---------------|-----------------|-------------|-------------|
| production | `stage3-v1`   | `manager4-v1`   | `rag1-v1`   | Stage-3 literal/comment jobs remain the default production lane. |
| candidate  | `stage5-v1`   | `manager4-v1`   | `rag3-v1`   | Stage-5 dual-file batches gathering telemetry ahead of promotion. |
| manual     | `stage4-v1`   | `manager4-v1`   | `rag2-v1`   | Use Codex/manual workflows for out-of-policy or harness edits. |

The manifest also records the current promotion policy (`candidate_success_threshold`,
`candidate_failure_budget`, the required regression pack, trace window budget,
and the desired lane behaviors) so operators can validate evidence consistently.

## Manager-4 routing

- `bin/manager4.py` now accepts `--lane {auto,production,candidate,manual}`.
  - `auto` infers production vs candidate based on the manifest, the literal
    span, and any Stage-5 parameters.
  - If a target violates the lane’s `allowed_targets`, the job reroutes to the
    manual lane with messaging and manifest guidance.
- Each dispatch exports `PROMOTION_*` environment variables so downstream
  managers inherit lane metadata plus the manifest snapshot.
- Manager traces (`artifacts/manager4/traces.jsonl`) now serialize the
  `trace-v1` schema that records:
  - lane name/label/status and the routing reason,
  - stage/manager/RAG versions plus the manifest path/version,
  - the literal line span, promotion outcome, and commit hash when a candidate
    commit is produced,
  - any lane-specific metadata such as allowed targets, regression packs, and
    auto-reroute decisions.

## Running candidate work safely

1. Edit `config/promotion_manifest.json` to update lane versions, lane rules,
   or the promotion policy criteria before making major sequencing changes.
2. Run Manager-4 with `--lane candidate` or supply Stage-5 parameters
   (`--stage stage5` or the secondary literal flags). The dispatcher enforces the
   lane’s allowed target set, emits trace metadata, and passes the lane context
   to Stage-5 via `PROMOTION_*` variables.
3. Stage-5 manager traces inherit the lane metadata so every dual-file commit
   is tagged with the lane, stage, manager, RAG, and manifest version.

## Promotion qualification

`bin/promotion_qualify.py` now summarizes whether the candidate lane meets the
anticipated policy and highlights missing evidence:

```sh
python3 bin/promotion_qualify.py \
  --manifest config/promotion_manifest.json
```

The script reports:

- total candidate successes/failures from the Manager-4 trace,
- the most recent Stage-5 commits (or states that commits are absent),
- the policy criteria (success threshold, failure budget, trace window),
- the lane rules that describe target constraints and regression pack needs,
- whether the success/failure targets are satisfied, and
- the last recorded promotion decision.

Use the summary plus the required regression pack (`bin/micro_lane_stage5.sh`)
to decide whether the candidate lane is ready to promote. Once promoted, update
the manifest so the production lane points at the new stage/manager/RAG
versions, bump the manifest version, and reset the candidate lane to the next
class of work.
