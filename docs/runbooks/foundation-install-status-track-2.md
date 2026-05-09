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
- Stage 5: ✓ Serena MCP installed (1.2.0, corrected per oraios docs)
- Stage 6: ✓ OpenHands sandbox installed (1.7, smoke test passed)
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

## Stage 5 — Serena MCP Server

**Status:** ✓ COMPLETE (corrected per oraios official documentation)

**Initial Attempt (FAILED — documented in commit 5a63dbf5):**
- Used incorrect package: `uv tool install serena` (name collision)
- Result: serena==0.9.1 (wrong package, library-only, no CLI)
- Issue: Roadmap §11.2 pointed to incorrect PyPI package name

**Corrected Installation (per https://oraios.github.io/serena/02-usage/010_installation.html):**
```bash
uv tool install -p 3.13 serena-agent@latest --prerelease=allow
```

**Installation Details:**
- Package: serena-agent (correct oraios MCP server)
- Version: 1.2.0
- Python runtime: 3.13.13 (provisioned by uv)
- Executables installed: serena, serena-hooks
- Installation path: `/Users/adriancox/.local/bin/serena`

**Verification Gate (PASSED):**
```bash
which serena                    # ✓ /Users/adriancox/.local/bin/serena
serena --version                # ✓ Serena 1.2.0
serena --help                   # ✓ Shows CLI subcommands (init, start-mcp-server, project, config, etc.)
serena init                      # ✓ Initialized successfully
```

**Initialization:**
- Config file: `/Users/adriancox/.serena/serena_config.yml`
- Language backend: LSP
- Auto-detected clients: claude-code, codex
- Status: "Serena has been initialised successfully"

**Configuration (per roadmap §11.3):**
Per-workspace Serena configuration can be set with:
```bash
serena start-mcp-server --project /path/to/current/worktree
```

**Role (per roadmap §11.1):**
Semantic code-intelligence layer for symbol search, definition/reference lookup, repo structure analysis, semantic navigation, safe refactor planning, and large-codebase context reduction.

**Note:**
This corrects commit 5a63dbf5 (Stage 5 failure). The roadmap §11.2 contained a reference to the wrong PyPI package (serena vs serena-agent). The correct package is serena-agent from the oraios project.

## Stage 6 — OpenHands Sandbox

**Status:** ✓ COMPLETE

**Installation Method:** Docker image pull via OrbStack
```bash
docker pull docker.openhands.dev/openhands/openhands:1.7
```

**Verification — Smoke Test:**
Official quick-start docker run command (per https://docs.openhands.dev/openhands/usage/run-openhands/local-setup):
```bash
docker run -it --rm --pull=always \
  -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server \
  -e AGENT_SERVER_IMAGE_TAG=1.19.1-python \
  -e LOG_ALL_EVENTS=true \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.openhands:/.openhands \
  -p 3000:3000 \
  --add-host host.docker.internal:host-gateway \
  --name openhands-app \
  docker.openhands.dev/openhands/openhands:1.7
```

**Smoke Test Results:**
- Image pull: ✓ Successful (2.02GB, image docker.openhands.dev/openhands/openhands:1.7)
- Container startup: ✓ Started successfully
- Database migrations: ✓ Completed (log: "Applying alembic migration versions")
- HTTP endpoint: ✓ Responsive on port 3000 (`curl -s http://localhost:3000` returned OpenHands UI HTML)
- UI load: ✓ Full page HTML with React application loaded
- Container lifecycle: ✓ Stopped cleanly with `docker stop openhands-app`
- Socket binding: ✓ /var/run/docker.sock correctly mapped from OrbStack

**Configuration (per roadmap §15.1):**
OpenHands runs as Docker-only sandbox autonomy. No CLI needed; access via web UI on http://localhost:3000 after starting container. Environment variables:
- AGENT_SERVER_IMAGE_REPOSITORY: ghcr.io/openhands/agent-server
- AGENT_SERVER_IMAGE_TAG: 1.19.1-python (matches 1.7 image)
- LOG_ALL_EVENTS: true
- Docker socket: /var/run/docker.sock (OrbStack-provided symlink from ~/.orbstack/run/docker.sock)
- Volume mounts: ~/.openhands for state persistence

**Role (per roadmap §15.1):**
Sandbox-only autonomy system. Requires running container with Docker socket access. Cannot operate standalone on host; no host shell, host editing, or host command execution. All work confined to container. Used for rapid iteration, testing, and teaching.

**Note:** Container image is tagged as "latest" in the Dockerfile but semantic version 1.7 corresponds to agent-server tag 1.19.1-python. Both are current stable as of 2026-05-09.

## Baseline agents (already installed, pre-Session 2)

- aider 0.86.2 (installed at `/opt/homebrew/bin/aider`)
- claude (installed at `/Users/adriancox/.local/bin/claude`)
- goose 1.33.1 (installed at `/opt/homebrew/bin/goose`)

## Session 2 Summary

**All Track 2 agents successfully installed and verified:**
- OrbStack container runtime (2.1.1,20026) replaces Docker Desktop per ADR-A-019
- OpenCode CLI (1.14.41) + configuration (opencode.json + AGENTS.md.template)
- Cline VS Code extension (3.82.0) for IDE-supervised autonomous tasks
- Continue VS Code extension (1.2.22) for IDE helper mode
- Serena MCP server (1.2.0) for semantic code intelligence
- OpenHands sandbox (1.7) for docker-only autonomy

**Docker Desktop issue resolved:** OrbStack provides fully functional docker daemon with standard socket at /var/run/docker.sock (symlink from ~/.orbstack/run/docker.sock). Docker Desktop remains installed but inactive.

**Remaining work (Stage 7):** Control plane filesystem layout and final foundation status report.

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
- B2.1 OpenCode CLI — ✓ **INSTALLED** (1.14.41)
- B2.2 Goose — ✓ **ALREADY INSTALLED** (1.33.1)
- B2.3 Aider — ✓ **ALREADY INSTALLED** (0.86.2)
- B2.4 Cline — ✓ **INSTALLED** (3.82.0)
- B2.5 Continue — ✓ **INSTALLED** (1.2.22)
- B2.6 Serena MCP — ✓ **INSTALLED** (1.2.0)
- B2.7 OpenHands — ✓ **INSTALLED** (1.7)

Track 1 (production Ollama models, Miniflux, litellm) is a separate task, not in scope for this session.

---

**Next action:** Operator must resolve Docker startup before continuing Track 2. Consider resuming either:
1. Full session (all stages) after Docker is fixed, OR
2. Partial session (Stages 3–5 only) if Docker remains problematic and Stages 3–5 agents are higher priority.
