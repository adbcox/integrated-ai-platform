# ADR-A-007 — External systems should be adopted where commodity fit is strong
**Status:** Accepted
**Date:** 2026-04-25
**Source:** docs/architecture/DECISION_REGISTER.md

## Context

An autonomous AI platform has many subsystem needs (secrets management, project tracking, monitoring, etc.). Building every component from scratch would consume disproportionate effort relative to the platform's differentiating value.

## Decision

Use adopt/build/hybrid discipline. Do not rebuild every commodity platform component.

Adoption is preferred when:
- Commodity fit is strong (mature open-source tool exists that handles the exact use case)
- Integration cost is low (API, MCP server, or simple config available)
- Maintenance burden is acceptable (active upstream, low CVE surface)

Building is preferred when:
- The capability is a differentiator (autonomous execution, local AI routing, CMDB logic)
- No commodity tool fits without significant adaptation
- The build cost is bounded and maintainable

## Consequences

- Vault adopted for secrets (not built)
- Plane CE adopted for roadmap tracking (not built)
- VictoriaMetrics + Grafana adopted for observability (not built)
- Uptime Kuma adopted for uptime monitoring (not built)
- AnythingLLM adopted for semantic doc search (not built)
- Autonomous execution framework, RAG pipeline, CMDB validation → built
- Each adoption decision recorded in docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md
