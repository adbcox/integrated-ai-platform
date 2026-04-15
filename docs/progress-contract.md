
# Progress Contract

## Purpose

This file exists to prevent drift into measurement-only, roadmap-only, version-label-only, or fixture-only work.

The system must optimize for real capability gain toward the Codex 5.1 replacement milestone and then toward the broader Version 15 goal.

## Approved session types

Every session must declare exactly one primary type:

1. capability_session
2. measurement_session
3. planning_session
4. governance_session

## Session type rules

### capability_session

A capability session is the default.
It exists to make the system materially more capable.

A capability session counts as successful only if at least one of these is true:

* a real capability blocker was fixed and the affected real path was rerun successfully
* a major subsystem version step was implemented in code and proven on real work
* real local-first task completion improved on representative bounded complex tasks
* the Codex 5.1 replacement gap was reduced with evidence from real runs

### measurement_session

A measurement session is allowed only when needed to evaluate a newly implemented code path or replacement-gate metric.

A measurement session does not count as forward progress unless it directly enables the next capability session.

A measurement session must not be repeated back-to-back unless there is a named blocker requiring it.

### planning_session

A planning session is allowed only when:

* a major roadmap decision is needed
* a review gate is explicitly required
* or a dependency order must be clarified before implementation

A planning session must produce a concrete next execution step.
Planning alone is not sufficient progress.

### governance_session

A governance session is allowed only when:

* a promotion gate must be evaluated
* a source-of-truth versioning or rollout decision is required
* or a human review gate is explicitly triggered

A governance session must not become the default operating mode.

## Sessions that do NOT count as real progress

A session does not count as progress if it only produces:

* docs
* roadmap updates
* benchmark plumbing
* curation plumbing
* version renaming
* fixture-only validation
* dry-run-only validation
* summary/report formatting
* promotion math without corresponding capability movement

## Required primary-objective discipline

Every session must declare:

1. primary_session_type
2. primary_objective
3. blocker_or_capability_gap
4. why_this_is_the_highest_leverage_move
5. real_path_to_rerun_before_stopping

Only one primary objective may be active at a time.

## Required real-path rule

No session is complete unless:

* a real local-first path is rerun, and
* the result is used to state a net capability gain,

unless a true external blocker prevents the rerun.

Fixture-only or dry-run-only evidence is acceptable only to prove a newly added code path before the real rerun in the same session.

## Full validation completion rule

After any meaningful code change, a session is incomplete unless it finishes with:

* the affected real-path rerun, and
* the full discovered repo check surface rerun,

unless a true external blocker prevents the full check-surface rerun.

Benchmark green alone is not sufficient.
Real-path success alone is not sufficient.
Capability proof must be paired with repo validation proof.

## Required net capability gain rule

Every final report must include:

1. primary_session_type
2. primary_objective
3. blocker_attacked
4. code_changed
5. real_path_rerun
6. net_capability_gain
7. remaining_blocker
8. repo_clean

If the net_capability_gain field is weak or empty, the session should be considered weak.

## Anti-drift rules

Do not:

* run two measurement sessions in a row unless a named blocker requires it
* run planning sessions repeatedly without capability follow-through
* stop after benchmark improvements alone
* stop after capability-path success alone when full repo validation has not been rerun
* stop after source-of-truth or docs changes alone
* stop after version bookkeeping alone
* optimize reporting over capability movement

## Local-first rule

The local system should do as much real coding work as safely possible.
Codex/manual help should be used to:

* remove blockers
* improve architecture
* enforce governance
* strengthen the system’s ability to replace external help

The local system should not be displaced by Codex for routine in-scope bounded complex work unless a real gate requires it.

## Stop conditions

A session may stop only if one of these is true:

1. the declared capability blocker was fixed, the real path was rerun, and the full discovered repo check surface was rerun after meaningful code changes
2. the declared version step was implemented and proven on real work
3. a true external blocker prevents safe continuation
4. a named human review gate blocks the next step

## Final rule

The system must optimize for actual replacement capability, not just cleaner instrumentation, safer wrappers, or better summaries.

If work does not clearly advance:

* local-first completion,
* first-attempt quality,
* bounded complex task success,
* or trusted evidence for the replacement gate,

then that work is lower priority until a justified review gate says otherwise.
