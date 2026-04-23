# Reuse First Implementation Wave

## Objective
Materially accelerate the local AI coding system by implementing the first reuse-first OSS wave with bounded wrappers, validation, and rollback posture.

## Implemented packet

### 1) OpenHands
- Canonical deployment/runbook: `docs/runbooks/REUSE_FIRST_OSS_WAVE_RUNBOOK.md`
- Operational runbook: `docs/runbooks/OPENHANDS_REUSE_FIRST_RUNBOOK.md`
- Approved launch modes: `launch-gui`, `launch-headless` via `bin/oss_wave_openhands.sh`
- Wrapper/integration boundary: wrapper-only launch with repo-bounded workspace mounts.
- Config capture/validation: locked `config/oss_wave/openhands.env` (with example template) + `validate-config`.
- Validation status: implemented (validated headless execution, model-dependent stability).
- Canonical validation command: `python3 bin/oss_wave_openhands_validate.py` (requires `AgentState.FINISHED` in logs).
- RM-UI-005 binding: status surfaced via `python3 bin/oss_wave_status.py`.

### 2) MarkItDown
- Install path: `bin/oss_wave_markitdown.sh install`
- Thin-wrapper integration: `bin/markitdown_wrapper.py`
- Supported input/use path: document ingestion to markdown for local workflows.
- Validation samples/commands: `bin/oss_wave_markitdown.sh smoke`
- RM-GOV-009 binding: governed install/smoke/rollback posture documented.

### 3) MCP reference servers
- Approved shortlist: filesystem, everything, sequential-thinking.
- Wrapper/security boundary: `bin/oss_wave_mcp.sh` + allowlist config + repo-root filesystem clamp.
- Smoke path: `bin/oss_wave_mcp.sh smoke`
- Explicit constraint: reference/test servers, not hidden production backbone.
- RM-GOV-009 binding: documented in item and architecture register.

### 4) PR-Agent
- Deployment/integration posture: local venv CLI + disabled workflow template.
- Command/workflow entrypoints: `bin/oss_wave_pr_agent.sh` and `.github/workflows/pr-agent.yml.disabled`.
- Validation path: `install`, `validate-env`, `smoke`.
- RM-GOV-009 binding: governance item updated with boundary and rollback.

### 5) n8n
- Evaluation lane only in this wave.
- Fit/overlap/adopt-vs-defer criteria in `docs/roadmap/N8N_EVALUATION_BOUNDARY.md`.
- No broad rollout in this pass.
