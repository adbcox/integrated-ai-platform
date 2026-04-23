# n8n Evaluation Boundary

## Wave posture
n8n remains evaluation-only for this first reuse-first wave.

## Bounded fit criteria
Adopt in a future wave only if all are true:
1. It adds measurable capability not already provided by current control-plane + scripts.
2. Workflow definitions can remain governed, versioned, and reviewable in-repo.
3. It does not become a hidden planner or policy authority.
4. Security and secrets handling can stay local-first and auditable.

## Overlap analysis
- High overlap with existing task orchestration wrappers and scripted automation.
- Potential value mainly in operator-facing workflow composition for low-risk non-core automation.

## Adopt vs defer decision for this pass
- Decision: defer broad adoption.
- Reason: immediate capability gain is higher from direct coding/ingestion/PR-path OSS wrappers.
- Explicit rule: no broad n8n deployment in this pass.
