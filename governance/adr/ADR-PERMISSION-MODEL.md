# ADR: Permission Model as Role-Based Tool Access Control

## Decision

Tool access is controlled through a role-based permission model where sessions declare their role (and inherit permissions), and tool access is checked against role + specific tool + parameter constraints.

## Rationale

1. **Predictable Security**: Permissions are declarative, not contextual
2. **Auditability**: Every permission check is recorded with outcome
3. **Consistency**: Same role always gets same permissions (reproducible)
4. **Escalation Clarity**: Denied tool = clear reason (role X cannot call tool Y for parameter type Z)

## Constraints

- Roles must be predefined (no ad-hoc permissions)
- Tool parameters must have permission constraints (required, optional, range, enum)
- Permission checks must be synchronous and atomic

## Consequences

1. Sessions become security-classifiable (which role → what capabilities)
2. Permission denials become actionable escalation signals (need human to approve higher role)
3. Concurrent sessions with different roles have different capabilities
4. Learning system can categorize work by role and success rate
