# Instructions

## Mission

Advance this repository toward the next production-capable stage, not just by measuring the current stage, but by implementing the next useful system layers.

## Operating mode

* Continue working in batches inside the current session until a real stop condition is met.
* Do not stop after a single batch, a summary, or a checklist update.
* Do not treat "more telemetry is needed" as a sufficient reason to stop if safe implementation work remains.

## Priority order

1. Implement code that advances the current architecture.
2. Use the local worker for low-level safe tasks whenever possible.
3. Improve the manager when it limits forward progress.
4. Improve retrieval when it limits forward progress.
5. Run only the minimum validation needed to confirm new code paths work.

## Do not default to

* repeated Stage-3-only telemetry
* repeated summaries
* repeated checklist narration
* stopping because "organic work is scarce"

If organic work is scarce, generate safe repo-grounded promotability tasks.

## Required behavior

* Keep the repo clean between batches.
* Commit meaningful bounded progress immediately.
* If a file change is intended and is the only dirty change, commit it before moving on.
* When a blocker is found, fix it and rerun the relevant path before stopping.

## Worker-first policy

Use the local worker by default for:

* single-file safe edits
* bounded literal/comment changes
* currently promoted task classes

Use Codex directly for:

* manager changes
* retrieval changes
* architecture changes
* broader guarded promotions

## Stage advancement policy

* Stage-3 is not the final goal.
* Reopen Stage-4 as soon as the entry criteria are actually satisfied.
* Once Stage-4 is reopened, stabilize it instead of drifting back to Stage-3-only work.
* Advance retrieval and manager architecture whenever they are the limiting factor.
* Build toward a justified Stage-5 candidate.

## Stop conditions

Stop only if:

1. a true external blocker prevents further safe progress,
2. the repo enters an unrelated inconsistent state that cannot be safely resolved, or
3. the targeted next-stage implementation for the session is complete and no further safe in-session action remains.

Do not stop merely because:

* one batch finished
* you can summarize progress
* a checklist is not yet complete
* telemetry exists
