# Architecture Decision Register

## Purpose

This register records the most important standing architecture decisions in condensed form.

## Core decisions

### ADR-A-001 — Retain the existing control plane
**Decision:** Keep the existing control plane and harden it rather than replacing it before the new runtime substrate is proven.

### ADR-A-002 — Shared runtime substrate is mandatory
**Decision:** Implement a shared runtime substrate beneath the control plane and require branches to use it.

### ADR-A-003 — Ollama-first is the default coding posture
**Decision:** Ollama remains the default first-attempt local coding engine for routine approved work.

### ADR-A-004 — Aider is an adapter, not a backbone
**Decision:** Aider-derived capabilities may be used as controlled adapters or transport/helpers, but may not become the architecture center.

### ADR-A-005 — Claude Code is supervisory or exceptional
**Decision:** Claude Code may assist in planning, review, critique, or explicit escalation, but may not silently become the routine implementation path counted as local autonomy.

### ADR-A-006 — Repo docs are canonical for architecture and roadmap planning
**Decision:** Repo-owned docs remain canonical for architecture and roadmap planning; tools such as Plane are operational overlays rather than the planning source of truth.

### ADR-A-007 — External systems should be adopted where commodity fit is strong
**Decision:** Use adopt/build/hybrid discipline; do not rebuild every commodity platform component.

### ADR-A-008 — Branches may not fork the platform
**Decision:** Domain branches may specialize in tools, adapters, prompts, workflows, and UI, but may not fork the shared runtime, permission model, artifact contract, or backbone logic.
