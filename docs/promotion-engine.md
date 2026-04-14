# Promotion Engine

The repository now distinguishes **production**, **candidate**, and **manual**
lanes using `config/promotion_manifest.json`. Each lane declares the stage,
manager, and Stage RAG helper version plus the regression pack that must stay
green. The manifest also defines lane rules, policy criteria, and the last
promotion decision so the rest of the tooling can enforce the next sensible
stage.

As of manifest `version=3`, the same file also contains `subsystem_levels`,
which tracks current production/candidate/preview posture, next target level,
and required advancement evidence for:
- stage system
- manager system
- retrieval / RAG
- promotion engine
- worker utilization
- regression / qualification framework

## Lanes at a glance

| Lane       | Stage version | Manager version | RAG version | Description |
|------------|---------------|-----------------|-------------|-------------|
| production | `stage3-v1`   | `manager4-v1`   | `rag1-v1`   | Stage-3 literal/comment jobs remain the default production lane. |
| candidate  | `stage5-v1`   | `manager4-v1`   | `rag3-v1`   | Stage-5 dual-file batches gathering telemetry ahead of promotion. |
| manual     | `stage4-v1`   | `manager4-v1`   | `rag2-v1`   | Use Codex/manual workflows for out-of-policy or harness edits. |
| stage6     | `stage6-v2`   | `manager5-v3`   | `rag4-v2`   | Candidate-ready Stage-6 batches with scored secondary selection, per-target literal contracts, and adaptive grouped secondary retry/decomposition. |

The manifest also records the current promotion policy (`candidate_success_threshold`,
`candidate_failure_budget`, the required regression pack, trace window budget,
and the desired lane behaviors) so operators can validate evidence consistently.

## Explicit subsystem version movement

`config/promotion_manifest.json` now includes `subsystem_version_movement`, which explicitly tracks per subsystem:
- `current_version`
- `target_next_version`
- `decision` (`implemented_now`, `held`, `deferred`)
- required code change and minimal validation signal

This keeps version movement operational and auditable instead of “generic improvement” language.

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

## Stage-6 preview and Manager-5 routing

- Manager-5 (`bin/stage6_manager.py`) orchestrates Stage-6 preview runs by
  calling the new Stage RAG-4 planner and then executing up to three
  sequential Stage-5 jobs from a single plan id. Each job reuses the staging
  budget while letting the orchestrator commit the coordinated multi-target
  change.
- Stage RAG-4 (`bin/stage_rag4_plan_probe.py`) wraps the Stage-5 search surface
  plus related-file heuristics to produce multi-target plans with optional
  companion paths. The plan’s payloads feed the Stage-6 manager so the
  operator can glance at the job list before firing off the Stage-5 workers.
- Stage-6 traces (`artifacts/manager5/traces.jsonl`) follow the same `trace-v1`
  schema, recording the plan, job outcomes, lane metadata, and the borrower's
  promotion policy status for auditing.
- The manifest keeps the lane in `preview` status. Operators may sample it
  manually before Stage-6 accumulates enough evidence to promote the lane to
  production.

## Level 7 roadmap reference

- See `docs/level7-roadmap.md` for the Level 7 definitions of the manager and
  retrieval stacks, the current Level 6 gaps, and the first code steps we added
  to move forward (plan history persistence, fallback targets, enriched
  provenance).

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
anticipated policy and highlights missing evidence. In order to reflect the
improved Stage-5 work, qualification counts only the candidate jobs logged
within the manifest’s `trace_window_days`, letting long-past failures fall off
the rolling window as fresh wins arrive.

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

## Unified Level-10 qualification

Use `bin/level10_qualify.py` to score all major subsystems together rather than
checking only the candidate lane.

```sh
python3 bin/level10_qualify.py --manifest config/promotion_manifest.json
```

The report combines:
- lane snapshot (production/candidate/preview),
- candidate + stage6 orchestration success/failure metrics,
- worker success/failure outcomes from Stage-5 traces,
- RAG-4 plan volume and confidence summaries,
- manager plan-lifecycle health from `artifacts/manager5/plans/`,
- subsystem readiness (`ready_for_next_level` vs `needs_more_evidence`).

Roadmap details live in `docs/level10-roadmap.md`.

## Level-10 promotion control loop

Use `bin/level10_promote.py` to consume `bin/level10_qualify.py --json`,
compute objective lane decisions (`promote`, `demote`, `hold`), and update:
- lane statuses in `config/promotion_manifest.json`,
- `promotion_policy.last_decision` and `promotion_policy.history`,
- audit history in `artifacts/promotion/decision_history.jsonl`.

Dry-run mode keeps the manifest untouched while still appending an auditable
decision record:

```sh
python3 bin/level10_promote.py --manifest config/promotion_manifest.json --dry-run
```
