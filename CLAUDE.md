# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)

**Hardware:**
- Mac Mini M4 Pro 48 GB at 192.168.10.145 — control plane (`system_profiler`-verified 2026-05-01; earlier "M5" framing was wrong)
- Mac Studio M3 Ultra 96 GB at 192.168.10.142 — compute node (arrived 2026-05-01)
- MacBook Pro M5 — local-parity node (Phase 13 Block 3 vocabulary; tracked in current phase plan)
- QNAP NAS — backup target

## Phase / deliverable state — DO NOT duplicate here

**Canonical sources (read these, do not infer from this file):**
- `docs/PROJECT_FRAMEWORK.md` §9 — current phase deliverable table (status of every D-NN-MM)
- `docs/PHASE_ROADMAP.md` — open phase + roadmap pointers
- `docs/phase-NN/PHASE_NN_PLAN_<date>.md` — current phase charter (find via `ls -t docs/phase-*/PHASE_*_PLAN_*.md | head -1`)
- `docs/phase-NN/PHASE_NN_*_CLOSEOUT_<date>.md` — closeout for the most recently closed phase
- `git log --oneline -20 docs/PROJECT_FRAMEWORK.md` — recent deliverable flips

**Auto-prioritization rule:** never auto-prioritize a deliverable from staleness in *this* file. Always reconcile against PROJECT_FRAMEWORK.md §9 first. Phase rollovers (Phase 16 → 17, etc.) re-parent open items into new D-NN-MM IDs in §9, and the old phase's "open items" become invalid pointers. If a deliverable looks important but is not in §9 of the latest framework, treat it as closed-or-superseded until proven otherwise.

**Postmortem / incident pointers (historical, do not confuse with active state):**
- Vault KV mount data loss (Sev-2, 2026-04-30): `docs/phase-15/PHASE_15_KV_LOSS_2026-04-30.md` — KV rebuild closed 2026-05-01
- Other phase-specific incidents live under `docs/phase-NN/`

## Quick Start

You are working on a production autonomous AI platform. Before taking any action:

1. **Read the docs first:** All context is in `docs/ARCHITECTURE.md` (supersedes `docs/PLATFORM_OVERVIEW.md`)
2. **Deployment target:** Mac Mini .145 (192.168.10.145)
3. **All code execution:** Happens ON the Mac Mini, NOT locally
4. **User preference:** Give complete prompts, don't execute incrementally

## Core Documentation (canonical sources)

