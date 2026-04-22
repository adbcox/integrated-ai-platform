# ADR: Inference Gateway as Model Selection and Routing

## Decision

Model selection (Ollama vs Claude vs other) is routing through an inference gateway that applies session-level policies and workload-type hints.

## Rationale

1. **Policy Enforcement**: Governance rules can enforce "local-first" or "Claude-only" or hybrid per session
2. **Workload Awareness**: Different task types route to different models (e.g., code generation → local, architecture → Claude)
3. **Fallback Safety**: If primary inference fails, gateway can route to fallback model
4. **Attribution**: Gateway logs which model was used for which task, enabling later analysis

## Constraints

- Model selection decision must be made before prompt execution
- Fallback models must respect the same governance policies as primary
- Inference gateway must record all routing decisions with rationale

## Consequences

1. Model policy becomes enforceable at runtime (not just in planning)
2. Local-first optimization becomes transparent (can see what went local vs. was escalated)
3. Learning system can measure first-attempt quality per model
4. Billing and quotas can be enforced at gateway level
