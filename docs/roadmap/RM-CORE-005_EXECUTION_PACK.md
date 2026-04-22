# RM-CORE-005 — Execution Pack

## Title

**RM-CORE-005 — Identity, secrets, permissions, and trust-boundary management**

## Objective

Define and implement the trust-boundary layer for credentials, secrets, permissions, and scope-limited operations across the platform.

## Why this matters

A local/private agent system still needs strong boundaries around what can access what, under what conditions, and with what audit trail.

## Required outcome

- secrets and credential handling model
- permission/scope model
- trust-boundary definitions
- operator approval classes
- audit linkage for sensitive actions

## Required artifacts

- trust-boundary map
- secret/credential policy
- permission scope schema
- approval class model
- sensitive-action audit template

## Best practices

- separate identity, secrets, and permissions concerns
- keep least-privilege as the default
- make approval classes explicit and machine-readable
- ensure sensitive actions map to audit evidence and telemetry

## Common failure modes

- hidden tokens/secrets in runtime configs or prompts
- no distinction between read-only and mutating scopes
- broad permission grants because the system is local

## Recommended first milestone

Define the trust-boundary map and permission-scope model first, then add approval classes and secret-handling policy.
