# ADR: Tool System as Permission-Enforcing Gateway

## Decision

All tool invocations pass through a permission decision gate that checks (1) is this tool allowed in this session, (2) are the parameters safe, (3) what is the outcome to record.

## Rationale

1. **Safety by Default**: Tools are blocked unless explicitly allowed in session scope
2. **Attribution Clarity**: Every tool call has an owner (session) and outcome (traced)
3. **Bounded Rescue**: Tool failures are caught, classified, and escalated or recovered
4. **Reproducibility**: Tool outcomes are recorded so sessions can be replayed or analyzed

## Constraints

- All tool definitions must declare required/optional parameters and constraints
- Permission decisions must be made synchronously (no async permission changes mid-session)
- Tool outcomes must be recorded with timestamps and classification

## Consequences

1. Tool system becomes security-first (deny by default)
2. Sessions have measurable "tool surface" (count, diversity, pattern of tool usage)
3. Escalation can be precise ("tool X was denied in session Y because Z")
4. Learning system can categorize failures by tool and outcome type