- `docs/ARCHITECTURE.md` — system overview, architecture, service inventory (supersedes PLATFORM_OVERVIEW.md)
- `docs/PROJECT_FRAMEWORK.md` — PMP+ITIL labels, lifecycle, surface format, AND **canonical phase/deliverable state** (§9 for current phase)
- `docs/runbooks/` — operational runbooks (add-new-service, restart-services, vault-unseal, vault-recovery-from-shamir, rotate-credentials, incident-response, etc.)
- `docs/troubleshooting/` — issue resolution (DECISION_TREE.md, common-issues.md, MANDATORY_CHECKLIST.md, plus case-studies/)
- `docs/PHASE_ROADMAP.md` + most-recent `docs/phase-NN/PHASE_NN_*_CLOSEOUT_*.md` — session continuity (current phase status + latest closeout)
- `~/.platform-registry/inventory.json` — runtime service registry (D#25 substrate; canonical for ports, internal IPs, depends_on, Caddy routes, credential file metadata)
- `docs/architecture-facts/` — durable findings + per-subsystem chronicles (e.g. exo-cluster.md)

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
- **Runtime service substrate:** `~/.platform-registry/inventory.json` (D#25). Source of truth for ports / internal IPs / depends_on / Caddy routes / credential file metadata. Always consult before guessing.
- Mac Studio M3 Ultra (.142) is a **compute node** as of 2026-05-01 (Day-1 in D-17-15). Distributed inference is upstream-blocked (D-17-25 Findings U+V); single-node placement on Mac Mini works and is the demo path.
- MacBook Pro M5 parity (Ollama + LiteLLM + Open WebUI + Headscale client + smart routing) is the original "Block 3" framing — current scope tracking lives in `docs/PROJECT_FRAMEWORK.md` §9.
- Linux (Threadripper) is a **future host**. Every architectural decision is portability-flagged.
- Per-host configs in `config/vault-configs/` (`vault-config-macmini.hcl`, `vault-config-linux.hcl`).
- Avoid Mac-only patterns unless explicitly approved as platform-specific (KNOWN-LIMITATION).
- Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git doesn't track them automatically.

### Active follow-up lists

Phase-specific follow-up lists live in their phase plan / closeout
docs, NOT here. To find what is open: `docs/PROJECT_FRAMEWORK.md` §9
(current phase deliverable table) plus the latest
`docs/phase-NN/PHASE_NN_*_PLAN_*.md`. Cross-phase parking-lot items
that survive a phase rollover are re-parented into the new phase's
deliverable table with a fresh D-NN-MM ID.

### Verification Doctrine
- Every claim verified by command output or cited source.
- "Probably works" is never sufficient.
- Pass-or-fail gates on every phase. Phases do not progress until gates pass.
- Regression probe (`docs/phase-13/h1-regression-probe.sh` — checks a-h) at every gate close.

### Service Registry Consultation Doctrine (D-17-29)
- **Before any operation involving container ports, internal addresses, dependencies, or external routing**, AI sessions MUST consult `~/.platform-registry/inventory.json` (or `~/.platform-registry/by-service/<service>.json` for a single record).
- Convenience reader: `python3 -c "import sys; sys.path.insert(0,'/Users/admin/repos/integrated-ai-platform/scripts/platform-registry/lib'); import registry_writer as rw; import json; print(json.dumps(rw.query('seal-vault'), indent=2))"`
- The registry is the canonical source for: container_name ↔ service_id, host_port ↔ container_port mapping, internal IPs per network, depends_on/depended_on_by graph, attached Caddy routes, credential file metadata (paths + fingerprints, never values).
- If the registry is stale (`last-refresh.json` older than 30 minutes), run `scripts/platform-registry/refresh.sh` before proceeding.
- **Failure to consult before guessing is a doctrine violation.** Tonight's seal-vault recovery (D-17-28) cost ~3 hours because AI guessed port 8200 instead of looking up 8201. The registry exists to eliminate that failure mode permanently.
- Spec: `docs/architecture-patterns/service-registry-mvp.md`. Builder code: `scripts/platform-registry/lib/`.
- **Sub-doctrine (D-17-26 close, Finding DD) — container env inspection:** when inspecting container environment for credential or runtime-set variables, query `/proc/1/environ` rather than spawning a fresh shell via `docker exec env`. Image-baked `Config.Env` ≠ runtime PID 1 environ when entrypoint scripts source secret files. Correct check: `docker exec <container> sh -c 'tr "\0" "\n" < /proc/1/environ | grep ^VAR='`. Apply BEFORE reporting a credential as missing/empty.

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
docs/PROJECT_FRAMEWORK.md   — PMP+ITIL labels, lifecycle, surface format, §9 deliverable table
docs/runbooks/              — operational runbooks (add-new-service, restart-services, vault-unseal, etc.)
docs/troubleshooting/       — issue resolution (DECISION_TREE.md, common-issues.md, MANDATORY_CHECKLIST.md)
docs/PHASE_ROADMAP.md       — current phase + roadmap; per-phase docs in docs/phase-NN/
docs/architecture-facts/    — durable per-subsystem chronicles (findings, dependencies)
docs/architecture-patterns/ — reusable patterns (e.g. service-registry-mvp.md)
config/mac_mini/            — Mac Mini M4 Pro node config
config/mac_studio/          — Mac Studio M3 node config
config/qnap/                — QNAP NAS config
```

OpenProject (D-17-04) is the **PM substrate / operational mirror** for
two complementary scopes, synced one-way by
`scripts/openproject-sync-from-framework.py`:

1. **Framework deliverables** (`D-NN-MM`) — sourced from
   `docs/PROJECT_FRAMEWORK.md` §9. Status is sync-managed; manual
   status edits in the OpenProject UI are overwritten on next run.
2. **Roadmap scope items** (`RM-<phase>-<sub>-<NNN>`, e.g. `RM-16-A-001`,
   `RM-18-D-001`) — sourced from `docs/PHASE_ROADMAP.md` §16/§18 sub-block
   `**Scope:**` bullets via `scripts/lib/roadmap_parser.py` (D-17-31).
   Status is **operator-owned** (sync only creates / refreshes title
   and description; never overwrites status drift). Items get the
   `autonomous-coding` category when their scope text matches the
   buildable-work heuristic (scripts/, services, routes, endpoints,
   dashboards, plugins, harnesses, agents, MCP, prompt libraries,
   provenance, capabilities, inference) and don't match the
   judgment-work veto (audit, review, evaluation, decision, ADR-…).

For both scopes the markdown is canonical; the UI is for comments and
operational links. Plane CE was retired 2026-05-01.

**"What's next?" doctrine (D-17-31):** never answer this from
PROJECT_FRAMEWORK.md §9 alone. The framework table covers the *current
phase's* deliverables only — it intentionally excludes long-horizon
roadmap items (Phase 18 health/fitness, Linux migration, platform
hardening) and Phase-16 carry-overs not promoted into the active phase.
Always also consult OpenProject's queue (filter by status=Backlog/In
Progress, optionally category=autonomous-coding) before recommending
work. Convenience: `python3 scripts/openproject-sync-from-framework.py
--query-backlog [--autonomous-coding-only]`.

**Sync flags (D-17-31):**
- `--include-roadmap` — include `RM-*` items in normal framework run
- `--roadmap-only` — sync just the roadmap section (skip §9)
- `--dedup-phase17` — one-shot: close `17.A`–`17.T` shorthand WPs as
  superseded by their `D-17-NN` canonical equivalents (already run
  2026-05-03; idempotent if re-run)

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
