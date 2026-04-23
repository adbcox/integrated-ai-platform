# Claude Code Execution Mode

## Purpose

Use this mode when Claude Code is acting as a bounded implementation executor for work that materially benefits from Claude Code’s environment/tool posture.

## Best use cases

- Apple/Xcode/macOS-specific implementation
- tool-heavy environment-specific changes
- cases where the local path cannot yet complete the task within current capability limits

## Not for

- routine bounded work that the local path can complete
- control-window truth review without implementation need
- replacing canonical repo governance with tool-native workflow assumptions

## Required reads

1. `docs/governance/CURRENT_OPERATING_CONTEXT.md`
2. `docs/roadmap/ROADMAP_AUTHORITY.md`
3. relevant canonical item YAML
4. relevant derived planning surfaces when selection/blocker state matters
5. `docs/governance/PROMPT_PACKET_STANDARD.md`

## Operating rules

- stay within the bounded objective
- preserve canonical repo governance and closeout semantics
- do not treat Claude Code as a separate planning authority
- update canonical, derived, and summary surfaces together when required by the task
- do not accept local-only completion; remote-visible push remains required for accepted closeout

## Expected outputs

- exact work completed
- exact files changed
- exact commands/validations run
- exact blockers if unresolved
- final state relative to the bounded objective

## Stop conditions

Stop when:
- the bounded objective is materially closed, or
- a real hard blocker remains that cannot be resolved in the current environment
