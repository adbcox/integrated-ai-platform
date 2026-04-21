# RM-INV-003 — Execution Pack

## Title

**RM-INV-003 — Live product search, pricing history, and inventory-aware procurement workflow**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-INV-002`, `RM-INV-001`, `RM-GOV-001`

## Objective

Support real product discovery with live listings, availability checks, historical pricing context, watchlists, and future linkage to owned assets and replacement needs.

## Why this matters

This turns the system from passive inventory awareness into active procurement intelligence that can help source real items at the right time.

## Required outcome

- real product/listing discovery
- in-stock confidence
- pricing-history context
- watchlist and alert support
- compatibility-aware recommendations tied to known assets

## Recommended posture

- separate owned-asset truth from market listing data
- preserve provenance, timestamp, and confidence on listing availability
- keep recommendations reviewable rather than auto-purchasing by default

## Required artifacts

- product identity schema
- listing/availability record
- pricing history record
- watchlist state
- compatibility linkage record

## Best practices

- support part numbers, models, and category search
- distinguish in-stock, out-of-stock, and uncertain states
- track why a candidate was recommended
- preserve compatibility linkage to known hardware where possible

## Common failure modes

- stale listing pages treated as live stock
- weak product identity normalization across sellers
- recommendations with no compatibility context
- procurement logic drifting away from inventory truth

## Recommended first milestone

Build the product identity and listing schema first, then add availability and pricing-history layers.
