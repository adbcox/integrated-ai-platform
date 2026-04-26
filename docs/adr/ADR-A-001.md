# ADR-A-001 — Retain the existing control plane
**Status:** Accepted
**Date:** 2026-04-01
**Source:** docs/architecture/DECISION_REGISTER.md

## Context

The platform had accumulated a working control plane implementation before the shared runtime substrate was proven. A decision was needed on whether to replace the control plane or harden it.

## Decision

Keep the existing control plane and harden it rather than replacing it before the new runtime substrate is proven.

## Consequences

- Control plane code remains the operational backbone
- Hardening work (security, observability) takes priority over replacement
- Replacement is deferred until runtime substrate is validated
- No parallel implementation of a competing control plane
