# RM-GOV-009

- **ID:** `RM-GOV-009`
- **Title:** External application connectivity and integration control plane
- **Category:** `GOV`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M3`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `3`
- **Target horizon:** `next`
- **LOE:** `L`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `3`
- **Dependency burden:** `3`
- **Readiness:** `near`

## Description

Build a single external-application connectivity and integration control plane that standardizes how the platform connects to outside applications, APIs, SaaS tools, local services, and adopted OSS systems. This layer should centralize adapter boundaries, auth handling, sync posture, webhook/event intake, rate-limit handling, capability registration, and policy/governance rules so the rest of the platform does not wire external systems ad hoc.

## Why it matters

The platform already depends on or plans to depend on a growing set of external systems such as Home Assistant, Plex, Sonarr, Radarr, Plane, Strava, ChatGPT/OpenAI surfaces, and future adopted tools. Without one governing connectivity layer, integrations will drift into one-off adapters, duplicate auth handling, inconsistent polling/sync behavior, and weak operational visibility. A control plane for external connections reduces that drift and makes future autonomous work safer.

## Key requirements

- define one standard adapter boundary for external applications and services
- centralize auth, credential reference posture, token refresh, and permission boundaries
- define standard patterns for pull sync, push/webhook intake, polling, and event normalization
- support capability registration so the platform knows what each external integration can do
- provide observability and failure handling for external connectors
- keep external systems subordinate to the platform architecture rather than allowing them to become hidden backbones
- remain compatible with MCP where MCP is the preferred boundary

## Affected systems

- roadmap governance layer
- external application catalog and crosswalk surfaces
- future runtime tool/adapter boundaries
- future sync/webhook/event normalization surfaces
- future dashboard and control-center surfaces that consume external integrations

## Expected file families

- `docs/roadmap/*`
- future integration-control-plane architecture docs
- future adapter registry/config files
- future auth/connector policy files
- future sync/event handling surfaces

## Dependencies

- `RM-GOV-008` — external application and integration registry with phased adoption and interface guidance
- `RM-GOV-006` — hybrid roadmap operations layer with Plane on top of repo-doc canonical roadmap
- `RM-GOV-007` — Plane deployment, roadmap field mapping, and repo-to-Plane sync implementation
- shared runtime substrate and external-systems policy

## Risks and issues

### Key risks

- could become overengineered if built before enough common connector patterns are identified
- could accidentally become a second backbone if it tries to own platform logic instead of external connectivity concerns

### Known issues / blockers

- exact first adapter boundary and connector registry model still need to be defined
- auth posture must remain consistent with local-first and governance rules

## CMDB / asset linkage

- should later link external systems to owned hosts, services, devices, accounts, and inventory/CMDB records where relevant
- should support capability-aware planning and impact analysis for integrated services

## Grouping candidates

- `RM-GOV-008`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-GOV-001`

## Grouped execution notes

- Shared-touch rationale: this item overlaps heavily with the external systems registry, operational roadmap layer, governance metadata, and future runtime adapter design.
- Repeated-touch reduction estimate: high if built together with adjacent governance/integration work.
- Grouping recommendation: `Bundle now`

## Recommended first milestone

Define the external connector model for one or two representative systems, including capability registration, auth handling posture, sync/event intake mode, and normalized status/health reporting, then document the control-plane rules those connectors must follow.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: first connector model, adapter boundary, and auth/sync policy are explicitly defined
- Validation / closeout condition: one bounded external connectivity slice exists and becomes the standard pattern for later integrations

## Notes

This item should produce one governing connection model for external systems. It should reduce one-off integrations, not multiply them.