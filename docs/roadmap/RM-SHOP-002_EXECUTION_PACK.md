# RM-SHOP-002 — Execution Pack

## Title

**RM-SHOP-002 — 3D capture, guided measurement, and reconstruction stack**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-SHOP-003`, `RM-SHOP-004`

## Objective

Build a 3D workflow that supports guided photo capture, room-scale measurement, scanner integration, and object-scale reconstruction.

## Why this matters

This turns 3D capture from an ad hoc toolset into a structured capability that supports room planning, reconstruction, and future design work.

## Required outcome

- guided capture workflow
- room-scale measurement path
- scanner import/integration path
- object-scale reconstruction path
- confidence/calibration layer

## Recommended posture

- separate room-scale and object-scale flows
- preserve scanner-derived versus image-estimated distinction
- keep calibration and confidence explicit

## Required artifacts

- capture request schema
- scan/import record
- reconstruction output record
- measurement confidence metadata
- handoff bundle for downstream design/layout

## Best practices

- require capture guidance by use case
- preserve source imagery and scanner provenance
- distinguish estimated measurements from higher-confidence scans
- keep outputs suitable for later modeling/layout workflows

## Common failure modes

- collapsing room-scale and object-scale workflows into one generic path
- no scale reference or calibration metadata
- no provenance between photo-derived and scanner-derived geometry
- outputs not reusable by downstream design systems

## Recommended first milestone

Define the capture schema, measurement-confidence model, and separation of room-scale versus object-scale workflows first.
