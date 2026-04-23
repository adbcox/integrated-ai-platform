# External Applications And Integrations

## First-wave scope
- OpenHands: local wrapper-governed deployment surface.
- MarkItDown: ingestion conversion utility wrapper.
- MCP reference servers: allowlisted test/reference integrations.
- PR-Agent: practical local/self-hosted PR review helper.
- n8n: bounded evaluation only.

## Explicit non-goals for this pass
- No broad external orchestration backbone swap.
- No hidden migration of planning/control authority.
- No silent auto-enable of cloud-hosted or webhook-triggered automation.

## Operational entrypoints
- `bin/oss_wave_openhands.sh`
- `bin/oss_wave_markitdown.sh`
- `bin/oss_wave_mcp.sh`
- `bin/oss_wave_pr_agent.sh`
- `bin/oss_wave_status.py`
