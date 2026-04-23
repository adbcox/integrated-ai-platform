# RM-GOV-009

## Item
Governed OSS adoption posture for first-wave integrations.

## Status
Implemented in bounded first wave.

## Scope covered
- MarkItDown integration posture and rollback path.
- MCP reference server allowlist + security boundary + smoke path.
- PR-Agent deployment posture + validation + rollback path.

## Evidence surfaces
- `docs/architecture/OSS_REUSE_AND_ADOPTION_REGISTER.md`
- `docs/roadmap/REUSE_FIRST_IMPLEMENTATION_WAVE.md`
- `bin/oss_wave_markitdown.sh`
- `bin/markitdown_wrapper.py`
- `bin/oss_wave_mcp.sh`
- `config/oss_wave/mcp_servers.json`
- `bin/oss_wave_pr_agent.sh`
- `.github/workflows/pr-agent.yml.disabled`
