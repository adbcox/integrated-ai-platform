# Current Operating Context

## Session posture
- `primary_session_type`: `capability_session`
- This pass executes the first bounded OSS reuse implementation wave.
- This pass does not reopen architecture selection.

## Governance anchors
- Canonical progress contract remains in `docs/progress-contract.md`.
- Codex 5.1 replacement gate remains in `docs/codex51-replacement-gate.md`.
- Version 15 roadmap remains in `docs/version15-master-roadmap.md`.

## First-wave governance constraints
- Reuse-first over greenfield subsystem rewrites.
- OSS integrations remain subordinate to repository roadmap and validation gates.
- No hidden control-plane authority transfer to OpenHands, MCP servers, PR-Agent, or n8n.
- No fake implementation claims: wrappers and smoke paths are required for any implementation claim.

## Current implementation state (this wave)
- OpenHands: governed wrapper and config/launch/rollback runbook surfaces.
- MarkItDown: local install + thin wrapper + ingestion smoke path.
- MCP reference servers: allowlisted shortlist + security-bound launcher + smoke checks.
- PR-Agent: local venv install posture + disabled workflow template + CLI entrypoint.
- n8n: explicit evaluation lane only, no platform rollout.
