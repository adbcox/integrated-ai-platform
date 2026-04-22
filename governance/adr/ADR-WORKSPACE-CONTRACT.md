# ADR: Workspace Contract as Execution Boundary

## Decision

Every session declares a workspace contract that binds it to a repo directory, git branch, and set of allowed paths. This contract is immutable for the session duration.

## Rationale

1. **Clear Boundary**: Sessions cannot drift into unrelated code or unintended repos
2. **Rollback Anchor**: Every session knows its starting state and can roll back if needed
3. **Concurrent Safety**: Multiple sessions can execute in isolation if they have different workspace contracts
4. **Authority Clarity**: Workspace contract makes git state, branch, and file access explicit

## Constraints

- Workspace contract is set at session start and immutable during session
- All file paths are resolved relative to workspace root
- Forbidden files are declared relative to workspace root
- Git state (branch, ahead/behind) is recorded at session start

## Consequences

1. Sessions become truly isolated in file access (if different repos/branches)
2. Rollback is scoped to the session's workspace (clean, deterministic)
3. File access auditing becomes simple (all accesses are within contract bounds)
4. Concurrent local execution becomes safer (isolated workspaces per session)
