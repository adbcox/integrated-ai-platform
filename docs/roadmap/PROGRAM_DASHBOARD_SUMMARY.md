# Program Dashboard Summary

## Purpose

This document provides an executive-level summary of the program for quick review by a senior technical lead, program manager, or architecture reviewer.

It is intentionally shorter and more decision-oriented than the full architecture and roadmap sets.

## Program identity

The integrated AI platform is a local-first AI development and operations platform whose primary near-term objective is to become a highly reliable home developer assistant built on a shared runtime substrate and an Ollama-first default coding path.

## Upstream authority

Use these documents as the canonical upstream references:

- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md` — architecture truth
- `docs/roadmap/ROADMAP_STATUS_SYNC.md` — roadmap status truth
- `docs/roadmap/ROADMAP_MASTER.md` — roadmap strategic interpretation
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` — external system catalog

## Current top program priorities

### 1. Shared runtime and local autonomy
The main architecture gap remains the missing shared runtime substrate beneath the retained control plane.

### 2. Governance and anti-drift discipline
The roadmap, architecture, and external-system governance layers have been normalized to reduce future drift.

### 3. Inventory and capability awareness
The platform is prioritizing stronger understanding of real-world assets, tools, components, and capabilities.

### 4. Controlled expansion
Domain branches remain valid, but should continue to follow shared-runtime maturity rather than outrunning it.

## Current active strategic cluster

- `RM-AUTO-001`
- `RM-GOV-001`
- `RM-OPS-004`
- `RM-OPS-005`
- `RM-INV-002`

## Governance alignment cluster

- `RM-GOV-006` — hybrid roadmap operations model with Plane
- `RM-GOV-007` — Plane deployment and sync implementation
- `RM-GOV-008` — external application and integration registry

## Major external-system posture

The platform now has a canonical external-systems catalog covering major adopted or integrated systems such as:

- Ollama
- vLLM
- MCP
- Qdrant
- gVisor
- Plane
- GLPI
- Home Assistant
- Plex
- Sonarr
- Radarr
- Prowlarr
- Strava
- ChatGPT / OpenAI surfaces
- Claude Code

## Current program-management strengths

- architecture is now centralized under `docs/architecture/`
- roadmap governance is now centralized under `docs/roadmap/`
- authority surfaces are explicit
- external systems are cataloged
- lifecycle, readiness, dependency, maturity, and hygiene rules now exist

## Remaining high-value normalization work

- bring more active per-item files up to the full item template
- apply queue-rank and maturity normalization more broadly across active items
- verify documentation-pack coverage for external-system-dependent active items
- continue reducing reliance on older legacy planning surfaces

## Reader shorthand

The repo now has a credible architecture-and-roadmap governance system.
The next step is continued item-level normalization against that system, not inventing more meta-framework.
