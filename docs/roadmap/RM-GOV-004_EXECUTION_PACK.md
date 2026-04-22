# RM-GOV-004 — Execution Pack

## Title

**RM-GOV-004 — Roadmap dependency graph and next-pull planner**

## Objective

Create a dependency-aware roadmap graph and pull-selection planner so the system can choose the next executable work based on readiness, ranking, dependencies, and grouped execution logic.

## Why this matters

This is the bridge between a backlog and an actual operating system for project execution.

## Required outcome

- dependency graph model for roadmap items
- blocked/unblocked logic
- next-pull planning rules
- grouped execution candidate logic
- machine-readable pull recommendation output

## Required artifacts

- roadmap dependency schema
- pull-planning rules
- blocked-state report
- next-pull recommendation artifact

## Best practices

- distinguish hard dependencies from soft grouping relationships
- preserve canonical roadmap IDs as the graph keys
- ensure planner output can be reviewed, not just auto-executed
- tie pull logic to readiness and priority class, not just priority band

## Common failure modes

- treating every relationship as a hard dependency
- no blocked-state reasoning
- pull recommendations with no explanation or evidence

## Recommended first milestone

Define the dependency graph schema and generate the first blocked/unblocked roadmap report with ranked next-pull candidates.
