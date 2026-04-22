# ADR: Session and Job Schema as Runtime Contract

## Decision

The session and job execution model is defined in `schemas/session_job_schema.v1.json` and serves as the canonical runtime contract for all bounded execution work.

## Rationale

1. **Bounded Execution Guarantee**: Every session has explicit scope (allowed_files, forbidden_files, expected_artifacts)
2. **Tool Trace Support**: All tool invocations are traced with permission decisions, inputs, outputs
3. **Artifact Linkage**: Sessions produce measurable artifacts that prove execution
4. **Validation Linkage**: Sessions reference validation steps that must pass before completion
5. **Rollback Semantics**: Every session defines its rollback_rule for safety

## Constraints

- Session scope must be finite and decidable at declaration time
- Forbidden files are immutable during session execution
- All tool calls require permission decision record
- Artifact outputs must exist on disk before session closure

## Consequences

1. Sessions become auditable and reproducible
2. Parallel sessions are isolated by scope boundaries
3. Safety gates are enforceable at tool-invocation time
4. Escalation logic can be deterministic (tool call denies permission → escalate to human)
5. Attribution of work becomes precise and automatic
