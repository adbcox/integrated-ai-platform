# Working Conventions

## Purpose

This document records the practical conventions used when working with the roadmap and its downstream execution artifacts.

## Reference conventions

- Use roadmap IDs such as `RM-GOV-001` consistently.
- Reference roadmap IDs in issues, PRs, execution packs, and implementation summaries.
- Preserve canonical names where they have already been normalized.

## Naming conventions

- Prefer explicit titles over catchy or vague names.
- Keep family/category prefixes consistent.
- Avoid creating duplicate concepts under lightly different wording.

## Issue and PR conventions

- Issues should reference the roadmap ID they execute or decompose.
- PRs should reference the roadmap ID or grouped execution block they implement.
- Execution summaries should distinguish between roadmap decision, implementation scope, and status outcome.

## Summary-surface conventions

- `ROADMAP_MASTER.md` = strategic interpretation
- `ROADMAP_INDEX.md` = backlog inventory
- `ROADMAP_STATUS_SYNC.md` = status truth
- architecture docs = upstream system direction

## Rule

Conventions exist to reduce ambiguity and preserve traceability as the repo grows.
