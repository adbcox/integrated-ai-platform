# OSS Reuse And Adoption Register

## First-wave decisions

### OpenHands
- Decision: adopt bounded local deployment wrapper now.
- Why: direct local coding acceleration surface without greenfield agent runtime rewrite.
- Integration: `bin/oss_wave_openhands.sh`, locked config `config/oss_wave/openhands.env` (+ template).
- Validation: implemented (validated headless execution, model-dependent stability) via `python3 bin/oss_wave_openhands_validate.py` with `AgentState.FINISHED` assertion.
- Rollback: wrapper rollback command and env-file removal.

### MarkItDown
- Decision: adopt now as ingestion converter.
- Why: direct reuse for document ingestion into markdown with minimal custom code.
- Integration: `bin/oss_wave_markitdown.sh`, `bin/markitdown_wrapper.py`.
- Validation: install + conversion smoke.
- Rollback: uninstall command removes local venv.

### MCP reference servers
- Decision: adopt shortlist now for governed local experimentation.
- Why: reuse official reference servers while preserving security boundaries.
- Integration: `bin/oss_wave_mcp.sh`, `config/oss_wave/mcp_servers.json`.
- Validation: npm package availability smoke.
- Rollback: remove client registration + stop wrapper-launched processes.

### PR-Agent
- Decision: adopt practical local/self-hosted posture now.
- Why: immediate PR workflow acceleration without replacing existing governance flow.
- Integration: `bin/oss_wave_pr_agent.sh`, `.github/workflows/pr-agent.yml.disabled`, `.pr_agent.toml.example`.
- Validation: local install and CLI version smoke.
- Rollback: env removal and workflow template remains disabled until explicit enable.

### n8n
- Decision: defer rollout, run bounded evaluation only.
- Why: overlap risk with existing control-plane orchestration.
- Integration: evaluation note only in this wave.
- Validation: explicit adopt/defer criteria documented.
