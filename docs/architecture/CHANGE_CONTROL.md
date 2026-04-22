# Architecture Change Control

## Purpose

This document explains how architecture changes should be introduced without re-fragmenting the repo.

## Core rule

Any material change to core platform direction should update the canonical architecture set in the same change stream.

## What counts as a material architecture change

Examples include:

- changing the default model routing posture
- introducing or replacing a backbone service
- changing authority boundaries
- altering the shared runtime contract
- changing the role of external systems like Aider, Claude Code, Plane, or Home Assistant
- allowing a new branch family to own infrastructure previously defined as shared

## Required update set for major changes

When a material change occurs, update:

- `MASTER_SYSTEM_ARCHITECTURE.md`
- one or more supporting detail docs in `docs/architecture/`
- roadmap alignment docs if the roadmap interpretation changes
- external systems catalog if software-adoption posture changes

## Non-goal

This is not heavy bureaucracy.
It is a safeguard against architectural drift caused by partial updates and scattered notes.

## Reader shorthand

If a change affects platform shape, it should not live only in a prompt, handoff, or execution note.
