# Claude Code - Project Instructions

**Project:** Integrated AI Platform (Enterprise Autonomous AI Infrastructure)

**Hardware:**
- Mac Mini M4 Pro 48 GB at 192.168.10.145 — control plane (`system_profiler`-verified 2026-05-01; earlier "M5" framing was wrong)
- Mac Studio M3 Ultra 96 GB at 192.168.10.142 — compute node (arrived 2026-05-01)
- MacBook Pro M5 — local-parity node (Phase 13 Block 3 vocabulary; tracked in current phase plan)
- Home Assistant hub at 192.168.10.141 — canonical HA host (physical/VM, not platform-managed). Caddy `homeassistant.internal` proxies here. Mac Mini did NOT and does NOT host an HA container; a stray container retired 2026-05-03 per D-17-34.
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

1. **Read the docs first:** All context is in `docs/ARCHITECTURE.md` (supersedes the archived `docs/_archive/PLATFORM_OVERVIEW.md`)
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
- **Service inventory authoritative source:** NetBox CMDB at `netbox.internal`. `CMDB_SOURCE` env var (`yaml|netbox`, **default: netbox** as of Phase 14 D-DOC) controls source per consumer. `config/service-registry.yaml.DEPRECATED` retained as A-012 deprecation-gate fallback only.
- **Runtime service substrate:** `~/.platform-registry/inventory.json` (D#25). Source of truth for ports / internal IPs / depends_on / Caddy routes / credential file metadata. Always consult before guessing.
- Mac Studio M3 Ultra (.142) is a **compute node** as of 2026-05-01 (Day-1 in D-17-15). Distributed inference is upstream-blocked (D-17-25 Findings U+V); single-node placement on Mac Mini works and is the demo path.
- MacBook Pro M5 parity (Ollama + LiteLLM + Open WebUI + Headscale client + smart routing) is the original "Block 3" framing — current scope tracking lives in `docs/PROJECT_FRAMEWORK.md` §9.
- Linux (Threadripper) is a **future host**. Every architectural decision is portability-flagged.
- Per-host configs in `config/vault-configs/` (`vault-config-macmini.hcl`, `vault-config-linux.hcl`).
- Avoid Mac-only patterns unless explicitly approved as platform-specific (KNOWN-LIMITATION).
- Out-of-repo compose changes (`~/control-center-stack/stacks/*`) require pre/post snapshots in the rewire log because git doesn't track them automatically.

### Network Topology
- LAN: 192.168.10.0/24. OPNsense at .1 on Minisforum MS-01 is the sole DNS authority (Dnsmasq; never Unbound, never Kea per D-17-21).
- Wiring: OPNsense → Ruckus ICX 7150-C12P-2X1G PoE+ switch via 10G DAC (not through the Deco AP — that path was the SPOF for AI workloads, corrected). Deco BE95 in AP mode only.
- Hosts: Mac Mini M4 Pro at .145 (orchestration, 48 GB), Mac Studio M3 Ultra at .142 (96 GB, delivered, currently NOT joined to Headscale — see KI-010 for the dependency this creates), Threadripper + RTX 4070 (GPU compute: ingestion at scale, AI image/video, 3D model gen), Ryzen 9900X (daily driver), QNAP at .201 (NAS), Home Assistant at .141 (sole canonical instance per D-17-34).
- Current primary work surface: MacBook Pro 32 GB.

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

### Artifact Substrate Doctrine (D-17-37)
- **Roadmap binary artifacts (PDFs, schematics, vendor docs, source dumps) live on QNAP, not Mac Mini and not git.** Canonical layout: `/Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts/<phase>/<deliverable>/{source,extracted,annotations}/` with `metadata.yaml` at deliverable root.
- **Stable pointer scheme:** `qnap://download/manual/roadmap-artifacts/<phase>/<deliverable>/source/<file>`. Roadmap docs reference artifacts by this URI, never by absolute local path. Resolver: `scripts/artifact-resolve.sh <qnap-uri>` prints the local path.
- **Sibling registry axis:** `~/.platform-registry/artifacts.json` (index) + `~/.platform-registry/artifacts/<deliverable>.json` (per-record). Built by `scripts/platform-registry/lib/artifact_writer.py`; refreshed by `scripts/platform-registry/refresh-artifacts.sh` (chained from the launchd-driven `refresh.sh`).
- **Ingestion is mandatory.** Use `scripts/artifact-ingest.sh <D-NN-NN> <local-path> [--class CLASS]`. Never one-off `cp`/`mv` into the artifact tree. ACL classes: `property` (700/600), `schematics` (750/640), `vendor-docs` (755/644), `source-files` (750/640).
- **Before answering a question that references a roadmap artifact**, consult `~/.platform-registry/artifacts/<deliverable>.json` first to discover what's actually persisted (avoid re-reading the same PDF from chat context multiple times — the F9 anti-pattern).
- **Backup posture:** QNAP RAID + native snapshots are the durability layer for QNAP-hosted artifacts. Restic targets MinIO **on QNAP** (`s3://192.168.10.201:9000/backups`), so adding artifact paths to `BACKUP_DIRS` would be circular. Off-host replication is a future deliverable.
- **Substrate-defining-deliverable exemption:** D-17-37 itself does not need to be retrofitted through its own substrate. Doctrine + chronicle: `docs/architecture-facts/integration-audit-doctrine.md` Finding 5.

### Integration Health-Check Doctrine (D-17-38)
- **Container-healthy ≠ integration-healthy (Gap F5).** A health endpoint that returns 200 because no probes ran is silence, not evidence. Layer-3 (integration) checks must execute against real upstream and classify failures by HTTP status (401/403 → critical, 5xx → critical, network → critical, app-level warnings → warning). The selfheal layer must escalate auth failures to *critical*, not downgrade them to warnings — see `framework/health_checker.py` `_classify_http_exc`.
- **Credential-source authority is the running service, not Vault.** When Vault holds external-API credentials for an existing service (Sonarr/Radarr/Prowlarr API keys), the live service config (e.g. `<ApiKey>` in `/config/config.xml`) is canonical. Harvest from the running container, then write to Vault. Reading Vault and writing back to the service is the wrong direction and creates drift.
- **URL values in Vault are part of the credential, not metadata.** A service URL that resolves on the host but not from inside a consumer container is a broken credential record. For dashboard-style consumers on a Docker network, the canonical form is `http://<container-name>:<port>` (container DNS), not `http://<host>.<lan-tld>:<port>`. The D-17-38 root cause was Vault holding `mac-mini.internal` URLs that didn't resolve from the dashboard container.
- **Reachability vs storage-stats are different probes.** A bare TCP connect to the appliance port proves "alive on the network" without requiring TLS handshake or auth. Application-level probes (HTTPS GET, API call) prove "service is responsive" but can fail for orthogonal reasons (TLS incompatibility, cert trust). The connector pattern: try the application probe first, fall back to TCP-connect for reachability classification — see `connectors/qnap.py` `health_check`.
- **Hash-only verification — `/proc/1/environ` reads must redact (D-17-38 near-miss):** the D-17-26 sub-doctrine pattern `tr "\0" "\n" < /proc/1/environ | grep ^VAR=` MUST be piped through a redactor when the var holds a credential. Correct form: `... | sed 's/=.*/=<set>/'` for presence-only checks, or `... | grep -c ^VAR=` for count-only. Bare grep emits the value; doing this on a credential variable counts as a credential-display incident even when "just diagnosing".
- **Chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 8.

### Roadmap Ingestion Flow Doctrine (D-17-39)
- **Roadmap items with binary artifacts MUST flow through the ingestion surface, not direct filesystem placement.** Canonical entrypoint: `scripts/roadmap-create.sh <D-NN-NN> "<title>" [--status STATUS] [--reference TEXT] [--artifact <path>] [--class CLASS]`. The script composes D-17-37 substrate (artifact-ingest.sh) + framework row insertion + OpenProject WP creation in one self-contained transaction.
- **Operator never invokes `scripts/artifact-ingest.sh` directly for new deliverables.** That script is the substrate primitive; `roadmap-create.sh` is the operator-facing surface. Direct `artifact-ingest.sh` usage is reserved for substrate-defining or substrate-bypass cases (D-17-37 self-test, retrofits without an existing roadmap intake event).
- **When recommending roadmap intake**, always include the artifact-field consideration. The four-question checklist for any new deliverable:  (a) is there a binary artifact (PDF, schematic, vendor doc, source dump)?  (b) which ACL class fits?  (c) does it close at the storage layer (D-17-37) or also need flow-layer integration (D-17-39)?  (d) is this a *new* row or an *update* to an existing one — for closing an IN PROGRESS row whose gating artifact has now landed, use `roadmap-create.sh <ID> "" --update-existing --artifact <path>` (status defaults to DONE; rejects already-DONE/DEFERRED rows; idempotent on re-run).
- **Close-out flow (`--update-existing`, landed 2026-05-03):** preserves existing title cell verbatim, augments the reference column with the qnap:// pointer + a `Closed via --update-existing <date>` note, flips the status word. Idempotency: a re-run with the same artifact + same target status against an already-DONE row exits 0 with a no-op message rather than erroring. Rejects: missing `--artifact` (exit 64), row not found (exit 68), row already DONE/DEFERRED with different artifact (exit 70). The OpenProject sync path picks up the row change automatically via its diff-against-external_id mechanism — no separate PATCH path needed.
- **Substrate-defining vs consumer retrofit asymmetry (Path 1 worked example, D-17-39 WP-04):** substrate-defining deliverables retrofit cleanly via synthetic placeholders (the substrate is what's being validated, not the artifact). Consumer deliverables (D-17-35 et al) retrofit ONLY with real artifacts; closing a consumer deliverable on a placeholder is false-positive completion (Gap F7 territory). When the real artifact isn't available, validate the flow with a synthetic placeholder, restore the consumer's IN PROGRESS state with a note, and remove the placeholder from canonical store.
- **Backlog (deferred, not blocking):** MCP-tool surface (`roadmap_create_with_artifact` exposed via xindex-mcp) once chat-attachment-pickup primitive is reliable in this surface — was Option (c) in the WP-02 surface decision, deferred on primitive-stability grounds. Option (b) (OpenProject attachment hook) explicitly rejected on doctrine inversion grounds (would invert D-16-02.A "repo-owned docs are canonical" by making OP the source of truth). The `--update-existing` flag (originally listed here) landed 2026-05-03 — see "Close-out flow" bullet above.
- **Chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 5 (extended with flow-layer closure section).

### DNS Authority Doctrine (D-17-21)
- **Dnsmasq is the sole DNS authority for `*.internal` on this platform.** It runs on OPNsense (192.168.10.1) on port 53. All `.internal` records (Caddy fronts + bare-hostname DHCP reservations) live in Dnsmasq host entries. Verified via `/api/dnsmasq/settings/searchHost`.
- **Unbound is forbidden.** It was disabled (`unbound.general.enabled=0`, service stopped) at D-17-21 close after being identified as unintended residue. If a future session observes Unbound running on this OPNsense, treat that as drift and re-disable. Do not author any deliverable that re-enables Unbound; do not reference Unbound in service routing or audit scripts except as historical context for D-17-21.
- **Adding a `.internal` record:** OPNsense GUI (Services → Dnsmasq DNS → Hosts → +) or via API. For Caddy-fronted services the IP is always `192.168.10.145` (Mac Mini). For non-Caddy direct-port services (qnap, mac-studio, etc.) the IP is the upstream host. Reference: `docs/architecture-facts/opnsense-dns-authority.md`.
- **Parity check is enforced.** `scripts/check-repo-coherence.py caddy-dns-parity` exits 1 on missing or wrong-target records. Adding a new Caddy `*.internal` site without a matching Dnsmasq record will fail pre-commit. Refresh: `scripts/check-repo-coherence.py caddy-dns-parity --refresh` (writes `~/.platform-logs/caddy-unbound-parity.json`).
- **Two probe shapes; prefer the specific:** Dnsmasq accepts both `host=foo, domain=internal` (Shape 1) and `host=foo, domain=""` bare-hostname (Shape 3). The parity check matches Shape 1 first; Shape 3 is a fallback only. A bare-hostname DHCP reservation pointing at an upstream IP must not be matched against a Caddy-fronted `*.internal` site that needs the Mac Mini IP. Worked example: `homeassistant.internal` Shape 1 → 192.168.10.145 (Caddy proxies to .141:8123); bare `homeassistant` Shape 3 → 192.168.10.141 (HA hub direct). Both are valid; the parity check correctly prefers Shape 1.
- **Configuration audits verify against operator-stated intent, not currently-running config.** Running state can be unintended residue (the D-17-21 root cause: Unbound was running with 38 records as residue from a prior session, but operator intent was Dnsmasq-as-sole-authority). Architecture-facts in this repo are the authority signal; probes detect divergence; divergence is drift, not evidence about correct posture. Sub-doctrine in `integration-audit-doctrine.md` Finding 9.
- **Migration script as reference pattern:** `scripts/d-17-21-dns-migration.sh` is the worked example for any future cross-daemon record migration (snapshot → add → reconfigure → validate-pre-flip → disable-source → port-flip → validate-post-flip; halt on any error).
- **Chronicle:** `docs/architecture-facts/opnsense-dns-authority.md` (now VERIFIED, no longer provisional); `docs/architecture-facts/integration-audit-doctrine.md` Finding 9; KI-009 RESOLVED at D-17-21 close.

### Buildarr Config-as-Code Doctrine (D-17-44)
- **Buildarr is the canonical config authority for Radarr and Prowlarr.** Declarative state lives in `config/arr-stack/buildarr/buildarr.yml`. Any manual UI change to Radarr/Prowlarr settings (quality profiles, custom formats, indexer config, application URLs) that is not reflected in that YAML will be reverted on the next `buildarr-run.sh` execution. To make a permanent change: edit the YAML, commit it, then run `scripts/buildarr-run.sh`.
- **Scope (as of D-17-44, 2026-05-03):** Radarr (full coverage) + Prowlarr applications-only. Sonarr v4.0.17 and Sportarr are out of scope — Buildarr plugin does not support them yet. They remain under reactive/manual management. Prowlarr indexer definitions and download clients are also out of scope (plugin schema gap).
- **Buildarr does NOT manage Vault secrets.** Credentials remain in Vault; Buildarr reads them via Vault Agent sidecar (AppRole `buildarr`, policy `config/vault-policies/buildarr-policy.hcl`). The `${RADARR_API_KEY}` / `${PROWLARR_API_KEY}` placeholders in `buildarr.yml` are substituted at runtime by `scripts/buildarr-run.sh`.
- **Run schedule:** daily at 03:00 via launchd `com.iap.buildarr-sync`. Manual run: `scripts/buildarr-run.sh`. Syntax check only (no mutations): `scripts/buildarr-run.sh --check`. **Verification:** check heartbeat freshness at `/Users/admin/.platform-logs/buildarr-sync.heartbeat` (updates within 24h on healthy schedule). `launchctl list | grep com.iap.buildarr-sync` may return empty between firings for `StartCalendarInterval`-only jobs — heartbeat is the canonical liveness signal, not `launchctl list`.
- **Drift detection workflow:** after any manual arr-stack session, run `buildarr radarr dump-config` + `buildarr prowlarr dump-config` against the live instances and diff against the committed YAML. Any diff IS the empirical drift record (F11 first worked example: D-17-38 URL drift would have been detected and reverted automatically).
- **Chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 11.

### arr-stack Metrics Observability Doctrine (D-17-46)
- **Canonical metrics path for arr-stack is Scraparr → vmagent → VictoriaMetrics → Grafana.** This is the Phase 18 §18.G component-1 observability substrate and is a sibling to D-17-38 selfheal, not a replacement.
- **Layer split is mandatory:** `selfheal.py` remains remediation/classification logic; exporter metrics are continuous telemetry. Do not add Prometheus-metric responsibilities to selfheal.
- **Credential pattern is unchanged:** Scraparr reads Sonarr/Radarr/Prowlarr API keys from Vault-rendered `/vault/secrets/credentials.env` via Vault Agent sidecar. Key comparisons remain hash-only (`sha256[:12]`), never value output.
- **Current scope:** Sonarr/Radarr/Prowlarr metrics in scope; Sportarr exporter coverage is out-of-scope for D-17-46 and tracked as follow-on backlog under §18.G.
- **Dashboard baseline:** `docker/grafana-provisioning/dashboards/arr-stack-overview-p18.json` is the provisioned minimal dashboard. Community dashboard adaptation is a backlog item (datasource-templating normalization required).

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
- `git commit --no-verify` is forbidden — pre-commit hooks are load-bearing security (`detect-secrets`, `yamllint`, trim-trailing-whitespace, end-of-files, JSON/YAML validation, plus phase/ADR/launchd/Mac-Studio-reach/Caddy-DNS-parity conditional checks). Bypassing the gate is not an option; fix the cause when a hook blocks a commit.
- `.secrets.baseline` auto-rebuild via `detect-secrets scan --baseline .secrets.baseline` is forbidden — full-rebuild sweeps unrelated repo-wide findings (`connectors.yaml`, `obot/tools.yaml`, `nextcloud/vault-mapping.yaml`, `qnap-syncthing/qnap-config.xml.snapshot`, `vault-mapping.yaml`) into the whitelist. Surgical hand-edits only: add specific new entries in alphabetical position, refresh `generated_at`, no other changes.
- LiteLLM's `openai/` provider requires a non-empty `api_key` field even for unauthenticated upstreams — the literal placeholder `"not-needed"` is the documented convention. detect-secrets flags this as a false positive; whitelist via surgical `.secrets.baseline` entry per the rule above.

### Common Failure Modes

Patterns that recur and should be actively guarded against during brief authoring and execution:

- **Ollama-anchoring** — defaulting to Ollama-shaped solutions even after architectural demotion. vllm-mlx is the default stunt-double now; tier-1 Ollama remains for small-model fallback only. When in doubt, route through the new pattern.
- **Stale-context drafting** — assuming a deliverable is greenfield when it's already DONE. Always check `docs/PROJECT_FRAMEWORK.md` §9 status table and `ls docs/phase-NN/` before referencing any deliverable. Recurring miss; treat as default failure mode.
- **Brief bloat** — long briefs that obscure the actual ask. Tight is better. Pre-flight reads belong inside the brief; speculative content does not.
- **Friction stacking** — per-step approval requests instead of autonomous execution between checkpoint gates. Brief should specify hard stops; everything else runs through.

### LLM Access Doctrine

The platform's default LLM access is local Ollama via Claude Code:

```
claude-local       # → local Ollama (free, no quota; orchestrator: qwen2.5-coder:32b)
claude-pro         # → Anthropic via Pro subscription (uses quota)
claude (aliased)   # → defaults to claude-local
```

Use `claude-local` for routine work: implementation, refactoring, documentation, file exploration, code review.

Use `claude-pro` ONLY for high-judgment tasks where Anthropic-quality reasoning is genuinely required. Pro quota is finite; treat it as expensive.

**Platform services must NEVER depend on Anthropic API access.** `secret/anthropic/api` is permanently unused and deleted from Vault. Any service that needs LLM capability uses local models via litellm or Ollama directly.

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

### Current Inference Stack

State as of HEAD `81db99ea`; re-verify on session start since this changes faster than file commits.

- Tier-1 Ollama on port 11434 (untouched; qwen2.5-coder:7b for fast tasks)
- LiteLLM proxy on port 4000 (config at `configs/litellm/config.yaml`; live path at `~/local-ai-workstation/configs/litellm/config.yaml` is symlinked to the repo file)
- vllm-mlx on port 8500 (default stunt-double; persistent via launchd `com.adriancox.vllm-mlx`; serves `mlx-community/Qwen3-Coder-30B-A3B-Instruct-3bit`)
- Ollama stunt-double on port 11435 = DEMOTED (plist renamed to `.plist.disabled`, preserved for one-step rollback)

Cross-reference: @docs/orchestration-layer-build-mlx-integration-test.md

### Provenance Governance

- Cisco Provenance Kit at `~/repos/model-provenance-kit/` on Mac Mini and MacBook (NOT a repo subdir; outside the integrated-ai-platform repo).
- Wrappers: `scripts/verify-model-provenance.sh`, `scripts/ollama-pull-verified.sh`, `scripts/hf-download-verified.sh`, `bin/ollama_pull_with_provenance.sh`.
- Doctrine: @docs/architecture-facts/model-provenance.md, @docs/architecture-facts/model-provenance-doctrine.md.
- Override log: `docs/_provenance/overrides.log`. Backfill docs: `docs/_provenance/backfill-YYYY-MM-DD.md`.
- Map files (BOTH active, neither supersedes): `config/model-hf-map.yaml` (D-17-92, flat, used by `verify-model-provenance.sh`) AND `config/model_provenance/ollama_to_hf_mapping.yaml` (D-17-122, structured; has `hf_direct_models:` stanza for HF-direct pulls; used by `ollama_pull_with_provenance.sh`).
- Verdict classes: verified-specific (exit 0), unverified (exit 1), marginal (exit 2), verified-base-family (exit 3). Plus operator-accepted (Path B) — doctrine-level disposition for hardware-blocked scans, not a wrapper exit code; see `model-provenance-doctrine.md` §"Operator-accepted (Path B)".

### Execution surfaces

Execution surface = the runtime that drives a coding/operations session: reads files, calls tools, edits the repo, runs commands. This is a *different axis* from "LLM Access Doctrine" above (which is about which model answers a single inference). One execution surface can be paired with multiple LLM-access modes; one LLM-access mode can drive multiple execution surfaces.

Three surfaces are in use as of 2026-05-03:

- **Claude Code** — Anthropic's CLI. Default for high-judgment work, frontier-PM, multi-step workflows. Pairs with `claude-local` (Ollama-backed via litellm) or `claude-pro` (Anthropic API). All capability surfaces enabled.
- **Codex** — OpenAI's CLI. Used in parallel for cross-check / second-opinion review. Capability surface broadly enabled.
- **Goose** (D-17-13) — Block's open-source agent CLI, Apache 2.0. Paired with native Ollama provider + qwen3-coder:30b on Mac Studio (no litellm hop). **Current state: Posture 2 (dual-review)** — capability-validation gate is complete; enablement remains constrained and all Goose-authored output is reviewed by operator/frontier surface before merge or platform-state change. See `docs/architecture-facts/goose-capability-boundary.md` for current posture and promotion criteria.

The intended trajectory (§18.O migration framework): progressive migration of execution-surface work-classes from frontier-cost surfaces (Claude Code under `claude-pro`, Codex) to local-cost Goose+T3-B, with frontier surfaces doing correctness review on Goose output. First measured economics datapoint (D-17-13 WP-06): drafting a runbook from 3 source files completed in 51 seconds on local Mac Studio compute, ~75% Goose-authored / ~25% frontier-corrected on review.

Operating rule in Posture 2: **Goose output is dual-reviewed before enactment.** Changes informed by Goose run through operator/frontier review prior to merge or any platform-state mutation; promotion beyond this posture remains gate-driven in the Goose capability-boundary doctrine.

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
- **§6 final state (Increment 1.5.A):** All 16 credential-consuming services have Vault Agent sidecars. 15 were covered by prior block work; plane-web decommissioned as N/A (frontend, no credential consumption). The orphan plane-web policy was removed as part of that close.
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
work — read via the OpenProject UI or API directly. (A CLI convenience
flag was previously prescribed here but the implementation never landed
— removed 2026-05-04 per D-17-81 H2; documenting non-existent flags is
the same fabrication-as-canonical pattern chronicled in F17. If a CLI
backlog reader is wanted, file as a separate deliverable to implement
properly.)

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

### OpenProject Enrichment Doctrine (D-17-55)
- `PROJECT_FRAMEWORK.md` §9 is canonical; OpenProject is an enriched projection.
- Enrichment fields are maintained by `scripts/openproject-enrich-from-framework.py` (description, percentageDone, phase, deliverable_class, finding_refs, dependencies).
- Manual-edit safety is default: non-empty conflicting managed fields are preserved unless `--force` is explicitly used.
- `customField1` (Plane RM ID) and `customField2` (External ID) are preserved as mapping/sync keys.
- `scripts/openproject-sync-from-framework.py` now runs enrichment as a follow-on pass unless `--skip-enrich` is passed.
