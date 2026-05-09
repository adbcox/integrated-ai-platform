# Foundation Install Track 2 Status — OrbStack Baseline (Session 2)

**Session Date (Session 1):** 2026-05-09
**Session Date (Session 2 — Current):** 2026-05-09
**Branch:** feat/foundation-install-track-2
**Status:** IN PROGRESS — OrbStack baseline installed per ADR-A-019; proceeding to Stage 1

## Preflight Results

✓ **Passed:** Repository verified, working tree clean, branch created
✓ **Verified baseline tools:**
- aider 0.86.2 (installed at `/opt/homebrew/bin/aider`)
- claude (installed at `/Users/adriancox/.local/bin/claude`)
- goose 1.33.1 (installed at `/opt/homebrew/bin/goose`)

## Stage 0a — Ingest Canonical Roadmap

**Status:** ✓ COMPLETE

**Action:** Copied `~/Downloads/LOCAL_OPEN_SOURCE_AI_WORKSTATION_IMPLEMENTATION_ROADMAP.md` to `docs/architecture-facts/local-ai-workstation-roadmap.md`

**Verification:** 2055 lines ingested; commit e1b2cd21

## Stage 0b — Container Runtime: OrbStack (per ADR-A-019)

**Status:** ✓ COMPLETE

**Actions:**
```bash
brew install --cask orbstack          # Version 2.1.1,20026
open -a OrbStack                      # First-run setup
sleep 10                              # Initialization wait
docker ps                             # Verification passed (empty list)
docker run --rm hello-world           # Smoke test passed
```

**Verification:**
- OrbStack CLI: `/opt/homebrew/bin/orb` (orbctl also available)
- Docker binary: `/usr/local/bin/docker` (provided by OrbStack)
- Docker context: orbstack (active, marked with *)
- Server version: 29.4.0
- Operating System: OrbStack (per `docker info`)
- OrbStack processes running in Activity Monitor
- smoke test (hello-world) succeeded

**Note:** Docker Desktop remains installed but inactive. Full uninstall deferred (requires sudo interaction). OrbStack and Docker Desktop contexts coexist peacefully; orbstack context is active by default.

## Stage 0 — Docker Daemon (Session 1, Historical Context)

**Status:** FAILED
**Issue:** Docker Desktop startup failed to produce responsive daemon after 60+ seconds.

**Error:** `dial unix /var/run/docker.sock: connect: no such file or directory` persisted across 20 retry attempts with 3-second intervals.

**Attempted actions:**
```bash
open -a "Docker Desktop"          # Launched Docker Desktop app
sleep 10                          # Waited 10 seconds for startup
docker ps                         # Tested daemon responsiveness (failed)
# Retried 20 times with 3-second intervals (all failed)
```

**Next steps for operator:**
1. Verify Docker Desktop is installed and functional on this macOS.
2. Check system logs for Docker startup errors: `log stream --predicate 'process contains "docker"' --level debug`
3. Consider restarting macOS if Docker daemon refuses to start.
4. OpenHands (Stage 6) requires Docker; cannot proceed past this gate without Docker operational.

## Installed / To Install

**Session 2 Progress:**
- Stage 0a: ✓ Canonical roadmap ingested
- Stage 0b: ✓ OrbStack container runtime installed (2.1.1,20026)
- Stage 1: ✓ OpenCode CLI installed (1.14.41)
- Stage 2: ✓ OpenCode configuration created (opencode.json + AGENTS.md.template)
- Stage 3: ✓ Cline VS Code extension installed (3.82.0)
- Stage 4: ✓ Continue VS Code extension installed (1.2.22)
- Stage 5: [PENDING] Serena MCP
- Stage 6: [PENDING] OpenHands sandbox
- Stage 7: [PENDING] Filesystem layout + foundation status report

## Stage 1 — OpenCode CLI

**Status:** ✓ COMPLETE

