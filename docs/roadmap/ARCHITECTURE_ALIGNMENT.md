# Architecture to Roadmap Alignment Guide

## Purpose

This document explains how the roadmap should be interpreted against the master architecture source of truth.

Use it to keep planning aligned with the platform architecture instead of letting roadmap execution drift into a separate planning universe.

## Primary architecture source

The roadmap is downstream of:

- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`

If a roadmap interpretation conflicts with the master architecture, the architecture controls unless there is an explicit approved architecture update.

## Core alignment rules

### 1. Shared runtime first

Roadmap items that materially support the shared runtime, inference gateway, workspace/tool/permission model, artifact contract, and developer-assistant proof path should be prioritized ahead of broad branch expansion.

### 2. Ollama-first remains the default execution posture

No roadmap item should be interpreted in a way that silently displaces the local Ollama-first route as the routine default coding path.

### 3. Branches may not invent new backbones

Roadmap items in media, home, athlete analytics, inventory, translation, hardware, or other branch families must sit on top of the shared substrate and may not create parallel execution/control architectures.

### 4. Governance items are architectural support items

Governance items such as roadmap tracking, naming integrity, grouped execution planning, Plane rollout, and the external application registry are important, but they remain supporting layers around the architecture rather than substitutes for runtime completion.

### 5. External software must be cataloged, not improvised

Whenever the roadmap depends on external software, the dependency should be represented in `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` with:

- official source link
- API or integration docs
- adoption posture
- phase/group placement
- local integration pattern

## Architecture priority to roadmap family mapping

### Shared runtime / local autonomy priorities

Most directly supported by:

- `RM-AUTO-001`
- `RM-DEV-001`
- `RM-OPS-004`
- `RM-OPS-005`
- relevant future runtime-specific execution packs

### Governance and anti-drift priorities

Most directly supported by:

- `RM-GOV-001`
- `RM-GOV-002`
- `RM-GOV-003`
- `RM-GOV-006`
- `RM-GOV-007`
- `RM-GOV-008`

### Inventory / capability-awareness priorities

Most directly supported by:

- `RM-INV-001`
- `RM-INV-002`
- `RM-INV-003`

### Domain expansion priorities

These are valid but should generally follow substrate maturity:

- `RM-HOME-*`
- `RM-MEDIA-*`
- `RM-SHOP-*`
- `RM-AUTO-MECH-*`
- `RM-LANG-*`
- `RM-HW-*`
- `RM-DOCAPP-*`

## Practical reader sequence

When trying to decide what should be worked next:

1. read `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`
2. read `docs/roadmap/ROADMAP_STATUS_SYNC.md`
3. read `docs/roadmap/ROADMAP_MASTER.md`
4. read `docs/roadmap/ROADMAP_INDEX.md`
5. read `docs/roadmap/EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md` if external systems are involved

## Rule

If a roadmap item is exciting but does not support or at least respect the architecture master, it should be decomposed, delayed, or re-scoped before execution.
