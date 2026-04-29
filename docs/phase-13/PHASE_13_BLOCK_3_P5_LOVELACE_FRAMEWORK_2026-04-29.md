# Phase 13 Block 3 P5 — Lovelace Dashboard Framework

**Date**: 2026-04-29
**Operator**: claude-opus-4-7[1m]
**Scope**: framework only — area-driven dashboard YAML covering all 15 HA Areas. Auto-populates as devices are paired into areas. No entity_id hardcoding.

---

## Deliverable

| File | Purpose |
|---|---|
| `config/phase-13/lovelace/area-driven-dashboard.yaml` | Full YAML dashboard, 15 views, sections layout, area-filter cards |
| (this doc) | Deployment workflow + design rationale |

---

## Why area-driven, not entity-id-driven

Phase 2 confirmed:
- Areas (15) **survived** the wipe (per P2 lesson #2)
- The single dashboard ("Map") **did not** — clean Lovelace slate
- `device_registry` and `entity_registry` are populated incrementally as integrations are paired

A dashboard that hard-codes `entity_id` references is brittle: it breaks every time an integration is repaired, devices are renamed, or a HACS module changes its naming convention. Area-driven cards (`filter: { include: [{ domain: light, area: kitchen }] }`) auto-populate as new devices are added to the room, with zero edits to this file.

**Cost**: dashboard does not display state on day-zero (no entities yet). **Benefit**: dashboard scales with the home for the lifetime of the platform without YAML churn.

---

## Layout choice: HA `sections` view

HA 2024.3+ `type: sections` views give responsive grids without manual column math. Each view is one Area; each section is one entity-class group (lights, climate, media, sensors, cameras for outdoor areas, cover for the garage).

Headings are explicit (`type: heading`) so empty sections show "no entities" cleanly without breaking the grid.

`show_empty: false` on entity cards suppresses display of empty groups. As devices arrive, they appear automatically.

---

## Per-area view inventory

Total: 15 views, matching all Areas from Phase 2 P2.4 preservation.

| View path | Area ID | Card groups |
|---|---|---|
| `foyer` | `foyer` | lights, climate, media, sensors |
| `kitchen` | `kitchen` | lights, climate, media, sensors |
| `living-room` | `living_room` | lights, climate, media, sensors |
| `master-bedroom` | `bedroom` | lights, climate, media, sensors |
| `master-bathroom` | `master_bathroom` | lights, climate, sensors |
| `master-closet` | `master_closet` | lights, sensors |
| `office` | `office_2` | lights, climate, media, sensors |
| `movie-room` | `movie_room` | lights, media, sensors |
| `workout-area` | `workout_area` | lights, climate, media, sensors |
| `upstairs-hallway` | `upstairs_hallway` | lights, sensors |
| `garage` | `garage` | lights, cover, sensors |
| `mdf` | `office` | sensors, lights |
| `front-porch` | `front_porch` | lights, cameras, sensors |
| `backyard` | `backyard` | lights, cameras, sensors |
| `deck` | `deck` | lights, sensors |

### Area-id quirk (lesson)

HA's actual `area_registry` does **not** slugify the friendly name 1:1. Three views had to be re-mapped after grepping the live registry:

| Friendly name | Slugified guess | Real `area_id` |
|---|---|---|
| Master Bedroom | `master_bedroom` | `bedroom` |
| Office (the desk-room upstairs) | `office` | `office_2` |
| MDF (server closet) | `mdf` | `office` |

Why: when areas were originally created, "Office" was claimed first (and used for what is colloquially the MDF closet — the "office" wifi network signage gave the room its name in HA). The real upstairs office got created second and HA appended `_2` to disambiguate. Master Bedroom likely was originally created as just "Bedroom" and then renamed.

**For future operators**: never assume `slugify(name) == area_id`. Always pull the live registry first:

```python
await cmd(ws, "config/area_registry/list")
```

---

## Deployment workflow (out-of-scope this phase, kept for posterity)

1. SSH or Studio Code Server into HA host. Copy file:
   ```
   /config/dashboards/area-driven.yaml
   ```
2. Edit `/config/configuration.yaml` — add (preserving any existing `lovelace:` block):
   ```yaml
   lovelace:
     mode: storage
     dashboards:
       area-driven:
         mode: yaml
         filename: dashboards/area-driven.yaml
         title: "Areas"
         icon: mdi:home-map-marker
         show_in_sidebar: true
         require_admin: false
   ```
3. `Developer Tools → Reload Lovelace` (or restart HA Core).
4. Verify "Areas" appears in the sidebar with 15 views; each view is empty until devices populate (expected, by design).

---

## Out-of-scope (rolled forward)

- Actual entity-bearing devices in each area (device-population work, multi-block)
- Per-area fine-tuning (camera streaming layouts, room-specific media controls, climate scheduling cards) — those are post-population polish work
- Mobile-app-friendly views (a separate "Mobile" dashboard with simplified layout) — defer to Phase 5.5 or later
- Auth/role-based view visibility (admin-only views for MDF / utility) — defer

---

## Design notes for future operators

- The YAML uses **flow-style mappings inside the cards list** (`{ type: heading, heading: "Lights" }`) to keep the file under ~200 lines while still being valid HA Lovelace YAML. Block-style is fine too — pick one and stay consistent.
- The first view (`foyer`) keeps full block-style mapping as a documentation anchor — it shows the expanded form for readers who haven't seen `filter:` cards before. Other views use compact form for brevity.
- **No card-mod, no `custom:` cards, no HACS-installed Lovelace dependencies.** Only HA core card types — keeps the dashboard portable across HA Core upgrades and reproducible after any wipe (resilient to HACS re-bootstrap state).
