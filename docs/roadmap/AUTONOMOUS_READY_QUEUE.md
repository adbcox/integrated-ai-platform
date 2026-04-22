# Autonomous Ready Queue

## Purpose

This document provides a governed shortlist of item classes the AI may consider for autonomous pull once they satisfy readiness and normalization requirements.

## Current preferred queue class

### Tier A — architecture/governance reinforcement
Prefer from this tier first:

- normalized active strategic-cluster items
- governance items that reduce future drift or improve autonomous target selection
- operational evidence and recovery items that increase trust in loop execution

## Current exclusion rule

Do not auto-pull any item that is:

- inventory-only
- title-recovery placeholder
- blocked by missing external documentation packs
- architecture-sequence violating
- too immature to define a bounded first milestone

## Reader shorthand

The autonomous queue is intentionally narrower than the active backlog.
This is a safety feature, not a limitation.
