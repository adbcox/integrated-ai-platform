# RM-DEV-002

- **ID:** `RM-DEV-002`
- **Title:** Local development environment setup script
- **Category:** `DEV`
- **Type:** `Enhancement`
- **Status:** `Planning`
- **Maturity:** `M0`
- **Priority:** `High`
- **Priority class:** `P1`
- **Queue rank:** `1`
- **Target horizon:** `immediate`
- **LOE:** `S`
- **Strategic value:** `5`
- **Architecture fit:** `5`
- **Execution risk:** `1`
- **Dependency burden:** `0`
- **Readiness:** `now`

## Description

Create an automated setup script that configures the complete local development environment with all dependencies, database initialization, and configuration defaults in a single command.

## Why it matters

Reduces developer onboarding time from hours to minutes. Eliminates setup errors and environment inconsistencies. Increases productivity for new team members.

## Key requirements

- Single-command environment setup
- Python dependency installation
- Database initialization with seed data
- Configuration file generation
- IDE integration helpers
- Validation checks post-setup
- Support for macOS and Linux

## Affected systems

- local development environment
- dependency management
- configuration system
- database schema

## Expected file families

- scripts/setup.sh
- scripts/setup-config.template
- docs/DEVELOPMENT_SETUP.md

## Dependencies

- none

## Risks and issues

### Key risks
- platform-specific issues (macOS vs Linux vs Windows)
- dependency version conflicts

### Known issues / blockers
- none; ready to start

## Recommended first milestone

Working setup script for primary platform (macOS) with database initialization and validation.

## Status transition notes

- Expected next status: `In progress`
- Transition condition: script created and tested
- Validation / closeout condition: new developer completes setup in < 5 minutes
