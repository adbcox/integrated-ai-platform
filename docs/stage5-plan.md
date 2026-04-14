# Stage-5 Candidate Plan (Draft — April 2026)

Stage 5 = **guarded multi-file patching with contextual retrieval + adaptive
manager orchestration**. The plan below ties directly to the current repo,
harness, and new Stage-4/RAG-2/Manager-3 stack.

## What Stage 5 would enable

- Up to **two files per job** with cumulative diff budget ≤ 30 lines.
- Mixed literal/comment scopes plus small structural rewrites (e.g., inserting a
  helper function and updating its caller).
- Automatic Stage RAG selection: lexical (RAG-1) for small probes, structural
  (RAG-2) plus upcoming embeddings for multi-file edits.
- Manager-3 orchestrates a two-step flow: (1) gather anchors for each file,
  (2) run worker with a combined brief while tracking per-file budgets.
- Regression hooks extend `bin/micro_lane_stage4.sh` to include success cases for
  the promoted class and new rejection cases (multi-file shell control, improper
  diff budgets, etc.).

## Technical work remaining

1. **Guard upgrades**
   - Extend `bin/aider_micro.sh` to enforce per-file diff budgets under a new
     `stage5` flag and to log per-file diff stats. Stage-4 already records diff
     stats in the manager; Stage 5 will move those checks into the guard to catch
     violations even when dispatched outside `stage4_manager.py`.
2. **Retrieval**
   - Enhance Stage RAG-2 with an embedding-backed booster (e.g., fasttext or a
     local MiniLM) stored under `artifacts/stage_rag2/index/`. Use it to surface
     related files (callers/callees) and pass them to Manager-3 as candidate
     secondaries.
3. **Manager orchestration**
   - Promote Manager-3 to take multiple `--target` values, run RAG per file, and
     synthesize a combined worker prompt that names both anchors explicitly. The
     manager should inject “two replacement maximum” text automatically so the
     worker stays bounded.
4. **Validation / Regression**
   - Clone `bin/micro_lane_stage4.sh` into `bin/micro_lane_stage5.sh` with
     success/failure probes for the Stage-5 class.
   - Update `docs/stage4-operator-guide.md` into a unified Stage4/5 doc once the
     new guard proves stable.

## Promotion gate

Stage 5 will be considered production-ready once:

- Two consecutive weeks of Manager-3 telemetry show ≥ 80 % accepted changes for
  the Stage-5 class with <10 % guard rejections.
- Stage RAG-2 (with embeddings) demonstrates <1 per 40 jobs missing anchors.
- Regression packs for Stage 3, 4, and 5 run green on main twice in a row.
- Safety sign-off confirms that diff budgets, rollback, and per-file logging all
  work via automation paths.

This plan assumes the Stage-4 implementation (multi-line literal edits) and
Stage RAG-2 are in place, so Stage 5 can focus on multi-file orchestration
rather than re-solving the structural context problem.
