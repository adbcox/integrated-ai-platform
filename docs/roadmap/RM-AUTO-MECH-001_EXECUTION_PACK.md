# RM-AUTO-MECH-001 — Execution Pack

## Title

**RM-AUTO-MECH-001 — Automotive repair and maintenance assistant with broad general knowledge for all cars and deep classic Mercedes specialization**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-INV-002`, `RM-SHOP-003`

## Objective

Create an automotive repair and maintenance assistant that supports broad general vehicle work while providing deeper specialization for classic Mercedes vehicles.

## Why this matters

This is a high-value domain assistant with direct practical use and strong fit with your restoration and repair workflows.

## Required outcome

- automotive task/request schema
- general vehicle knowledge path
- classic Mercedes specialization layer
- parts/tool/procedure linkage where possible
- repair/maintenance handoff artifact model

## Recommended posture

- separate general knowledge from marque-specific depth
- preserve confidence and source/procedure traceability
- link parts, tools, and inventory where relevant

## Required artifacts

- automotive task schema
- vehicle context record
- procedure/support output record
- parts/tool linkage record
- follow-up/handoff summary

## Best practices

- preserve vehicle context explicitly (year/model/system)
- separate general procedural guidance from specialization logic
- keep parts and tool recommendations traceable and reviewable
- link to owned inventory or procurement pathways when relevant

## Common failure modes

- generic advice with no vehicle context
- marque-specific guidance mixed into every workflow indiscriminately
- weak linkage between repair guidance and parts/tools needed
- no distinction between diagnostic support and procedural handoff

## Recommended first milestone

Define the automotive request schema and vehicle-context model first, then add the Mercedes specialization layer and parts/tool linkage.
