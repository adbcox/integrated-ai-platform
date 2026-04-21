# RM-DEV-001 — Execution Pack

## Title

**RM-DEV-001 — Add Xcode and Apple-platform coding capability to the developer assistant**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-DEV-003`

## Objective

Support Apple-platform development tasks under the same bounded runtime model used by the local development assistant.

## Why this matters

Apple-platform support broadens the practical usefulness of the local assistant without requiring a separate workflow or agent stack.

## Required outcome

- explicit Apple-platform task classes
- bounded build/test/simulator actions
- clear separation between coding, testing, signing, and release-sensitive work

## Recommended posture

- preserve explicit platform/toolchain profiles
- separate codegen from signing and release operations
- treat simulator, test, and archive as distinct execution classes

## Required artifacts

- platform/task descriptor
- scheme/target selection record
- build/test/simulator output
- environment/profile used
- rollback/follow-up note

## Best practices

- always specify scheme/target for actions
- keep signing-sensitive operations gated
- avoid hidden mutation of local Apple development state
- keep simulator and device actions clearly separated

## Common failure modes

- implicit target/scheme selection
- mixing codegen with signing or release logic
- hidden environment changes
- broad project mutation without bounded scope

## Recommended first milestone

Add bounded Apple build/test task classes with explicit scheme/target selection and artifact-complete outputs.
