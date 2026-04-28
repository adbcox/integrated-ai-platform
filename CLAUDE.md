# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)
**Deployment Target:** Mac Mini M5 at 192.168.10.145
**Current Phase:** Phase 3 Complete - All services operational

## Quick Start

You are working on a production autonomous AI platform. Before taking any action:

1. **Read the docs first:** All context is in `docs/PLATFORM_OVERVIEW.md`
2. **Deployment target:** Mac Mini .145 (192.168.10.145)
3. **All code execution:** Happens ON the Mac Mini, NOT locally
4. **User preference:** Give complete prompts, don't execute incrementally

## Core Documentation

- `docs/PLATFORM_OVERVIEW.md` - System overview, architecture, status
- `docs/DEPLOYMENT_GUIDE.md` - How to operate services
- `docs/TROUBLESHOOTING.md` - Issue resolution
- `docs/ARCHITECTURE.md` - Detailed technical architecture
- `docs/HANDOFF_GUIDE.md` - Session continuity instructions

## Critical Behavioral Rules

**When user asks for:**
- "Give me a prompt" → Provide complete prompt as text, DON'T execute
- "How do I deploy X" → Point to `docs/DEPLOYMENT_GUIDE.md`
- "Service not working" → Point to `docs/TROUBLESHOOTING.md`
- "What's the architecture" → Point to `docs/PLATFORM_OVERVIEW.md`

**Never:**
- Try to execute on local filesystem (everything is on Mac Mini .145)
- Reference files expecting them to be read - include content inline
- Waste tokens on unnecessary validations or tool calls

## Platform Rules — Non-Negotiable

These rules are platform doctrine. Every Claude Code session must respect them. They cannot be overridden by individual prompts.

### Terminology
This is the "AI workstation" or "platform". Pre-2026 alternative terminology (the 7-letter compound term starting with "h" that conflates personal-tinkering scope with this enterprise system) is deprecated and must not appear in any artifact — documentation, code, configs, secrets, container labels, or conversation. This is a doctrine rule, not a stylistic preference. Context for the deprecation lives in the §13.5 strike commit's diff (see `git log --grep="terminology audit"`).

### Secrets Management
- All secrets live in Vault.
- No `.env` files containing credentials. Pre-commit hook (`detect-secrets`) enforces this on tracked files.
- Services authenticate via per-service AppRole, never the root token.
- Credentials reach containers via Vault Agent sidecars writing to bind-mount volumes (`/Users/admin/.vault-agent-secrets/<svc>/`), never as Docker `environment:` variables.
- When adding a new service, follow `docs/runbooks/add-new-service.md`.
- Hash-only verification, no value display, ever (even during diagnostics).

### Vault Operations
- Auto-unseal via Transit (seal-vault container). Manual Shamir unsealing is for emergencies — see `docs/runbooks/vault-unseal.md`.
- Token rotation uses `-orphan` flag always (per Block 1.7 lesson).
- Audit log enabled; every operation in `/vault/logs/audit.log`.
- 30-day local retention; archived nightly to QNAP via cron.

### Heterogeneous Architecture
- Platform spans Mac Mini today; Linux (Threadripper) and Mac Studio soon. Every architectural decision is portability-flagged.
- Per-host configs in `config/vault-configs/` (`vault-config-macmini.hcl`, `vault-config-linux.hcl`).
- Avoid Mac-only patterns unless explicitly approved as platform-specific (KNOWN-LIMITATION).
- Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git doesn't track them automatically.

### Verification Doctrine
- Every claim verified by command output or cited source.
- "Probably works" is never sufficient.
- Pass-or-fail gates on every phase. Phases do not progress until gates pass.
- Regression probe (`docs/phase-13/h1-regression-probe.sh` — checks a-h) at every gate close.

### Container Hardening
- `cap_drop: [ALL]` with minimal `cap_add` per workload class.
- `security_opt: [no-new-privileges:true]` universally.
- `read_only: true` where image supports.
- `mem_limit` calibrated from baseline (don't undersize; postgres needs shared_buffers headroom).
- Privileged containers: only cAdvisor with documented rationale.
- Docker socket mounts: documented per-container (openhands, homarr) with rationale.

### Backup Policy
- Restic backups run nightly via `scripts/backup.sh` authenticated by `backup` AppRole.
- Vault data: `/vault/data` backed up via Restic.
- Test restore quarterly. Document in `docs/runbooks/backup-restore.md` (pending Phase 14).

### Anti-patterns (forbidden)
- `--no-deps` with sidecar pattern (sidecar IS a dependency)
- `sh -c` without `exec` at end (signal-handling failure; PID 1 stays as wrapper)
- Credential values in tool output, commit messages, or transcripts
- URL-embedded credentials using non-URL-safe characters (must be hex or other URL-safe encoding; base64's `/+=` break DSN parsing)
- Pre-compose launcher scripts (e.g., `bin/oss_wave_openhands.sh`) — deprecated; compose is canonical service lifecycle
- Display of credential values during diagnostics (use hash-based equality verification only; if diagnosis appears to require value inspection, stop and surface for user decision)

### Operating Doctrine
- Master project manager (separate Claude window) is responsible for system health and completion.
- Plan-first protocol: Claude Code outputs plan, master verifies, user approves.
- No assumptions: command output or cited source.
- Right way over easy way; document trade-offs.
- Stop on any unexpected behavior; surface to user.

## Project Structure

```
docs/PLATFORM_OVERVIEW.md   — start here
docs/DEPLOYMENT_GUIDE.md    — operations
docs/TROUBLESHOOTING.md     — issue resolution
docs/ARCHITECTURE.md        — technical depth
docs/HANDOFF_GUIDE.md       — session continuity
docs/roadmap/ITEMS/         — 601 roadmap items (canonical truth)
config/mac_mini/            — Mac Mini M5 node config
config/mac_studio/          — Mac Studio M3 node config (future)
config/qnap/                — QNAP NAS config
```

## Phase Document Storage Convention

All phase planning documents, inventories, audits, and deployment
artifacts MUST be written to:

  ~/repos/integrated-ai-platform/docs/phase-NN/

Where NN is the zero-padded phase number (01, 13, etc.). Subdirectories
allowed for sub-phases (phase-13/block-1/, phase-13/block-2/).

Filename pattern: PHASE_NN_<TYPE>_<YYYY-MM-DD>.md

Examples:
  docs/phase-13/PHASE_13_INVENTORY_2026-04-28.md
  docs/phase-13/PHASE_13_BLOCK_1_PLAN_2026-04-29.md
  docs/phase-13/PHASE_13_BLOCK_1_RESULTS_2026-04-29.md

NEVER write phase docs to ~/, /tmp/, or other ad-hoc locations.
