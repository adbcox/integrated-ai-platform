# RM-CORE-002 — Execution Pack

## Title

**RM-CORE-002 — Installable edition-builder for the AI system with selectable feature sets for macOS and Windows**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-GOV-001`, `RM-UI-001`, `RM-DEV-005`

## Objective

Create a repeatable edition-builder that can package the integrated AI platform into installable variants with selectable feature sets for macOS and Windows.

## Why this matters

Without a packaging/installability path, the platform remains a repo-centered engineering project rather than a reproducible deployable system.

## Required outcome

- edition/feature-set model
- build/package profiles for macOS and Windows
- explicit inclusion/exclusion rules for features
- installable artifact definitions
- validation rules for packaged editions

## Recommended posture

- separate runtime components from edition packaging metadata
- preserve deterministic build manifests
- keep per-edition feature toggles explicit and machine-readable

## Required artifacts

- edition manifest schema
- feature-set matrix
- package/build profile definitions
- validation checklist per edition

## Best practices

- define core vs optional features clearly
- preserve OS-specific differences explicitly
- keep installers reproducible and versioned
- link packaged editions back to roadmap and capability sets

## Common failure modes

- hidden feature inclusion rules
- per-OS drift in edition behavior
- installable output with no validation matrix
- packaging logic mixed directly into runtime rules

## Recommended first milestone

Define the edition manifest and feature-set matrix first, then add bounded packaging flows for one macOS and one Windows baseline edition.
