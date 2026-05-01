# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)
**Deployment Target:** Mac Mini M4 Pro 48 GB at 192.168.10.145 (control plane; verified via `system_profiler` 2026-05-01 — earlier "M5" wording was incorrect); MacBook Pro M5 parity in Block 3; Mac Studio M3 Ultra 96 GB at 192.168.10.146 (compute node, arrived 2026-05-01).
**Current Phase:** Phase 14 CLOSED (2026-04-30). Phase 15 CLOSED (2026-05-01) — see `docs/phase-15/PHASE_15_CLOSEOUT_2026-05-01.md` and tag `phase-15-final`. Phase 13 Increments 2B–7 still gated on Mouser+DigiKey+CSV. Vault KV mount data loss incident (Sev-2, 2026-04-30) — postmortem: `docs/phase-15/PHASE_15_KV_LOSS_2026-04-30.md`. KV rebuild completed: 47/47 enumerated leaf paths populated as of 2026-05-01 (verified by root-token enumeration); naming scheme differs from postmortem (e.g. `inventree/postgres` not `inventree/db`). Phase 16 open items: Block 4.D closeout, Block 4.E cross-index service (autonomous-coding structural enabler), Mac Studio Day-1 execution, Vault data volume in backup chain, loose-doc retirement, drift-detection automation, recovery-handoff doctrine update. (Six previously-listed phantom paths closed 2026-05-01 per validation §4.)

## Quick Start

You are working on a production autonomous AI platform. Before taking any action:

1. **Read the docs first:** All context is in `docs/ARCHITECTURE.md` (supersedes `docs/PLATFORM_OVERVIEW.md`)
2. **Deployment target:** Mac Mini .145 (192.168.10.145)
3. **All code execution:** Happens ON the Mac Mini, NOT locally
4. **User preference:** Give complete prompts, don't execute incrementally

## Core Documentation

- `docs/ARCHITECTURE.md` - System overview, architecture, service inventory (supersedes PLATFORM_OVERVIEW.md)
- `docs/PROJECT_FRAMEWORK.md` - PMP+ITIL labels, lifecycle, surface format, current Phase state
- `docs/runbooks/` - Operational runbooks (add-new-service, restart-services, vault-unseal, vault-recovery-from-shamir, rotate-credentials, incident-response, etc.)
- `docs/troubleshooting/` - Issue resolution (DECISION_TREE.md, common-issues.md, MANDATORY_CHECKLIST.md, plus case-studies/)
- `docs/PHASE_ROADMAP.md` + most-recent `docs/phase-NN/PHASE_NN_*_CLOSEOUT_*.md` - Session continuity (current phase status + latest closeout)

## Critical Behavioral Rules

**When user asks for:**
- "Give me a prompt" → Provide complete prompt as text, DON'T execute
- "How do I deploy X" → Point to `docs/runbooks/add-new-service.md` and `docs/runbooks/restart-services.md`
- "Service not working" → Point to `docs/troubleshooting/DECISION_TREE.md` and `docs/troubleshooting/common-issues.md`
- "What's the architecture" → Point to `docs/ARCHITECTURE.md`
- "How do we label X / where is Phase NN" → Point to `docs/PROJECT_FRAMEWORK.md`

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
- Mac Mini M4 Pro is the **control plane** today (Phase 13 Block 2 delivered: operator visualization, Vault, Caddy, observability stack, NetBox-driven topology API with YAML fallback during the C5 transition window).
- **Service inventory authoritative source:** NetBox CMDB at `netbox.internal`. `CMDB_SOURCE` env var (`yaml|netbox`, **default: netbox** as of Phase 14 D-DOC) controls source per consumer. `config/service-registry.yaml` retained as A-012 deprecation-gate fallback only.
- MacBook Pro M5 parity (Ollama + LiteLLM + Open WebUI + Headscale client + smart routing) is **Block 3**, executed when the user is ready.
- Linux (Threadripper) and Mac Studio M3 are **future blocks** beyond Block 3. Every architectural decision is portability-flagged.
- Per-host configs in `config/vault-configs/` (`vault-config-macmini.hcl`, `vault-config-linux.hcl`).
- Avoid Mac-only patterns unless explicitly approved as platform-specific (KNOWN-LIMITATION).
- Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git doesn't track them automatically.

