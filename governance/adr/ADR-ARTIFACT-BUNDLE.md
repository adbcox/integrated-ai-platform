# ADR: Artifact Bundle as Session Deliverable and Proof

## Decision

Every session produces an artifact bundle containing: code changes, validation results, traces, and metadata. Artifact bundle is the proof that work happened.

## Rationale

1. **Completion Proof**: Artifacts on disk prove execution succeeded
2. **Validation Integration**: Artifacts include validation results (tests pass, checks pass, etc.)
3. **Traceability**: Artifacts link to session metadata (who, when, what, why)
4. **Replayability**: Artifacts can be used to understand and replay what happened

## Constraints

- All expected artifacts must exist on disk before session closure
- Artifacts must be valid (parseable, not corrupt)
- Artifact metadata must include session_id, timestamp, owner

## Consequences

1. "Completion" becomes objectively measurable (artifacts exist and are valid)
2. No claim without evidence (docs-only progress is not completion)
3. Artifacts can be cached, analyzed, and learned from
4. Failed sessions have audit trail (what artifacts were partially created)
