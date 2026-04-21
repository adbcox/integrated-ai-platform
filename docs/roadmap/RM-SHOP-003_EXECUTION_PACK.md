# RM-SHOP-003 — Execution Pack

## Title

**RM-SHOP-003 — 3D model inventory, reuse, and external sourcing library**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-SHOP-002`, `RM-SHOP-004`

## Objective

Create a 3D asset library that inventories local models, enriches them with metadata, supports whole-model and partial reuse, and connects to trusted external model sources.

## Why this matters

This prevents repeated rebuilding from zero and turns existing and external 3D models into reusable design assets.

## Required outcome

- local model inventory
- semantic metadata and compatibility tags
- partial/whole reuse path
- external repository sourcing path
- provenance and lineage tracking

## Recommended posture

- separate capture/reconstruction from asset-library logic
- preserve provenance, licensing, and derived-work lineage
- support both exact reuse and reference-only reuse

## Required artifacts

- model inventory schema
- metadata/tag schema
- reuse/composition record
- external source record
- provenance/licensing record

## Best practices

- keep stable asset IDs
- preserve aliases for mislabeled models
- track compatibility context for bike mounts, vehicle parts, fixtures, etc.
- keep source and lineage explicit for composites

## Common failure modes

- local model files with no normalized metadata
- external models imported with no provenance/license tracking
- no distinction between reusable component and reference-only geometry
- weak searchability because tags are too shallow

## Recommended first milestone

Define the local inventory schema, metadata/tag model, and provenance rules first, then add external-source linkage.
