# Codex Execution Mode

## Purpose

Use this mode when Codex is acting as a **bounded implementation executor**.
This mode is for structured multi-file work, document/governance normalization, and repo-visible implementation under explicit scope.

## Best use cases

- bounded roadmap item implementation
- repo-wide document normalization
- governance and summary-surface reconciliation
- explicit execution-package work
- structured multi-file edits where a strong repo-wide view helps

## Not for

- ambiguous truth-only review without implementation need
- open-ended ideation without bounded scope
- work that is better handled as tactical local iteration in Aider

## Required reads

1. `docs/governance/CURRENT_OPERATING_CONTEXT.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. relevant canonical item YAML
4. relevant derived planning surfaces
5. `docs/governance/PROMPT_PACKET_STANDARD.md`

## Operating rules

- stay bounded to the defined objective
- fix directly connected gaps in the same pass when safely possible
- update canonical, derived, and summary surfaces together when the task requires it
- do not claim completion unless the canonical closeout condition is satisfied
- use validator outputs and artifact evidence, not narrative optimism

## Expected outputs

- exact work completed
- exact files changed
- exact validations run
- exact truth surfaces updated
- final result state and remaining blockers if any

## Stop conditions

Stop when:
- the bounded objective is materially closed, or
- a real hard blocker prevents truthful continuation
