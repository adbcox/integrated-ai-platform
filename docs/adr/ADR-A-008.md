# ADR-A-008 — Branches may not fork the platform
**Status:** Accepted
**Date:** 2026-04-25
**Source:** docs/architecture/DECISION_REGISTER.md

## Context

The platform supports domain branches (media, home automation, athlete analytics, etc.) that extend the core. Without a rule preventing forks, each branch could diverge the runtime substrate, permission model, or backbone logic, leading to an unmaintainable multi-platform situation.

## Decision

Domain branches may specialize in tools, adapters, prompts, workflows, and UI, but may not fork the shared runtime, permission model, artifact contract, or backbone logic.

## Consequences

- Branches add capabilities, not competing implementations
- Shared runtime (framework/) is platform-wide — branches import, don't copy
- Permission model cannot be branch-specific
- Artifact contracts are platform-wide schemas — branches add fields, don't replace schemas
- New domain branches must file an ADR if they need a runtime substrate change
- This prevents the "snowflake branch" problem where each domain needs its own deployment
