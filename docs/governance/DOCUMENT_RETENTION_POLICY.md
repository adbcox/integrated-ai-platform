# Document Retention Policy

## Purpose

This document defines how repository documents should be retained, archived, superseded, or retired to reduce confusion and search cost while preserving auditability.

## Retention classes

### Keep as canonical
Retain indefinitely while active.
Examples:
- architecture source of truth
- canonical item YAML
- authority model docs

### Keep as derived active
Retain while synchronized and useful.
Examples:
- queue/blocker/dependency projections
- synced human-readable status rollups

### Keep as operating
Retain while they define current posture or execution routing.
Examples:
- current operating context
- post-convergence operating mode
- execution router
- tool-mode docs
- prompt packet standard

### Mark historical
Preserve for audit or transition context, but clearly label as historical.
Examples:
- superseded transition plans
- once-current strategy docs no longer used as live posture

### Archive
Retain only for audit/history/reference if needed.
Move or clearly mark as archived.

### Retire/Delete
Remove when all are true:
- not canonical
- not required for audit/history
- fully superseded
- no active process depends on it

## Rules

1. Do not delete canonical sources casually.
2. Do not keep superseded planning docs unlabeled; mark them historical or archive them.
3. If a summary doc is duplicated elsewhere and no longer adds value, retire it or reduce it to a pointer.
4. If a document remains only for history, label that explicitly at the top.
5. Every archived or historical doc should point to the current replacement when one exists.
6. Keep document-governance metadata updated in `DOCUMENT_STATE_INDEX.md`.

## Required archival markings

Historical or archived docs should state:
- status: historical or archived
- why preserved
- what current document supersedes it
- whether it should still be read by default (usually no)

## PMP-style objective

The repository should have:
- one clear canonical source for each state domain
- one clear operating posture for the current phase
- minimal duplicate summaries
- explicit historical preservation where needed
- minimal search ambiguity for human and machine consumers
