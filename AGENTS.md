
# Instructions

Read and follow these documents first, in order, before any major work:

1. docs/progress-contract.md
2. docs/codex51-replacement-gate.md
3. docs/version15-master-roadmap.md
4. docs/subsystem-versioning-policy.md
5. docs/promotion-engine.md

## Mission

Advance this repository toward the Codex 5.1 replacement milestone as the first major strategic gate, and then toward the broader Version 15 goal.

The system must optimize for real capability gain:

* better local-first coding performance
* better first-attempt quality
* better bounded complex-task completion
* better trustworthy attribution of gains

Do not optimize mainly for:

* benchmark plumbing
* docs-only motion
* version-label churn
* telemetry loops
* fixture-only proof
* summary quality

## Primary operating rule

Every session must declare exactly one primary objective and one primary session type.

Allowed session types:

* capability_session
* measurement_session
* planning_session
* governance_session

Default is capability_session.

A session is incomplete unless it satisfies the progress contract in docs/progress-contract.md.

## Required preamble for each session

Before major work, determine internally and then act consistently on:

1. primary_session_type
2. primary_objective
3. blocker_or_capability_gap
4. why_this_is_the_highest_leverage_move
5. real_path_to_rerun_before_stopping

## Capability-first rule

Prefer work that directly improves:

* local-first task execution
* Codex 5.1 replacement benchmark performance
* first-attempt model quality
* bounded complex-task success
* manager/RAG/stage behavior only where it materially supports the above

Do not drift into supporting infrastructure unless it is required by a current blocker.

## Real-path rule

No session is complete unless a real local-first path is rerun and used to state a net capability gain, unless a true external blocker prevents it.

Dry-run-only or fixture-only validation is acceptable only to prove a newly added code path before the real rerun in the same session.

## Full repo validation rule

After any meaningful code change:

* rerun the affected real local-first path,
* rerun the benchmark if relevant,
* rerun the full discovered repo check surface.

Do not stop after only capability proof.
Do not stop after only benchmark proof.
A session is incomplete without full repo validation unless a true external blocker prevents it.

## Versioning rule

Version movement must stay explicit and trackable, but do not create micro-subversions unless a real code-path change landed.

Only change a version label when one of these is true:

* new code path exists
* routing behavior changed
* retrieval behavior changed
* stage behavior changed
* promotion or qualification behavior changed
* safety or operator workflow changed

## Local-first rule

Use the local system as the primary executor for in-scope bounded complex tasks whenever safe.

Use Codex/manual help primarily for:

* architecture
* blocker removal
* governance
* orchestration
* training/attribution pipeline work
* capability jumps the local system cannot yet perform safely

Do not let Codex displace the local system on work the local system should be learning to do.

## Human review gates

Do not proceed without human review for:

* benchmark set definition changes
* pass/fail threshold changes
* model training or fine-tuning rollout
* major promotion-policy changes
* unsafe scope expansion
* declaring the Codex 5.1 replacement milestone passed

## Anti-drift constraints

Do not:

* run two measurement sessions in a row unless a named blocker requires it
* run planning sessions repeatedly without a capability follow-through session
* stop after docs-only progress
* stop after benchmark-only progress
* stop after path-only capability proof when full repo validation has not been rerun
* stop after version-bookkeeping-only progress
* stop after fixture-only validation
* optimize reporting over capability gain

## Preferred order of work

When choosing between options, prefer:

1. fixing a real blocker on a real local-first path
2. implementing the next highest-leverage capability step
3. rerunning the affected real path
4. using existing benchmark/curation tooling on the real artifacts
5. only then making roadmap or governance updates if needed

## Final report requirements

Every final report must include:

1. primary_session_type
2. primary_objective
3. blocker_attacked
4. code_changed
5. real_path_rerun
6. net_capability_gain
7. remaining_blocker
8. repo_clean

## Stop conditions

Stop only if:

1. the declared capability blocker was fixed, the real path was rerun, and the full discovered repo check surface was rerun after meaningful code changes
2. the declared version step was implemented and proven on real work
3. a true external blocker prevents safe continuation
4. a named human review gate blocks the next step

## Final instruction

Optimize for actual replacement capability.

If a task does not clearly move the system toward:

* local-first completion,
* first-attempt model quality,
* bounded complex-task success,
* or trusted evidence for the replacement gate,

then it is lower priority until a justified review gate says otherwise.
