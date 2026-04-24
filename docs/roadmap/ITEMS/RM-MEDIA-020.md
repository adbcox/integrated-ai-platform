# RM-MEDIA-020

- **ID:** `RM-MEDIA-020`
- **Title:** Media format conversion API
- **Category:** `MEDIA`
- **Type:** `Enhancement`
- **Status:** `Accepted`
- **Maturity:** `M0`
- **Priority:** `Medium`
- **Priority class:** `P3`
- **Queue rank:** `20`
- **Target horizon:** `near-term`
- **LOE:** `M`
- **Strategic value:** `3`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `1`
- **Readiness:** `near`

## Description

Build media format conversion API supporting multiple input/output formats. Enable on-demand conversion with progress tracking and cancellation.

## Why it matters

Format conversion enables:
- compatibility with various systems
- format migration workflows
- user-driven format selection
- integration with external services
- data preservation workflows

## Key requirements

- multi-format input support (20+ formats)
- multi-format output support
- progress tracking and reporting
- cancellation and resumption
- batch conversion workflows
- quality and metadata preservation

## Affected systems

- media processing pipeline
- integration services
- user-facing workflows

## Expected file families

- framework/conversion_api.py — conversion API
- domains/media_conversion.py — conversion logic
- routes/media_api.py — HTTP endpoints
- tests/api/test_conversion.py — API tests

## Dependencies

- `RM-MEDIA-001` — media core infrastructure

## Risks and issues

### Key risks
- format compatibility issues
- lossy conversion quality
- latency for large files

### Known issues / blockers
- none; ready to start

## CMDB / asset linkage

- FFmpeg, libav, format libraries

## Grouping candidates

- none (depends on `RM-MEDIA-001`)

## Grouped execution notes

- Blocked by `RM-MEDIA-001`. Foundational for format handling.

## Recommended first milestone

Implement conversion API for 5 common formats with progress tracking.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: conversion API with progress tracking
- Validation / closeout condition: conversion working for 10+ format pairs

## Notes

Enables flexible media workflows.
