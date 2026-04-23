# Master System Architecture

## Authority model
- Canonical authority remains repository governance, promotion gates, and local control window surfaces.
- OSS tools are integrated as subordinate adapters with explicit boundaries.

## Reuse-first adapter boundaries
- OpenHands: bounded execution surface for interactive coding sessions, launched only through wrapper-approved modes.
- MarkItDown: document-to-markdown ingestion utility behind a thin local wrapper.
- MCP reference servers: governed allowlist for local tool experiments, not production backbone.
- PR-Agent: PR analysis assistant in local/self-hosted posture with explicit entrypoints.
- n8n: evaluation-only; no operational backbone role in this wave.

## Control-window truth surface
- `bin/oss_wave_status.py` reports adapter availability and bounded posture as machine-readable JSON.

## Drift prevention
- No adapter writes promotion policy.
- No adapter changes roadmap truth directly.
- All adapter changes require paired doc truth updates in `docs/roadmap/ITEMS/*`.
