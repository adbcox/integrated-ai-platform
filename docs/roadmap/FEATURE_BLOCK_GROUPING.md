# Feature-Block Grouping and Shared-Touch Planning

## Purpose

This document defines how roadmap items should be grouped into shared execution packages when they overlap in files, systems, or integration surfaces.

The objective is to reduce:

- repeated file touches
- repeated subsystem churn
- repeated validation passes
- repeated integration work
- inflated total LOE from isolated implementation

## Core rule

A roadmap item must be evaluated in two ways:

1. **Individual execution value**
2. **Grouped execution value** with adjacent items that share the same touch surface

## What counts as a shared touch surface

Grouping candidates should be considered when two or more roadmap items share one or more of the following:

- the same files
- the same file families
- the same subsystem
- the same dashboard or UI shell
- the same inventory or CMDB schema
- the same integration adapter
- the same policy engine
- the same monitoring or reporting surface

## Required grouping analysis fields

Each roadmap item should include:

- `Grouping candidates`
- `Shared systems`
- `Shared file families`
- `Estimated repeated-touch reduction`
- `Grouped LOE estimate`
- `Separate LOE estimate`
- `Bundling recommendation`

## Recommendation types

Use one of:

- `Bundle now`
- `Keep separate`
- `Bundle after substrate exists`
- `Split into shared substrate + separate feature layers`

## Required reasoning

A grouping recommendation must explain:

- why items should or should not be bundled
- what shared files/systems are involved
- whether grouping reduces or increases risk
- whether the grouped package is still coherent and bounded

## Example bundling patterns in this roadmap

### 1. Governance block

Likely grouping candidates:

- `RM-GOV-001` — integrated roadmap-to-development tracking system
- `RM-GOV-002` — recurring full-system integrity review
- `RM-GOV-003` — feature-block package planner

Reason:

These share the roadmap registry, metrics model, naming enforcement, impact-scope model, and CMDB linkage surfaces.

### 2. Ambient dashboard block

Likely grouping candidates:

- `RM-UI-003` — tablet-specialized ambient dashboards
- `RM-UI-004` — ambient tablet display themes
- `RM-HOME-001` — indoor air quality monitoring and purifier automation
- `RM-OPS-003` — outdoor activity readiness display

Reason:

These share tablet dashboard shells, room display surfaces, environment cards, and household-facing reporting widgets.

### 3. Media automation block

Likely grouping candidates:

- `RM-MEDIA-001` — media endpoint health and Plex/app compliance
- `RM-MEDIA-002` — unified media acquisition and watchlist automation

Reason:

These share media-system integrations, dashboard media surfaces, player/client assumptions, and library automation context.

### 4. Inventory and capability block

Likely grouping candidates:

- `RM-INV-001` — AI-generated full hardware inventory
- `RM-INV-002` — photo-driven inventory and capability mapping system

Reason:

These share asset schemas, physical inventory records, capability graphs, and CMDB-adjacent asset identity surfaces.

### 5. Developer autonomy block

Likely grouping candidates:

- `RM-DEV-002` — dual-model inline QC coding loop
- `RM-DEV-003` — bounded autonomous code generation
- `RM-DEV-004` — embedded firmware assistant
n
Reason:

These share execution-loop architecture, model orchestration, validation, and implementation policy surfaces.

## Guardrails

Do not bundle items together just because they are thematically similar.

Bundling should be rejected when:

- overlap is superficial
- the grouped package would become too broad
- the risk increase outweighs touch reduction
- one item is mature and another is still underdefined

## Canonical decision principle

Prefer grouped execution when:

- it reduces repeated touches to the same files/systems
- it lowers total effort compared with separate execution
- it preserves package coherence
- it does not create unacceptable risk or architectural drift
