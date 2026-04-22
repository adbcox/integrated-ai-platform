# Authority Surfaces

## Purpose

This document defines which repo or system surfaces are authoritative for which kinds of truth.

Its role is to stop architecture, roadmap, status, validation, and deployment truth from drifting into multiple conflicting documents.

## Core rule

No single document should be assumed to control every kind of truth.

Instead, authority is split by concern.

## Architecture truth

**Primary authority:**
- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`

Controls:
- system vision
- architecture principles
- target layered architecture
- phase scheme
- migration logic
- branch-expansion rules
- adopt/build/hybrid posture

## Roadmap planning truth

**Primary authority:**
- `docs/roadmap/ROADMAP_MASTER.md`
- `docs/roadmap/ROADMAP_INDEX.md`
- `docs/roadmap/STANDARDS.md`
- `docs/roadmap/ARCHITECTURE_ALIGNMENT.md`

Controls:
- roadmap interpretation
- backlog inventory
- item IDs/categories/metrics
- grouped execution planning
- architecture-to-roadmap mapping

## Roadmap status truth

**Primary authority:**
- `docs/roadmap/ROADMAP_AUTHORITY.md`
- `docs/roadmap/ROADMAP_STATUS_SYNC.md`

Controls:
- open vs completed vs archived state
- status synchronization across summary surfaces
- conflict resolution for roadmap state questions

## External system truth

**Primary authority:**
- `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`

Controls:
- approved external software catalog
- adoption posture
- official source/API references
- phase/group placement for external systems

## Execution and implementation truth

**Primary authority:**
- execution packs
- validation artifacts
- implementation-specific evidence files

Controls:
- exact implementation scope for a given package
- produced files/artifacts
- validations run
- execution-specific closeout evidence

## Release and promotion truth

**Primary authority:**
- promotion manifest and release/promotion artifacts

Controls:
- release authority
- promotion decisions
- qualification/progression evidence

## Runtime inventory / CMDB truth

**Current authority:**
- repo-owned CMDB-lite / governance registry surfaces where present

**Future authority:**
- later broader CMDB platform once phase maturity justifies it

Controls:
- phase and subsystem inventory
- runtime contract inventory
- adapter posture
- migration map and waivers where explicitly represented

## Handoff document role

Handoff documents are:
- explanatory
- planning-supporting
- historically important

They are **not** final machine authority once their durable content has been normalized into repo-owned canonical surfaces.

## Reader rule

When uncertain:

1. identify what kind of truth you need
2. go to the matching authority surface
3. do not infer authority from convenience or file prominence alone
