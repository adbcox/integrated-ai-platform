# AGENTS.md — Session Discipline and Operating Rules

Every agent execution session must follow this discipline.

## Required Preamble

Before major work, declare:

1. **primary_session_type**: capability_session | measurement_session | planning_session | governance_session
2. **primary_objective**: Single focused goal (not "improve everything")
3. **blocker_or_capability_gap**: What specific problem are we solving?
4. **why_highest_leverage**: Why is this the strongest next move?
5. **real_path_to_rerun**: What will we validate against?

## Mission

Build real local-first coding capability. Optimize for:

- Better bounded task completion
- Better first-attempt code quality
- Better token efficiency
- Trustworthy capability gains

Do NOT optimize for:

- Docs-only motion
- Benchmark plumbing
- Fixture-only proof
- Summary quality without real work

## Core Operating Rules

### 1. Bounded Slice Rule

- Every task must have finite scope
- Scope defined by: allowed_files, forbidden_files, expected_artifacts
- No "improve everything" tasks

### 2. Artifact-Driven Rule

- Execution proves itself with artifacts
- Expected artifacts listed in execution control template
- No completion claim without artifacts

### 3. Real-Path Validation Rule

- Code changes require validation on real code paths
- Fixture-only proof is acceptable only for new code paths before real rerun in same session
- Sessions incomplete without real-path validation on meaningful changes

### 4. Full Repo Validation Rule

After meaningful code changes:

1. Run `make check` (syntax validation)
2. Run `make quick` (fast affected checks)
3. Run `make test-offline` (real-path validation)
4. Report: all pass or all fail (no partial claims)

### 5. Ollama-First Rule

- Use local Ollama for in-scope bounded work
- Use Claude API for architecture, blocker removal, governance
- Never let external models displace the local system

### 6. Anti-Drift Constraints

Do NOT:

- Run two measurement sessions in a row without a capability session
- Stop after docs-only progress
- Stop after fixture-only validation
- Stop after version-bookkeeping without real capability
- Reopen accepted work without regression evidence

## Session Success Criteria

Session is COMPLETE when:

1. Primary objective addressed with evidence
2. Real local-first path rerun and validated
3. All expected artifacts produced
4. Full repo validation passes
5. Remaining blockers identified or none exist

Session is INCOMPLETE if:

- Only docs created, no code
- Only fixtures validated, no real paths
- Only benchmark proof, no artifact proof
- Blockers remain unaddressed without clear reason

## Execution Checklist

1. **Pre-execution**:
   - ✓ Read CLAUDE.md (operating rules)
   - ✓ Read docs/agent/commands.md (available commands)
   - ✓ Read docs/agent/validation_order.md (exact sequence)
   - ✓ State primary_session_type and primary_objective

2. **During execution**:
   - ✓ Modify only files in allowed_files
   - ✓ Never modify forbidden_files
   - ✓ Create all expected_artifacts
   - ✓ Follow validation_order exactly

3. **Post-execution**:
   - ✓ Run full validation (make check + make quick + make test-offline)
   - ✓ Verify all artifacts exist and are correct
   - ✓ Report completion with: session_type, objective, artifacts, validation_results

## Failure Mode

If validation fails:

1. Stop immediately
2. Apply rollback_rule
3. Report failure with exact error
4. Do not continue

## Final Report Template

Every session report MUST include:

1. primary_session_type
2. primary_objective
3. blocker_attacked
4. code_changed (yes/no)
5. real_path_rerun (which tests)
6. artifacts_produced (list)
7. validation_results (pass/fail)
8. remaining_blocker (or "none")
9. repo_clean (working tree status)

## Stop Conditions

Stop ONLY if:

1. Primary objective achieved AND real path validated AND full repo validation passes
2. External blocker prevents safe continuation
3. Human review gate blocks next step
4. Remaining work requires unsafe expansion

Stop immediately if:

- Validation fails at any step
- Forbidden files would be modified
- Artifact integrity compromised
- Session scope exceeded
