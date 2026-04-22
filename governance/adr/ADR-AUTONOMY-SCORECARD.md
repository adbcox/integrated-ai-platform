# ADR: Autonomy Scorecard as Model Capability Attribution

## Decision

System capability is measured through autonomy scorecard tracking: first_pass_success, retry_count, escalation_rate, artifact_completeness, and promotion_readiness per task class.

## Rationale

1. **Attribution Clarity**: Separates model capability from wrapper improvement
2. **Measurable Progress**: Can show if local-first quality is actually improving
3. **Promotion Decision**: Objective criteria for whether to expand local-first scope
4. **Learning Signal**: Failure data can be classified and used to improve future work

## Constraints

- Scorecard must track first-attempt quality (not rescued quality)
- Escalation and retry counts must be recorded separately
- Promotion readiness gates must be explicit (e.g., >80% first-pass for task class X)

## Consequences

1. System can measure whether replacement-level capability is being achieved
2. Model improvements are distinguishable from wrapper improvements
3. Promotion decisions become data-driven, not opinion-based
4. Learning system has clear signal on what to improve next
