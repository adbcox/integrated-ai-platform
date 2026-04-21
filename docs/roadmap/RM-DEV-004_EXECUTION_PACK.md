# RM-DEV-004 — Execution Pack

## Title

**RM-DEV-004 — Embedded firmware assistant for Nordic and ESP platforms**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-005`, `RM-HW-001`, `RM-INV-001`

## Objective

Extend the developer assistant into embedded workflows for Nordic and ESP families without creating a parallel execution architecture.

## Why this matters

A large part of your system strategy includes Nordic-based devices and hardware-adjacent software work. Firmware support has to be part of the local development assistant to make the whole platform more useful.

## Required outcome

- explicit firmware task classes for Nordic and ESP
- board/toolchain metadata in artifacts
- bounded build/test/flash/probe flows
- no hidden mutation of hardware state

## Recommended posture

- keep firmware under the same runtime, artifact, and evaluation rules as the rest of the dev assistant
- treat build, flash, probe, and debug as separate execution classes
- preserve board family and target metadata in machine-readable form

## Suggested tool posture

- explicit per-family toolchain profiles
- explicit board definitions and target manifests
- runtime-exposed build/test/flash tools with permission gates

## Required artifacts

- board/target descriptor
- toolchain profile used
- build output
- test/probe result
- flash action log if applicable
- rollback or recovery note

## Best practices

- separate Nordic and ESP flows early
- preserve firmware version and board identity in artifacts
- require operator approval for risky device mutation steps
- keep hardware/board config linked to inventory or CMDB data when available

## Common failure modes

- mixing incompatible board families in one execution path
- hiding flash/probe state changes inside generic tasks
- no record of toolchain version or board target
- destructive or irreversible actions without approval gates

## Recommended first milestone

Build the board/target descriptor and bounded firmware task classes first, before broadening automation depth.
