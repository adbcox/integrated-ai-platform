# Reuse-First OSS Wave Runbook

## Primary Session Declaration
- `primary_session_type`: `capability_session`
- `primary_objective`: Implement first-wave OSS reuse package with governed wrappers, smoke paths, and rollback posture.
- `blocker_or_capability_gap`: Selected OSS systems were only references; no repo-visible governed integration surfaces existed.
- `why_this_is_highest_leverage`: This unlocks immediate local-first acceleration paths without greenfield subsystem rewrites.
- `real_path_to_rerun_before_stopping`: `bin/oss_wave_smoke.sh`, then `make check`, `make quick`.

## OpenHands
- Wrapper: `bin/oss_wave_openhands.sh`
- Config template: `config/oss_wave/openhands.env.example`
- Locked runtime config: `config/oss_wave/openhands.env`
- Approved launch modes in this wave:
  - `launch-gui` (docker local GUI)
  - `launch-headless` (docker headless help-path)
- Workspace mount policy:
  - Wrapper enforces workspace root under repo root only.
- Validation:
  - `bin/oss_wave_openhands.sh validate-config`
  - `python3 bin/oss_wave_openhands_validate.py`
- Rollback:
  - `bin/oss_wave_openhands.sh rollback`
- Detailed operational runbook:
  - `docs/runbooks/OPENHANDS_REUSE_FIRST_RUNBOOK.md`

## MarkItDown
- Wrapper: `bin/markitdown_wrapper.py`
- Orchestrator: `bin/oss_wave_markitdown.sh`
- Supported inputs for this platform wave:
  - `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.txt`, `.html`, `.csv`, `.md`
- Validation:
  - `bin/oss_wave_markitdown.sh install`
  - `bin/oss_wave_markitdown.sh smoke`
- Rollback:
  - `bin/oss_wave_markitdown.sh uninstall`

## MCP Reference Servers
- Wrapper: `bin/oss_wave_mcp.sh`
- Approved first shortlist:
  - `filesystem`
  - `everything`
  - `sequential-thinking`
- Security boundary:
  - Allowlist-only launcher.
  - Filesystem server root forced under repo root.
  - Explicitly treated as reference/test servers, not hidden production backbone.
- Validation:
  - `bin/oss_wave_mcp.sh list`
  - `bin/oss_wave_mcp.sh smoke`
  - `bin/oss_wave_mcp.sh launch filesystem --dry-run`
- Rollback:
  - `bin/oss_wave_mcp.sh rollback`

## PR-Agent
- Wrapper: `bin/oss_wave_pr_agent.sh`
- Config template: `config/oss_wave/pr_agent.env.example`
- Workflow template (disabled by default): `.github/workflows/pr-agent.yml.disabled`
- Local config template: `.pr_agent.toml.example`
- Entry points:
  - `bin/oss_wave_pr_agent.sh validate-env`
  - `bin/oss_wave_pr_agent.sh review --pr-url <url>`
- Validation:
  - `bin/oss_wave_pr_agent.sh install`
  - `bin/oss_wave_pr_agent.sh smoke`
- Rollback:
  - `bin/oss_wave_pr_agent.sh rollback`

## n8n
- This wave is evaluation-only.
- Boundaries and adopt/defer criteria: `docs/roadmap/N8N_EVALUATION_BOUNDARY.md`.
- No broad workflow rollout in this pass.

## Unified status surface
- `python3 bin/oss_wave_status.py`

## Unified smoke path
- `bin/oss_wave_smoke.sh`
