# Integrated AI Platform — Roadmap Master

This is the **single master roadmap document** for the repository.

## Authority rule

Use this file as the first-read roadmap document.

- **Canonical roadmap root:** `docs/roadmap/`
- **Single master roadmap document:** `docs/roadmap/ROADMAP_MASTER.md`
- **Normalized backlog index:** `docs/roadmap/ROADMAP_INDEX.md`
- **Roadmap standards:** `docs/roadmap/STANDARDS.md`

If roadmap information appears in more than one place:

1. `docs/roadmap/ROADMAP_MASTER.md` controls overall interpretation and priorities.
2. `docs/roadmap/ROADMAP_INDEX.md` controls normalized item IDs and backlog membership.
3. `docs/roadmap/STANDARDS.md` controls naming, categories, and metrics.
4. Legacy material under `roadmap/` is historical context only unless explicitly migrated.

## Primary objective

The most important roadmap objective is to strengthen the **local development assistant** so the system becomes a highly reliable home developer assistant with minimal dependence on Claude Code or Codex for routine coding work.

## Program-critical pull-first item

### RM-DEV-005 — Local autonomy uplift, OSS intake, and Aider reliability hardening

**Status:** Proposed  
**Priority:** Highest / Program-critical / Pull-first  
**Why it is first:** This is the main force-multiplier item for the whole system. It improves Ollama-first execution quality, Aider reliability, OSS adoption discipline, local artifact quality, and long-term independence from paid external coding agents.

### Pull-first rule

Unless blocked by lower-phase prerequisites, pull work in this order:

1. `RM-DEV-005` — local autonomy uplift, OSS intake, and Aider reliability hardening
2. tightly related lower-phase infrastructure that directly unlocks `RM-DEV-005`
3. other developer-assistant and autonomy items
4. only then, domain-expansion items

### Local development assistant focus set

The highest-value roadmap cluster for the home developer assistant is:

- `RM-DEV-005` — Local autonomy uplift, OSS intake, and Aider reliability hardening
- `RM-DEV-003` — Bounded autonomous code generation
- `RM-DEV-002` — Dual-model inline QC coding loop for the developer assistant
- `RM-INTEL-001` — Open-source watchtower with update alerts and adoption recommendations
- `RM-DEV-004` — Embedded firmware assistant for Nordic and ESP platforms
- `RM-DEV-001` — Add Xcode and Apple-platform coding capability to the developer assistant

These items should be treated as the most strategically important cluster in the roadmap.

## Canonical backlog inventory

The current normalized backlog is maintained in `docs/roadmap/ROADMAP_INDEX.md`.
That file is the canonical inventory of roadmap IDs currently captured in the repo.

## Active roadmap families

### A. Governance / roadmap integrity
- `RM-GOV-001`
- `RM-GOV-002`
- `RM-GOV-003`

### B. Developer assistant / local autonomy / execution
- `RM-DEV-001`
- `RM-DEV-002`
- `RM-DEV-003`
- `RM-DEV-004`
- `RM-DEV-005`
- `RM-AUTO-001`
- `RM-INTEL-001`

### C. Core system / packaging / platform control
- `RM-CORE-001`
- `RM-CORE-002`
- `RM-OPS-001`
- `RM-OPS-002`
- `RM-OPS-003`
- `RM-UI-001`
- `RM-UI-002`
- `RM-UI-003`
- `RM-UI-004`

### D. Inventory / procurement / asset understanding
- `RM-INV-001`
- `RM-INV-002`
- `RM-INV-003`

### E. Domain expansion packages
- `RM-DOCAPP-001`
- `RM-DOCAPP-002`
- `RM-HW-001`
- `RM-HW-002`
- `RM-LANG-001`
- `RM-HOME-001`
- `RM-MEDIA-001`
- `RM-MEDIA-002`
- `RM-MEDIA-003`
- `RM-MEDIA-004`
- `RM-SHOP-001`
- `RM-SHOP-002`
- `RM-SHOP-003`
- `RM-SHOP-004`
- `RM-AUTO-MECH-001`

## Durable storage rule

To prevent roadmap drift or split authority:

- Add all new roadmap items in `docs/roadmap/ROADMAP_INDEX.md`.
- Update priority interpretation in `docs/roadmap/ROADMAP_MASTER.md` when strategic ranking changes.
- Store detailed normalization or chat-derived additions in a dated sync file under `docs/roadmap/`.
- Do not add new canonical roadmap items under the top-level `roadmap/` tree.
- If an item matters operationally, ensure it exists in the normalized index and not only in chat.

## Legacy rule

The top-level `roadmap/` tree is legacy historical material.
It may contain useful execution history, but it is not the canonical normalized roadmap database.

## Reader rule

When in doubt, read files in this order:

1. `docs/roadmap/ROADMAP_MASTER.md`
2. `docs/roadmap/ROADMAP_INDEX.md`
3. `docs/roadmap/STANDARDS.md`
4. any dated sync or execution-context files in `docs/roadmap/`
5. legacy files under `roadmap/` only for historical context
