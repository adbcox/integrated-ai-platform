# External System to Roadmap Crosswalk

## Purpose

This document maps major external systems to the roadmap families or items that depend on them most directly.

## Crosswalk

### Core platform and governance

- **Plane** -> `RM-GOV-006`, `RM-GOV-007`, `RM-GOV-008`
- **GLPI / CMDB path** -> `RM-GOV-001`, future CMDB-oriented governance and inventory work
- **Qdrant** -> future retrieval/memory implementation work tied to local autonomy and developer-assistant maturity

### AI and coding surfaces

- **Ollama** -> local autonomy and developer-assistant architecture priorities
- **Claude Code** -> controlled adapter / supervisory posture linked to architecture and governance policy
- **Aider-derived capabilities** -> controlled adapter posture linked to shared runtime and local coding support

### Media systems

- **Plex** -> `RM-MEDIA-001`, `RM-MEDIA-002`, related media endpoint and orchestration work
- **Sonarr** -> `RM-MEDIA-002`
- **Radarr** -> `RM-MEDIA-002`
- **Prowlarr** -> media-automation support and likely future media integration items

### Home and environment systems

- **Home Assistant** -> `RM-HOME-001` and related home/environment items
- **TP-Link Deco / network telemetry** -> `RM-OPS-002` and related home/network monitoring work

### Athlete / health systems

- **Strava** -> future athlete analytics branch work
- **Sportster (unresolved)** -> unresolved athlete analytics planning until confirmed

## Rule

If an external system is important enough to drive roadmap execution, it should appear both here and in `EXTERNAL_APPLICATIONS_AND_INTEGRATIONS.md`.