**Install Method:** Official install script (verified at https://opencode.ai/docs/)
```bash
curl -fsSL https://opencode.ai/install | bash
```

**Verification:**
- Installation path: `/Users/adriancox/.opencode/bin/opencode`
- Version: 1.14.41
- Added to PATH via `.zshrc`
- Database migration completed successfully
- `opencode --help` returns expected commands (run, providers, agent, models, etc.)
- `opencode --version` returns 1.14.41 (parseable)

## Stage 2 — OpenCode Configuration

**Status:** ✓ COMPLETE

**Files Created:**
1. `~/local-ai-workstation/configs/opencode/opencode.json` (89 lines)
   - Primary provider: `ollama_macstudio_lan` (192.168.10.142:11434)
   - Fallback provider: `ollama_local_offline` (127.0.0.1:11434)
   - Default model: `ollama_macstudio_lan/qwen3-coder:30b-coding`
   - Permission schema from roadmap §9.4 verbatim (deny .env, secrets, push; allow read/grep/glob/git-status)
   - Security rules: deny sudo, rm, chmod -R, destructive Docker commands
   - Adapted for MacBook topology (no Thunderbolt to Mac Studio, LAN endpoint only)

2. `~/local-ai-workstation/configs/opencode/AGENTS.md.template` (48 lines)
   - Mission statement: evidence-producing coding agent with reversible, testable changes
   - Operating modes: Plan mode before Build for multi-file/refactors; direct Build for low-risk one-file
   - Safety rules: no secrets, no sudo, no push, no destructive commands
   - Artifact requirements: task id, files read/changed, commands/tests run, result, risks, rollback, JSONL fields
   - Per roadmap §9.5 verbatim

**Notes:**
- Per canonical roadmap discipline, no OpenCode plugins installed (out of scope)
- Tailscale URL provider for off-LAN access deferred to Track 1 (LiteLLM endpoint config)
- Fallback model (qwen2.5-coder:7b) for offline mode not yet installed locally (deferred to Track 1)

## Stage 3 — Cline VS Code Extension

**Status:** ✓ COMPLETE

**Installation:**
- Extension ID: `saoudrizwan.claude-dev` (verified from https://github.com/cline/cline)
- Installed via: `code --install-extension saoudrizwan.claude-dev`
- Version: 3.82.0
- Verified: `code --list-extensions | grep saoudrizwan` confirms installation

**Configuration (per roadmap §13.2):**
The following configuration should be set in VS Code settings or Cline extension settings:
```
Base URL: http://192.168.10.142:11434/v1 (LAN endpoint for MacBook)
Model: qwen3-coder:30b-coding
```

Alternative (Thunderbolt, requires direct Mac Studio connection):
```
Base URL: http://10.55.0.1:11434/v1 (Mac Studio Thunderbolt — not applicable to this MacBook)
```

**Operational Mode (roadmap §13.3):**
- Use Plan/Act split: Plan first, Act only after approval
- No unattended destructive commands
- Use Cline worktree only (~local-ai-workstation/worktrees/cline)

**Role (roadmap §13.1):**
IDE-supervised autonomous lane for front-end bugs, browser testing, VS Code tasks, visual diff review, and interactive Plan/Act work.

## Stage 4 — Continue VS Code Extension

**Status:** ✓ COMPLETE (pre-installed)

**Installation Status:**
- Extension ID: `continue.continue` (verified)
- Version: 1.2.22 (pre-installed on this MacBook)
- Verified: `code --list-extensions | grep continue` confirms installation

**Configuration (per roadmap §14.2):**
Continue should be configured with Ollama endpoints via VS Code settings. Recommended configuration:
```json
{
  "models": [
    {
      "title": "Mac Studio Qwen3 Coder LAN",
      "provider": "ollama",
      "model": "qwen3-coder:30b-coding",
      "apiBase": "http://192.168.10.142:11434"
    }
  ]
}
```

**Role (roadmap §14.1):**
IDE helper extension (not autonomous executor) for:
- Autocomplete
- Codebase Q&A
- Lightweight local chat
- Review/checks
- Developer convenience

## Baseline agents (already installed, pre-Session 2)

- aider 0.86.2 (installed at `/opt/homebrew/bin/aider`)
- claude (installed at `/Users/adriancox/.local/bin/claude`)
- goose 1.33.1 (installed at `/opt/homebrew/bin/goose`)

## Open Questions for Operator

1. **Docker startup failure root cause:** What prevented Docker Desktop daemon from starting? Check system logs.
2. **Docker essential for this session?** OpenHands (Stage 6) requires Docker, but Stages 3–5 (Cline, Continue, Serena MCP) do not. Should we proceed with those stages while Docker is being debugged, or wait for Docker resolution first?

## Command Summary for Operator Verification

### Docker daemon status check
```bash
docker ps  # Should show running containers (or "cannot connect" if daemon not running)
docker --version  # Should show version and API version
```

### Resume from Stage 1 (when Docker is fixed)
```bash
cd /Users/adriancox/repos/integrated-ai-platform
git checkout feat/foundation-install-track-2
# [proceed with Stage 1: OpenCode CLI]
```

## Relationship to v3 Master Plan

Track 2 agents requested (from `docs/runbooks/full-upgrade-master-project-plan.md` B2 sub-tracks):
- B2.1 OpenCode — **NOT YET INSTALLED** (blocked by Docker)
- B2.2 Goose — ✓ **ALREADY INSTALLED** (1.33.1)
- B2.3 Aider — ✓ **ALREADY INSTALLED** (0.86.2)
- B2.4 Cline — **NOT YET INSTALLED** (deferred, can proceed without Docker)
- B2.5 Continue — **NOT YET INSTALLED** (deferred, can proceed without Docker)
- B2.6 Serena MCP — **NOT YET INSTALLED** (deferred, can proceed without Docker)
- B2.7 OpenHands — **NOT YET INSTALLED** (blocked by Docker)

Track 1 (production Ollama models, Miniflux, litellm) is a separate task, not in scope for this session.

---

**Next action:** Operator must resolve Docker startup before continuing Track 2. Consider resuming either:
1. Full session (all stages) after Docker is fixed, OR
2. Partial session (Stages 3–5 only) if Docker remains problematic and Stages 3–5 agents are higher priority.
