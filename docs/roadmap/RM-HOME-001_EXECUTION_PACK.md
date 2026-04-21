# RM-HOME-001 — Execution Pack

## Title

**RM-HOME-001 — Indoor air quality monitoring and purifier automation app with Home Assistant integration**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-OPS-001`, `RM-UI-001`

## Objective

Create a Home Assistant-linked indoor air quality monitoring and purifier automation app that can observe, decide, and act on air-quality conditions.

## Why this matters

This is a practical home-operations domain capability with direct sensor/automation value and strong fit with the control-center and monitoring stack.

## Required outcome

- indoor air-quality state model
- purifier automation logic
- Home Assistant integration pattern
- user-visible app/control surface

## Recommended posture

- separate sensed state from automation decisions
- keep Home Assistant integration explicit and bounded
- preserve manual override and visible automation rationale

## Required artifacts

- sensor/state schema
- automation rule model
- Home Assistant entity/service linkage
- user-visible action/status record

## Best practices

- preserve thresholds and automation rules explicitly
- surface both current state and why an action occurred
- keep manual override and safety posture clear
- align app UI with the same underlying state model used by automations

## Common failure modes

- hidden automation with no visible rationale
- state and automation logic diverging from UI state
- weak linkage to Home Assistant entities/services
- purifier control with no clear threshold or debounce logic

## Recommended first milestone

Define the air-quality state model and automation-rule schema first, then wire the Home Assistant integration and visible app surface.
