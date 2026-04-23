# Local Aider Execution Mode

## Purpose

Use this mode when the local stack is performing bounded implementation through Aider.
This is the default tactical local execution surface for many code and repo-maintenance tasks.

## Best use cases

- bounded bugfixes
- tactical multi-file implementation
- validator-driven repair loops
- local iteration with minimal prompt friction
- smaller connector/workflow implementation work

## Not for

- truth-only closeout audits
- unbounded planning-heavy work without framework decomposition
- using one oversized prompt as a substitute for bounded packetization

## Required reads

1. `docs/governance/CURRENT_OPERATING_CONTEXT.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. relevant canonical item YAML
4. relevant derived planning surfaces when queue/blocker state matters
5. `docs/governance/PROMPT_PACKET_STANDARD.md`
6. `docs/roadmap/items/RM-UI-005.yaml` when model-tier/runbook policy matters

## Operating rules

- local-first by default
- for complex tasks, use framework-first decomposition before tactical execution
- keep context tight and bounded
- use explicit validations and stop conditions
- do not claim completion from patch success alone
- escalate only after the local path proves insufficient

## Expected outputs

- exact files changed
- exact validations run
- exact blocker if unresolved
- exact artifact/truth-surface updates when applicable

## Stop conditions

Stop when:
- the bounded packet is complete and validated, or
- the local path proves insufficient and escalation criteria are met
