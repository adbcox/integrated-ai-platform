# Codex 5.1 Replacement Doctrine

Status: active

## Finding 39

`recurrence_rate` requires at least 3 distinct failed tasks before the metric is considered meaningful. Below that floor, retry semantics on a single failed task dominate the ratio and the benchmark reports `recurrence_status=insufficient_data` instead of treating the value as a failure gate.

## Finding 40

Codex 5.x replacement benchmark is passing at the current observed position as of 2026-05-05: `success_rate=0.933`, `rescue_rate=0.067`, `escalation_rate=0.133`, `first_attempt_quality_rate=0.666`, and `recurrence_status=insufficient_data` on a 15-task sample. The recurrence threshold remains available once the run set is expanded to a sufficiently large task population.
