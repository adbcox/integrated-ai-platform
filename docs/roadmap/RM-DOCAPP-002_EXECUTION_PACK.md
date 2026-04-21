# RM-DOCAPP-002 — Execution Pack

## Title

**RM-DOCAPP-002 — AI-assisted website generation, SEO, and analytics delivery stack**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-CORE-002`, `RM-UI-001`

## Objective

Create a website-delivery workflow that can generate, optimize, and instrument deployable websites using adopted OSS tools rather than building a custom site-builder platform.

## Why this matters

This is one of the strongest commercially useful domain packages and should be execution-ready with clear adopt/build boundaries.

## Required outcome

- OSS-backed generation workspace
- SEO/discoverability workflow
- analytics instrumentation path
- template packs for priority verticals
- deployable artifact bundle and handoff package

## Recommended posture

- adopt builder/editor surfaces rather than rebuilding a page builder
- preserve clear separation between generation, optimization, analytics, and deployment handoff
- keep outputs editable and reviewable

## Required artifacts

- site request schema
- generation artifact bundle
- SEO audit/report structure
- analytics configuration artifact
- vertical template pack definitions

## Best practices

- keep sites editable after generation
- separate generic templates from vertical packs
- preserve source content, generated assets, and audit results together
- require discoverability and measurement support as part of the workflow

## Common failure modes

- treating generated HTML as sufficient with no editability or handoff structure
- missing SEO remediation loop
- analytics bolted on with no clear profile/config layer
- custom-building tools that already exist as OSS

## Recommended first milestone

Define the site request schema, artifact bundle, and vertical template structure first, then wire generation, SEO, and analytics into one bounded flow.
