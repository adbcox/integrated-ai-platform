# RM-HW-001 — Execution Pack

## Title

**RM-HW-001 — AI-assisted electrical design workflow for ESP32 and Nordic hardware**

## Canonical relationship

- Master roadmap authority: `docs/roadmap/ROADMAP_MASTER.md`
- Normalized backlog entry: `docs/roadmap/ROADMAP_INDEX.md`
- Related items: `RM-DEV-004`, `RM-INV-002`

## Objective

Create a hardware/electrical design-assist workflow for ESP32 and Nordic-based projects that can support design reasoning, artifact capture, and later implementation handoff.

## Why this matters

This extends the platform into one of its most important hardware-adjacent workstreams while keeping it connected to the broader local development assistant and device roadmap.

## Required outcome

- electrical design request schema
- platform-family aware workflows for ESP32 and Nordic
- artifact model for design assumptions, calculations, and outputs
- handoff structure for implementation and review

## Recommended posture

- separate electrical reasoning/design support from firmware execution
- preserve platform-family distinction explicitly
- keep generated recommendations reviewable and assumption-heavy rather than overconfident

## Required artifacts

- design request schema
- design output record
- assumptions/constraints record
- review/handoff summary

## Best practices

- separate Nordic and ESP design paths
- preserve part assumptions, interfaces, and constraints explicitly
- keep calculations and design rationale machine-readable where practical
- tie outputs to downstream firmware/hardware tasks when relevant

## Common failure modes

- blending firmware and electrical design into one vague workflow
- missing assumptions and part constraints
- no clear handoff from design guidance to implementation work
- overconfident generated output with weak traceability

## Recommended first milestone

Define the electrical design request schema and family-specific constraint model first, then add bounded design-output artifacts.
