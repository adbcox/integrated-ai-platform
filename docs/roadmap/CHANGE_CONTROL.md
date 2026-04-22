# Roadmap Change Control

## Purpose

This document defines how roadmap changes must be recorded so backlog interpretation, status, and sequencing do not drift across files.

## Core rule

Any material roadmap change should update the canonical roadmap set in the same change stream.

## Material roadmap changes include

- adding a new roadmap item
- changing item priority or queue order
- changing strategic cluster interpretation
- changing grouping recommendations
- changing external-system posture for a roadmap-dependent system
- changing status in a way that affects active/closed interpretation

## Minimum update set

Depending on the change, update:

- `ROADMAP_INDEX.md`
- `ROADMAP_MASTER.md`
- `ROADMAP_STATUS_SYNC.md`
- per-item file under `ITEMS/`
- `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`
- `EXTERNAL_SYSTEM_TO_ROADMAP_CROSSWALK.md`

## Rule

Do not let roadmap truth live only in chat, temporary notes, or execution artifacts.