### Post-Block-2 Follow-up List
1. ~~Caddy route hygiene — prune 12 dead `*.internal` routes~~ — **DONE 2026-04-29 in commit 3db56c7** (pruned 13 routes: 12 from this list + dashboard.internal).
2. **Homepage widget completion** — confirm Grafana SA token (provisioned in P2.1) and Uptime Kuma slug config render the expected widgets on `homepage.internal`. Closes if no remaining gaps.
3. **Block 3** — MacBook Pro M5 parity: Ollama + LiteLLM + Open WebUI + Headscale client + smart routing.
4. ~~Phase 14 — Loki for log-based per-site Caddy analysis~~ — **DONE Phase 14 D-LOG** (Loki + Promtail deployed, see "Caddy per-site access logs (resolved Phase 14 D-LOG)" under Known Hardening Trade-offs).

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
- **Three permanently non-compose-hardened containers (D#30):** `mcp-docker-remote` (bare docker run — Phase H migration target), `sms1obot-mcp-server` (Obot-managed lifecycle), `sms1obot-mcp-server-shim` (Obot-managed lifecycle). These cannot be hardened without Obot configuration API support.

### Backup Policy
- Restic backups run nightly via `scripts/backup.sh` authenticated by `backup` AppRole.
- Vault data: `/vault/data` backed up via Restic.
- Test restore quarterly. Restore procedure: `docs/runbooks/vault-restore-from-backup.md` (authored Phase 14 D-DOC).

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

- **Caddy per-site access logs (resolved Phase 14 D-LOG)**: Each site imports a shared `(access_log)` snippet → JSON entries with site `host` field land in `/var/log/caddy/access.log` (rolled at 100 MiB, 7 keeps). Loki + Promtail deployed; Promtail tails the log from the `caddy-logs` Docker volume and extracts `req_host`, `resp_status`, `req_method` labels. Per-site analysis now available via `{job="caddy", req_host="..."}` LogQL. Grafana `caddy-per-site-p14` dashboard at grafana.internal. Promtail uses `cap_add: [DAC_READ_SEARCH]` (D#31 documented exception — minimal, read-only log shipping).

- **Zabbix Prometheus metrics (resolved Phase 14 D-ZBX)**: Custom `zabbix-exporter` container deployed at port 9224; scrapes Zabbix API (Bearer token via Vault Agent sidecar) and exposes `zabbix_triggers_active{severity=...}` + `zabbix_hosts_available{status=...}`. vmagent scrapes it; Grafana dashboard `zabbix-overview-p14` provisioned.

- **Cloud LLM routes deprecated platform-side (Phase 13.5)**: litellm-gateway no longer carries `claude-sonnet`, `claude-haiku`, or `gpt-4o` routes. `secret/anthropic/api` and `secret/openai/api` are deleted from Vault; `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` are no longer rendered into the litellm sidecar template. Platform services depend exclusively on local Ollama models. Anthropic Pro subscription access (when occasionally needed for high-judgment work) flows through the `claude-pro` shell function — Claude Code talking directly to Anthropic — and never traverses platform infrastructure. This decouples the platform from any cloud-LLM availability/quota constraint and matches the user's subscription posture (Pro + ChatGPT Plus, no API credits). See "LLM Access Doctrine" above.

- **cAdvisor friendly-name labels missing on Docker Desktop Mac**: cAdvisor (`zcube/cadvisor:latest`) on Mac Docker Desktop emits `container_*` metrics keyed by cgroup path (`id="/docker/<sha>"`) only; `name`/`image`/`container_label_*` labels do not populate because the cgroup-to-docker-API resolution is gated by Docker Desktop's VM boundary. Setting `--docker_only=true` does not help (it filters to zero series). Container Health dashboard panels therefore use `id=~"/docker/.+"` selectors with `label_replace` to truncate the hash to 12 chars in legends. Friendly labels will return when the platform migrates to Linux/Threadripper. Operators map a hash via `docker ps --format '{{.ID}} {{.Names}}'`.

### Operating Doctrine
- Master project manager (separate Claude window) is responsible for system health and completion.
- Plan-first protocol: Claude Code outputs plan, master verifies, user approves.
- No assumptions: command output or cited source.
- Right way over easy way; document trade-offs.
- Stop on any unexpected behavior; surface to user.
- **D#25 operating-model rule:** §6 AppRole provisioning must verify consumer presence before provisioning AppRole/policy. Mechanical provisioning without verifying that a service actually reads credentials creates orphan AppRoles (learned from plane-web Increment 1.5.A audit — plane-web had a policy provisioned but no credential consumption code). Always check the service's entrypoint/env consumption before provisioning.
- **§6 final state (Increment 1.5.A):** All 16 credential-consuming services have Vault Agent sidecars. 15 were covered by prior block work; plane-web decommissioned as N/A (frontend, no credential consumption). Orphan policy `config/vault-policies/plane-web-policy.hcl` deleted.
- **§7 final state (Increment 1.5.B):** All compose-manageable containers have `cap_drop:[ALL]`. 3 non-compose containers remain (D#30, see Container Hardening above).

## Project Structure

```
docs/ARCHITECTURE.md        — start here (supersedes PLATFORM_OVERVIEW.md)
docs/PROJECT_FRAMEWORK.md   — PMP+ITIL labels, lifecycle, surface format
docs/runbooks/              — operational runbooks (add-new-service, restart-services, vault-unseal, etc.)
docs/troubleshooting/       — issue resolution (DECISION_TREE.md, common-issues.md, MANDATORY_CHECKLIST.md)
docs/PHASE_ROADMAP.md       — current phase + roadmap; per-phase docs in docs/phase-NN/
docs/roadmap/ITEMS/         — 601 roadmap items (canonical truth)
config/mac_mini/            — Mac Mini M4 Pro node config
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
