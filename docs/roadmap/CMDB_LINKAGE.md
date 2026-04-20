# Roadmap to CMDB Linkage

## Purpose

This document defines how roadmap items should connect to the system inventory / CMDB layer.

The goal is to make roadmap planning system-aware, so each item can be evaluated in terms of:

- what systems it affects
- what assets it depends on
- what hardware or software it requires
- what capabilities already exist
- what gaps remain

## Why this matters

CMDB linkage improves:

- impact clarity
- naming consistency
- system identity accuracy
- dependency awareness
- package planning
- capability-gap analysis

## Required linkage fields per roadmap item

Where applicable, roadmap items should identify:

- `Affected systems`
- `Affected subsystems`
- `Affected services`
- `Affected hardware/assets`
- `Required capabilities`
- `Missing capabilities`
- `Expected file families`
- `Read-only dependencies`

## Typical linkage examples

### UI / dashboard items

Link to:

- dashboard shell
- tablet display surfaces
- household display devices
- authentication and user profile layers
- Home Assistant or media integrations where relevant

### Inventory items

Link to:

- servers
- network devices
- printers
- scanners
- 3D printers
- Bambu filament library
- computer components
- tools and workshop assets

### Media items

Link to:

- Plex
- Sonarr
- Radarr
- NVIDIA Shield
- Samsung TV endpoints
- Apple TV endpoints
- media storage and network dependencies

### Home automation items

Link to:

- Home Assistant
- sensor inventory
- purifier devices
- indoor and outdoor reporting surfaces

### Developer / autonomy items

Link to:

- repo/runtime environment
- model execution layer
- validation systems
- orchestration layer
- firmware and hardware development surfaces

## Canonical rule

If a roadmap item touches real systems, devices, tools, assets, or services, the roadmap item should declare them explicitly.

This is required to reduce unintended impact and to support grouped execution planning.
