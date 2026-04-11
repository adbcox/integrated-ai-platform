# Aider Task Brief

## Task Name
<short-name>

## Objective
<what to change>

## Why
<expected value>

## Scope
- In-scope files:
  - <path>
- Out-of-scope:
  - network/firewall/service exposure changes
  - secrets/config material

## Constraints
- keep behavior unchanged unless robustness bug is fixed
- prefer small, reversible patch
- preserve existing script output shape where possible

## Acceptance Criteria
- local checks pass (`make quick`)
- behavior checks pass (`make test-changed-offline` or `make test-offline`)
- changed files are explicitly listed

## Validation Commands
```sh
make quick
make test-changed-offline
```

## Notes For Remote Codex
- return patch-oriented changes
- list modified files
- include short rationale per file
