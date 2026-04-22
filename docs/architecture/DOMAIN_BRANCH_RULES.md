# Domain Branch Rules

## Purpose

This document defines how domain branches may expand on top of the integrated AI platform without fragmenting the architecture.

## Core rule

Domain branches are allowed to vary in domain logic, tools, workflows, prompts, adapters, reporting, and UI.

They are not allowed to create new platform backbones.

## What a branch may add

A branch may add:

- domain-specific tools
- external-service adapters
- branch-specific prompts
- branch-specific workflow logic
- branch-specific UI or dashboards
- domain reporting and policy layers
- branch-local data models where they do not replace shared runtime contracts

## What a branch may not replace

A branch may not replace or fork:

- the shared runtime substrate
- the session/job contract
- the workspace controller model
- the permission model
- the artifact bundle contract
- the release/promotion evidence model
- the architecture source-of-truth model

## Typical branch families

Examples of valid branch families include:

- developer assistant
- media control and automation
- athlete analytics
- environmental monitoring and automation
- inventory and capability mapping
- spreadsheet/document-to-app conversion
- embedded hardware/electrical design support
- language and translation tools
- woodworking and project-planning tools
- automotive repair and restoration support
- meeting/office automation

## External-system rule

Branches are encouraged to integrate mature external systems where appropriate.

Examples:

- media branch integrates Plex, Sonarr, Radarr, Prowlarr
- home/environment branch integrates Home Assistant
- athlete branch integrates Strava
- roadmap operations branch integrates Plane

The platform should own:

- policy
- orchestration
- data normalization
- governance
- local user experience surfaces

It should not rebuild every external system from scratch.

## Expansion sequence rule

Branch expansion should generally follow substrate maturity.

This means:

1. shared runtime first
2. developer assistant proof
3. evidence and governance hardening
4. controlled domain expansion

## Roadmap interpretation rule

A roadmap item in a branch family should be delayed, decomposed, or re-scoped if it implicitly requires a new backbone rather than a branch-level capability.

## Reader shorthand

Branches are free to specialize.
They are not free to fork the platform.
