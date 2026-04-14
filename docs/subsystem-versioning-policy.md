# Subsystem Versioning Policy

`config/promotion_manifest.json` is the source of truth for subsystem version movement.

## Rules
- Create a new version label only when behavior materially changes.
- Do not create version bumps for planning-only updates.
- A valid version step must include at least one of:
  - new code path
  - routing behavior change
  - retrieval behavior change
  - promotion/qualification behavior change
  - safety/guard behavior change
  - operator-visible workflow change

## Required fields
Each subsystem in `subsystem_versions` must define:
- `current_version`
- `next_version`
- `after_next_version`
- `upgrade_goal`
- `minimum_validation`
- `status` (`planned`, `building`, `validated`, `promoted`, `held`)

## Current active next-step targets
- `stage system`: `stage9-v1`
- `manager system`: `manager9-v1`
- `rag system`: `rag9-v1`

These targets are operational commitments and should be changed only when code and validation evidence justify it.
