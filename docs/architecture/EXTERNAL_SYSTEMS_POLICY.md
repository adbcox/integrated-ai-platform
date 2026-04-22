# External Systems Policy

## Purpose

This document defines how the platform decides whether to build, adopt, wrap, or defer external systems.

It exists to keep software-adoption decisions consistent across roadmap work, architecture evolution, and branch expansion.

## Core rule

The platform is not trying to rebuild every commodity capability.

External systems should be adopted when they are a strong fit for commodity infrastructure or clearly superior specialized surfaces, provided they do not displace the platform’s architectural backbone.

## Decision categories

### Build

Use `Build` when the capability is core differentiating system logic, especially when it controls:

- inference routing policy
- workspace or permission logic
- artifact contract
- validation/promotion behavior
- autonomy reporting
- governance-specific logic

### Adopt

Use `Adopt` when a strong open-source system already provides the commodity capability and local ownership is not strategically necessary.

### Hybrid

Use `Hybrid` when an external system is adopted, but a repo-owned wrapper, adapter, policy layer, or orchestration layer must sit around it to keep the architecture coherent.

### Conditional

Use `Conditional` when the system may be useful later, but should only be adopted if evidence justifies the complexity.

### Reference only

Use `Reference only` for systems that matter contextually but are not yet approved as dependencies or do not currently have a supported integration path.

## Required checks before adoption

Before an external system is approved for meaningful use, capture:

- official source / repository URL
- official API or integration docs if they exist
- install or deployment path
- architecture role
- whether it is adopt, hybrid, conditional, or reference only
- rollback/removability posture
- whether it threatens any non-negotiable architecture rule

## Non-negotiable policy rules

### 1. External systems may not silently replace the backbone

No external system may silently replace:

- the control plane
- the shared runtime substrate
- the Ollama-first default coding policy
- the artifact and validation model
- the roadmap/architecture source-of-truth model

### 2. Aider remains an adapter, not the backbone

Aider-derived capabilities may be used through controlled adapters, especially for RepoMap or edit primitives, but may not become the architecture center.

### 3. Claude Code remains supervisory or exceptional

Claude Code may support review, planning, critique, or explicit escalation. It may not become the default implementation engine for routine work that is supposed to prove local autonomy.

### 4. CMDB adoption is phase-gated

A larger CMDB system may be adopted only when runtime and governance maturity justify it. It must not outrun the core substrate work.

### 5. Domain apps should integrate, not over-rebuild

When a mature external system already exists for a specialized role — for example Home Assistant, Sonarr, Radarr, Plex, Strava, or roadmap operations tooling — the preferred pattern is usually integration plus repo-owned policy/UI/orchestration rather than full rebuild.

## Catalog rule

All approved or actively considered external systems must appear in:

- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

That file is the running catalog.
This file is the policy explanation behind it.

## Reader shorthand

Use external systems aggressively for commodity or specialized capability.
Do not let them take over the core platform identity.
