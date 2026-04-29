# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)
**Deployment Target:** Mac Mini M5 at 192.168.10.145 (control plane); MacBook Pro M5 parity in Block 3
**Current Phase:** Phase 13 Block 2 — Mac Mini operator visualization complete (homepage canonical, 6 Grafana dashboards, topology API, Zabbix host, Caddy access logs + metrics)

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
- Mac Mini M5 is the **control plane** today (Phase 13 Block 2 delivered: operator visualization, Vault, Caddy, observability stack, registry-driven topology API).
- MacBook Pro M5 parity (Ollama + LiteLLM + Open WebUI + Headscale client + smart routing) is **Block 3**, executed when the user is ready.
- Linux (Threadripper) and Mac Studio M3 are **future blocks** beyond Block 3. Every architectural decision is portability-flagged.
- Per-host configs in `config/vault-configs/` (`vault-config-macmini.hcl`, `vault-config-linux.hcl`).
- Avoid Mac-only patterns unless explicitly approved as platform-specific (KNOWN-LIMITATION).
- Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git doesn't track them automatically.

### Post-Block-2 Follow-up List
1. **Caddy route hygiene** — prune 12 dead `*.internal` routes from `docker/caddy/Caddyfile` (no backing service): `manyfold`, `gitea`, `tautulli`, `overseerr`, `ragflow`, `portainer`, `netdata`, `dozzle`, `pgadmin`, `bookstack`, `n8n`, `filebrowser`. Each carries the shared `import access_log` snippet which is harmless but inflates the Caddyfile.
2. **Homepage widget completion** — confirm Grafana SA token (provisioned in P2.1) and Uptime Kuma slug config render the expected widgets on `homepage.internal`. Closes if no remaining gaps.
3. **Block 3** — MacBook Pro M5 parity: Ollama + LiteLLM + Open WebUI + Headscale client + smart routing.
4. **Phase 14** — Loki for log-based per-site Caddy analysis (unblocks per-host dashboards which Caddy 2.11.2 default Prometheus output cannot provide).

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

### LLM Access Doctrine

The platform's default LLM access is local Ollama via Claude Code:

```
claude-local       # → local Ollama (free, no quota; orchestrator: qwen2.5-coder:32b)
claude-pro         # → Anthropic via Pro subscription (uses quota)
claude (aliased)   # → defaults to claude-local
```

Use `claude-local` for routine work: implementation, refactoring, documentation, file exploration, code review.

Use `claude-pro` ONLY for high-judgment tasks where Anthropic-quality reasoning is genuinely required. Pro quota is finite; treat it as expensive.

**Platform services must NEVER depend on Anthropic API access.** `secret/anthropic/api` is permanently unused (will be deleted in Phase 13.5 §6). Any service that needs LLM capability uses local models via litellm or Ollama directly.

**Token discipline practices**:
- Use `/compact` when session context exceeds ~150k tokens
- Use `/clear` when switching to unrelated work
- Never load skills you don't need for the current task
- `claude-local` pins model via shell function; don't override unless intentional
- `claude-pro` does not pin model — Anthropic defaults apply (don't pass --model with a local-only model name to claude-pro)

**Subagent pattern** (`~/.claude/agents/`):
- `decomposer` (qwen2.5-coder:32b): breaks complex problems into specs
- `implementer` (qwen2.5-coder:14b): executes single specs end-to-end
- `reviewer` (qwen2.5-coder:7b): validates implementation against spec

The orchestrator (Claude Code at the top level) delegates implementation work to subagents to minimize its own quota usage when running under `claude-pro`. Under `claude-local`, the entire chain runs on the Mac Mini's Ollama.

### Known Hardening Trade-offs

- **ICMP/fping monitoring not available**: zabbix-server uses `cap_drop:[ALL]` which excludes `NET_RAW`. ICMP items will be in unsupported state. Use TCP-based health checks (telnet item type, agent.ping, http.test) instead. Adding `NET_RAW` `cap_add` was rejected as exceeding minimal-cap doctrine.

- **Mac Mini host monitoring (registered Block 2 P6)**: Host `mac-mini` registered in Zabbix (hostid 10783) on group "Linux servers" with template "Linux by Zabbix agent" via DNS interface `zabbix-agent:10050`. Memory and CPU items are populating. ICMP-derived items remain unsupported (see NET_RAW note above). Host-level disk/network items reach the *agent container's* view, not the macOS host — true host-OS introspection (e.g., macOS-specific filesystems, Bonjour, smc temps) is deferred and will require either privileged agent or macOS-native exporter sidecar.

- **Caddy per-site access logs (resolved Block 2 P6)**: Each site imports a shared `(access_log)` snippet → JSON entries with site `host` field land in `/var/log/caddy/access.log` (rolled at 100 MiB, 7 keeps). Per-site Prometheus metrics are *partial*: Caddy 2.11.2's default Prometheus output labels `caddy_http_request_*` series with `code`, `handler`, `method`, `server` only — there is **no `host` label**. Per-server (`server="srv0"`) is the finest aggregation available from metrics. Per-site analysis requires Loki-tailing the JSON access.log (deferred to Phase 14 logging-stack work).

- **Zabbix Prometheus metrics**: zabbix-server 7.4 does not natively expose `/metrics`. Adding `zabbix-prometheus-exporter` (or similar) is an additive deployment, deferred to Block 2 when its metrics are needed in Grafana.

- **Cloud LLM routes deprecated platform-side (Phase 13.5)**: litellm-gateway no longer carries `claude-sonnet`, `claude-haiku`, or `gpt-4o` routes. `secret/anthropic/api` and `secret/openai/api` are deleted from Vault; `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are no longer rendered into the litellm sidecar template. Platform services depend exclusively on local Ollama models. Anthropic Pro subscription access (when occasionally needed for high-judgment work) flows through the `claude-pro` shell function — Claude Code talking directly to Anthropic — and never traverses platform infrastructure. This decouples the platform from any cloud-LLM availability/quota constraint and matches the user's subscription posture (Pro + ChatGPT Plus, no API credits). See "LLM Access Doctrine" above.

- **cAdvisor friendly-name labels missing on Docker Desktop Mac**: cAdvisor (`zcube/cadvisor:latest`) on Mac Docker Desktop emits `container_*` metrics keyed by cgroup path (`id="/docker/<sha>"`) only; `name`/`image`/`container_label_*` labels do not populate because the cgroup-to-docker-API resolution is gated by Docker Desktop's VM boundary. Setting `--docker_only=true` does not help (it filters to zero series). Container Health dashboard panels therefore use `id=~"/docker/.+"` selectors with `label_replace` to truncate the hash to 12 chars in legends. Friendly labels will return when the platform migrates to Linux/Threadripper. Operators map a hash via `docker ps --format '{{.ID}} {{.Names}}'`.

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
