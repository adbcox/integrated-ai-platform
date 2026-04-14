# Stage-4 Entry Checklist (April 2026)

The Stage-3 stack (Stage RAG-1 + Manager-2.3 + micro lane harness) remains
production by default. Stage-4 work may only begin after **all** of the
following evidence is collected and reviewed:

## 1. Telemetry Coverage
- ≥40 consecutive Stage-3 jobs logged by `bin/stage3_manager.py` over at least
  5 operator days.
- ≥70 % of those jobs end in `accepted_change` or `aider_exit_recovered`.
- ≤10 % guard-driven skips (`prompt_shape_invalid`, `comment_scope_preflight`,
  `literal_replace_missing_old`) with documented root causes.
- Zero unexplained `other_clean_rejection` or `literal_shell_risky` outcomes.

## 2. Retrieval & Anchor Health
- Stage RAG-1 metrics show `missing_file_ref` + `missing_anchor` combined rate
  <1 per 20 jobs for the same telemetry window.
- At least one refreshed Stage RAG audit demonstrating coverage of newest
  high-churn files (scripts + docs) without embedding support.

## 3. Harness & Guard Validation
- Micro-lane regression pack (`bin/micro_lane_regression.sh`) passes twice in a
  row on main without modifications between runs.
- Manager traces show zero `fallback_blocked_running_script` events in the last
  20 jobs.
- Placeholder-literal probes (with `<token>` text embedded inside quoted
  literals) succeed in at least 3 real jobs, confirming parity between manager
  preflight and harness behavior.

## 4. Stage-4 Boundary Readiness
- Stage-4 rejection pack reviewed and refreshed within the past week; no open
  TODOs.
- Documented mitigation for every 2026 boundary failure class
  (3-line literals, paired comments, shell-control edits, multi-file edits).
- Operator playbook drafted for how to roll back to Stage-3 if Stage-4 probes
  regress.

## 5. Approvals & Change Control
- Telemetry summary circulated in retro or RFC with links to relevant
  `artifacts/stage3_manager/traces.jsonl` plan IDs.
- Explicit approvals from Stage-3 operator lead, micro-lane maintainer, and
  safety owner confirming that these criteria were met and Stage-4 promotion is
  justified.

Only after the checklist is satisfied may Stage-4 tasks move beyond boundary
probes. Until then, Stage-3 must remain the production default.
