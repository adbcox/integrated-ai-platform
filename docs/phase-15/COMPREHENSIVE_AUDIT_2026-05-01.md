# Comprehensive System Architecture & Fitness Audit

**Date:** 2026-05-01
**Auditor:** Claude Code (claude-opus-4-7), running directly on `mac-mini.internal` (control plane, .145)
**Scope:** Every running service, every ADR, every integration, every architectural decision
**Status:** IN PROGRESS — written incrementally, sections delivered in priority order

---

## Document Conventions

- **VERIFIED** — claim backed by command output captured in this session
- **CITED** — claim backed by file path with line numbers
- **INFERRED** — reasoned from VERIFIED/CITED facts, not directly observed
- **ASSUMED** — flagged for follow-up; not validated
- Severity tags: **[CRITICAL]** | **[HIGH]** | **[MEDIUM]** | **[LOW]** | **[INFO]**

## Snapshot at audit start (VERIFIED)

- 63 containers running (`docker ps`, captured to `/tmp/audit-containers.txt`)
- Vault: initialized, unsealed, transit-sealed, file storage backend, no DR/perf replication (`/v1/sys/health` + `/v1/sys/seal-status` 2026-05-01 ~05:38 PT)
- Host uptime: 7d 21h, load avg 2.28 / 2.20 / 2.15 — sustained moderate load on M4 Pro 48 GB
- Working tree dirty: `M docs/adr/ADR-A-007-media-sync-syncthing.md`

## Audit reordering (rationale)

User-approved reorder vs the original 1→14 sequence. Time-sensitive findings first:

1. **Section 12** — Mac Studio Day-1 risk (Studio arrives today, blocks tomorrow's work)
2. **Section 11** — Vault failures root cause (3rd failure 2026-04-30, systemic)
3. **Sections 1–7** — Forensic verification (factual base)
4. **Sections 8, 9** — Backup, docs (operational debt)
5. **Sections 10, 13, 14** — Strategic synthesis (depends on 1–9)
6. Executive summary + risk register + Phase 17+ roadmap

---

## Executive Summary

**The platform is architecturally sound, operationally fragile, and not yet ready to operate autonomously. The fragility is concentrated in five fixable areas; the soundness is real and worth preserving.**

### What is working well

- **Architectural doctrine is mature.** 17 ADRs, an IV&V loop pattern (A-011), an equivalence harness doctrine (A-012), and folded-gates discipline (A-013). The platform operates with the sort of decision discipline that production systems acquire only after years.
- **Container hardening is genuine.** ~25 of ~28 compose-managed services follow `cap_drop:[ALL]` + `no-new-privileges:true` doctrine; the 3 documented exceptions (D#30) have specific blocked-on-upstream reasons.
- **Cloud-LLM cost exposure is zero.** Phase 13.5 deprecated all cloud-LLM routes; the platform depends only on local Ollama. A genuine architectural achievement.
- **Vault is correctly chosen and structurally well-deployed.** Transit auto-unseal, Shamir 5-of-3, AppRole-per-service, audit log doctrine. The recurring incidents are *process* failures, not tool failures.
- **Phase 14 closeout was clean.** D-LOG (Loki/Promtail), D-ZBX (Zabbix→Prometheus bridge), and D-RST (restore test) all landed correctly.

### What is broken — five things, in priority order

1. **Backup chain is silently broken end-to-end (Section 8).** `backup` AppRole missing post-KV-loss; `scripts/backup.sh` log redirected to unwritable path. **No backup has succeeded since 2026-04-30.** Until fixed, every other recovery story in this audit is hypothetical.
2. **Vault audit device disabled since 2026-04-30 (Section 11).** Forensic capability lost; CLAUDE.md outstanding item documented but not closed.
3. **Zero production alerts exist (Section 7).** vmalert not deployed; Uptime Kuma 11 of 12 monitors DOWN; no Grafana unified-alerting rules. The system has no way to tell you it's broken.
4. **No PreToolUse hooks for destructive Vault operations (Section 11 RCA, Section 13 Blocker 1).** The 2026-04-30 KV loss was a typed command; without hooks, the next typed command can do it again. **Single highest-leverage fix in the audit.**
5. **Configuration drift across CMDB consumers (Section 4).** ADR-A-014 says `CMDB_SOURCE=netbox` is the default, but only 1 of 4 consumers defaults to it; the live `topology-api` reads the deprecated YAML. Doctrine and reality have diverged.

### Same-week action list — ~6 operator-hours total, fixes top 5

| # | Action | Time | Section ref |
|---|---|---|---|
| 1 | Fix backup chain: rebuild `backup` AppRole, fix log redirect, take baseline Restic snapshot, verify | 2h | S8, S11 |
| 2 | Re-enable Vault audit device | 0.2h | S11 |
| 3 | Author + install PreToolUse hook for destructive Vault commands | 2h | S11, S13 |
| 4 | Stand up vault-test instance for pre-prod rehearsal | 1h | S11, S13 |
| 5 | Reconcile 6 phantom Vault paths from postmortem; close CLAUDE.md outstanding items | 0.5h | S11 |
| 6 | Fix CLAUDE.md broken doc pointers (DEPLOYMENT_GUIDE / TROUBLESHOOTING / HANDOFF_GUIDE refs) | 0.5h | S9 |

**Total: ~6.2h. Closes the entire CRITICAL row of the risk register below.**

### Mac Studio Day-1 (2026-05-01) recommendation

**GO with three pre-Day-1 actions and one deferral.** Full rationale in Section 12.

- ✅ **Pre-Day-1 (~10 min):** confirm working Vault root token; confirm Mini IP/SSH; confirm Studio physical setup ready
- ✅ **Execute Day-1:** Tasks 1-7 of `~/mac-studio-day1-execute.sh`
- ⛔ **DEFER:** Task 8 (Headscale enrollment) — Headscale single-client utility doesn't justify Day-1 risk; revisit when 2nd client lands

### What to expect from Phase 16-17

The combination of the same-week fix list and Section 12's GO recommendation creates a clean Phase 16 opening: backup chain working, Vault safe-railed, Studio integrated. **Phase 16 work then proceeds against a stable, observable, recoverable platform — for the first time since Phase 13 began.** This is the most important shift this audit recommends.

---

## Cross-cutting findings surfaced before section work

These are anomalies caught while gathering raw inventory; they are documented up-front because they affect multiple sections and inform the audit posture.

### XF-1 [HIGH] All `vault-agent-*` sidecars exited 6–7 hours ago with code 0

Captured from `docker ps -a`: every `vault-agent-<svc>` container shows `Exited (0)` 6–7 hours ago. 28 sidecars are dead.

**What this means:**
- Templates were rendered once at startup, written to bind-mount, sidecar exited cleanly
- No active credential renewal — if any rendered secret is short-lived (token, lease), services will silently fail at TTL expiry
- If any KV value rotates in Vault, services will not pick it up without manual restart of the sidecar
- Sidecars exited *together* ~7h ago — suggests either a host-wide event (Docker restart, daemon reload) or a deliberate one-shot run pattern

**To investigate (Section 5 — credential flow):**
- Are these sidecars *configured* as one-shot (`exit_after_auth = true`) or are they crashing?
- If one-shot by design, this is an architectural choice with implications for secret rotation
- If crashing, why does no monitoring catch it? (Section 7)

This is consistent with the Vault KV mount data loss postmortem (2026-04-30) — when KV was rebuilt, sidecars would have been restarted/affected.

### XF-2 [INFO] `seal-vault` running 2 hours less than `vault-server`

`vault-server` healthy 7h, `seal-vault` (transit auto-unseal) up 7h but no healthcheck status. Earlier seal-vault was BROKEN per `docs/phase-15/seal-vault-compose-BROKEN-2026-04-30.yml`. Current state warrants verification of unseal recovery on next vault restart.

### XF-3 [MEDIUM] `control-plane` and `catt-controller` exited 16h ago

Both `Exited (0)` 16h ago — one-shot containers, or services that died and weren't restarted? `control-plane` name is suggestive — if this is meant to be the platform's control plane container (per CLAUDE.md "Mac Mini is the control plane today"), being dead 16h is a problem.

### XF-4 [INFO] One image displayed by hash, not name

`mkdocs` runs as `868ad4d39fb5`, `openhands-app` as `5c0dc26f467b`, `structurizr` as `16af27248e96` — locally-built images without tags. Reproducibility risk if Docker prunes the image and the build context is gone.

### XF-5 [HIGH] Stale Vault root token in `~/vault-init-keys.txt`

The init-keys file dates 2026-04-28 17:36 (pre-KV-loss). The "Initial Root Token" listed in it (`[REDACTED — invalid post-recovery token, see D-17-84 for chronicle]`) is rejected by the post-recovery cluster as `invalid token`. Anyone reading this file expecting it to grant root would be wrong — and would not realize until they tried to use it.

The recovery did issue a new root token (the vault-RCA agent ran `vault audit list` successfully, so a working root token exists somewhere — likely in `~/vault-server-autounseal-token-20260430.json` which is `-rw-------` (mode 0600) and dates 2026-04-30 22:10). But the older file was never marked stale and was never updated to point at the working token.

**Risk:** during the next incident, the operator (or an agent) will follow muscle memory, read `~/vault-init-keys.txt`, get a token that fails, and waste minutes diagnosing "vault auth broken" when really the file is stale.

**Fix (5 min):** rename the stale file to `~/vault-init-keys-20260428-PRE-KV-LOSS-INVALID.txt`, write a fresh `~/vault-init-keys-20260430.txt` with current root token + recovery shamir keys (or a clear pointer to where they live).

---

## Section 12 — Mac Studio Day-1 Risk Assessment [TIME-SENSITIVE — STUDIO ARRIVES TODAY]

**Reviewed artifacts:**
- `~/mac-studio-day1-checklist.md` (456 lines, dated 2026-04-30, "paper-only; do not execute tonight")
- `~/mac-studio-day1-execute.sh` (459 lines, gated runner with confirm prompts)
- Cross-referenced against current Mini state (vault, headscale, netbox)

### Headline finding: the plan is *better* than I expected. The risks come from environmental drift since 2026-04-30, not from the plan itself.

The execute script enforces hard guardrails the user clearly internalized after the recovery incident: 30-min/task cap, no autonomous loops, no volume deletions, every change has a stated rollback, every task gates on operator confirmation. Pre-flight blocks if Vault is sealed. Tasks 6 (LiteLLM) and 8 (Restic) explicitly call out additivity and the rewire log. This is recovery-aware engineering — appropriate posture.

The risks are **prerequisite drift** (things changed in the system between when the checklist was written 2026-04-30 and execution today 2026-05-01) and **silent dependencies** (steps that don't have explicit prerequisite checks).

### Critical pre-flight failures the script does NOT catch

These will cause Day-1 tasks to fail in ways that look like "Studio integration is broken" when really the Mini is degraded:

#### S12-R1 [CRITICAL → blocks Task 7] Restic backup chain is broken
- Cross-cutting agent confirmed: `backup` AppRole was lost in 2026-04-30 KV mount data loss and never re-provisioned. `scripts/backup.sh` exits at AppRole login. The log-redirect bug (writing to `/var/log/restic-backup.log` which `admin` can't write) silently swallows the failure.
- **Day-1 Task 8** appends Studio dirs to `BACKUP_DIRS` and adds Studio-side cron — but if the Mini-side script doesn't run, Task 8 is a paper-edit. The Day-1 close checklist won't catch this.
- **Mitigation:** before Task 8, fix backup.sh log redirect (`tee -a "${HOME}/Library/Logs/restic-backup.log"` or similar writable path) AND re-provision the `backup` AppRole. Otherwise defer Task 8.

#### S12-R2 [CRITICAL → blocks Task 7] Vault audit device still disabled
- `vault audit list` returns "No audit devices are enabled." Last `audit.log` write was 2026-04-30T13:21Z (~16h ago, during the cascade).
- Day-1 Task 1 (NetBox device create), Task 7 (Zabbix host create), and any AppRole reads will not be recorded. If Studio integration causes a credential leak or unintended modification, **there is no audit trail**.
- The Studio onboarding will *create new attack surface* (new SSH endpoint, new Caddy upstream, new Headscale node, new Zabbix agent) — adding it under an unaudited Vault is a procedural regression.
- **Mitigation:** re-enable audit device BEFORE Task 1: `docker exec vault-server vault audit enable file file_path=/vault/logs/audit.log`. ~30 seconds. The CLAUDE.md "Outstanding" list called this out — it has been outstanding for 24+ hours.

#### S12-R3 [HIGH → blocks Task 2] Headscale user `homelab` does not exist
- `docker exec headscale headscale users list` returns ONE user: `admin` (created 2026-04-27 18:08:43, no email).
- Day-1 Task 2 hardcodes `--user homelab` in the preauthkey create command. The script comment says "user 'homelab' must already exist; verify with `docker exec headscale headscale users create homelab`" — but the script does NOT actually verify or create the user.
- The script will print the error from `headscale preauthkeys create` and the operator will need to choose: create `homelab` user, or change the script to `--user admin`. Either is fine but it stops Task 2 cold.
- **Mitigation:** decide now — `homelab` (semantic) or `admin` (existing). If `homelab`, run `docker exec headscale headscale users create homelab` BEFORE starting Day-1.

#### S12-R4 [HIGH → reveals operational gap] Headscale has zero registered nodes
- `docker exec headscale headscale nodes list` returns empty body (no nodes).
- This contradicts the memory file `phase13_30day_plan_completion.md` which lists "Headscale VPN" as completed. Either nodes deregistered (after a Headscale restart? the headscale container is "Up 9 hours" — uptime matches the 7-hour Vault Apr 30 cluster restart cascade) or the original deployment never enrolled the Mini/laptop.
- **Implication for Day-1:** Task 2 onboards Studio as the *first* node. Studio will join an empty mesh. There is no other peer to validate connectivity against. Caddy CA trust step (Task 2 hard-stop) will need separate validation since `headscale.internal` resolution from Studio depends on Caddy serving + Studio trusting Caddy's local CA.
- **Mitigation:** acknowledge the empty mesh; verify Studio→Mini reachability over **LAN IP** (`192.168.10.146` ↔ `192.168.10.145`) before relying on `*.internal` resolution.

#### S12-R5 [HIGH → blocks Tasks 1, 7] Cannot independently verify NetBox + Zabbix API tokens are in Vault
- Day-1 Task 1 reads `secret/netbox/api` (field `token` or `api_token`). Task 7 reads `secret/zabbix/api` (field `api_token`).
- I cannot verify these paths exist with my available token (the stale `~/vault-init-keys.txt` token is rejected — see XF-5). The vault-RCA agent enumerated 47 KV paths post-recovery; the user should check whether `netbox/api` and `zabbix/api` are among them, or whether the rebuild used a different naming scheme.
- The KV-loss postmortem listed paths that were rebuilt; the audit found that the rebuild used different names than the postmortem expected (e.g. `inventree/postgres` not `inventree/db`). Same risk applies to API tokens.
- **Mitigation:** before Task 1, run with the working root token: `vault kv list secret/netbox/` and `vault kv list secret/zabbix/`. Confirm the field names match the script's `vault kv get -field=` calls. If they don't, edit the script BEFORE running.

### Plan-level risks (issues with the plan itself, not environment drift)

#### S12-R6 [MEDIUM] Task 5 native Ollama on Studio bypasses Colima — different management surface than Mini
- Studio Task 5 installs Ollama via Homebrew, runs natively, sets `OLLAMA_HOST=0.0.0.0:11434` via `launchctl setenv`. Mini's Ollama (per memory) runs the same way.
- This is *consistent* with current Mini posture but inconsistent with the Phase 15 plan's framing of Studio as a "Colima compute node". Two operating models for the same workload.
- ADR-A-016 (canonical patterns registry) should be checked to see whether native Ollama vs containerized is captured as a pattern. If not, this is the moment to document the choice.

#### S12-R7 [MEDIUM] Caddy validate uses host-header `--resolve` but Studio LAN IP not in DNS
- Task 3 verification: `curl -ks --resolve ollama-studio.internal:443:127.0.0.1 https://ollama-studio.internal`. This validates Caddy serves the route, NOT that the upstream `192.168.10.146:11434` is reachable. With `Up 9 hours` for caddy and Ollama not yet installed on Studio, the verification will return `502 Bad Gateway` on first run — that is correct, but the operator should know to expect it.
- The script logs "Verify:" then runs the curl, but doesn't tell the operator that `502` is the *expected* state until Task 5 completes.

#### S12-R8 [MEDIUM] vmagent restart vs reload
- Task 4 does `docker restart vmagent`. vmagent supports `kill -HUP` for config reload. A restart drops in-flight scrape state (~30 seconds gap in metrics for ALL existing scrape jobs, not just Studio). Not catastrophic but unnecessary.
- **Better:** `docker exec vmagent kill -HUP 1` (if vmagent runs as PID 1). Test in dry-run first.

#### S12-R9 [LOW] LiteLLM additive but no smoke test of Mini routes after restart
- Task 6 verification lists models (`/models`) but does not actually invoke a Mini-side route to confirm it still works. If the additive YAML edit corrupts the file in a subtle way (indentation, duplicated key), `litellm-gateway` may start "healthy" but Mini routes silently fail.
- **Mitigation:** add a smoke test: `curl -s http://localhost:4000/v1/chat/completions -d '{"model":"qwen-coder-32b","messages":[{"role":"user","content":"ping"}]}' | head` — confirms a Mini-side route returns 200 before declaring Task 6 done.

### Plan-level strengths (worth preserving)

- **Pre-flight is gated.** Vault sealed → STOP. Working tree dirty for Caddyfile/scrape.yml → WARN. This is the right default.
- **Task 5 prompts before 50 GB model pull.** Operator-confirmation on disk-/network-expensive operations.
- **Task 6 captures out-of-repo edit in REWIRE_LOG.md and creates a `.bak.timestamp` file.** Aligns with the "out-of-repo compose changes require pre/post snapshots" doctrine in CLAUDE.md.
- **Task 8 explicitly excludes `~/.ollama`.** Prevents 50+ GB ballooning of Restic repo.
- **Day-1 close checklist resolves the M4-Pro vs M5 doc contradiction.** Updates CLAUDE.md and ARCHITECTURE.md from `system_profiler` ground truth. (Note: per memory, this was already corrected to "M4 Pro 48 GB" on 2026-05-01 in CLAUDE.md — the close checklist line is now stale.)

### Blast radius if Studio integration fails

If any Day-1 task fails *and rollback works*, blast radius is contained:
- Tasks 1, 2, 7 (NetBox device, Headscale node, Zabbix host) are pure additions — `delete` the new resource and you're back to baseline.
- Task 3 (Caddy) — `git checkout docker/caddy/Caddyfile && docker exec caddy caddy reload`. Verified as a clean revert pattern.
- Task 4 (vmagent) — `git checkout && docker restart vmagent`. Same.
- Task 6 (LiteLLM) — out-of-repo, but `.bak.timestamp` is created. Manual revert is `cp <bak> litellm_config.yaml && docker restart litellm-gateway`. This is the *most fragile* rollback because it depends on the operator remembering the .bak file exists.
- Task 5 — runs ON Studio; if it fails, Studio is in a transitional state but Mini is unaffected.

If a Day-1 task fails *and rollback also fails*, the worst-case scenario is:
- Caddy fails to reload after a malformed config edit → `docker exec caddy caddy reload` returns error → ALL Caddy routes serve last-good config (Caddy reload is atomic). Recovery: `git checkout` + `docker restart caddy` (full restart, ~10-second LAN gap).
- vmagent fails to restart → `docker logs vmagent` and revert YAML manually.
- LiteLLM corruption (wrong YAML indent breaks ALL routes including Mini) → docker logs reveal it, restore from .bak.

**The Day-1 plan does NOT have a "blast radius could escape Studio" risk.** Worst case is a few minutes of Caddy/vmagent/LiteLLM hiccup on the Mini, fully recoverable.

### Go / no-go recommendation

**GO with three pre-Day-1 actions:**

1. **Re-enable Vault audit device** (S12-R2) — 30 seconds, eliminates the "we made changes blind" risk.
   ```
   docker exec vault-server vault audit enable file file_path=/vault/logs/audit.log
   ```
2. **Decide and create Headscale user** (S12-R3) — 1 minute. Either:
   ```
   docker exec headscale headscale users create homelab
   ```
   OR edit Day-1 script Task 2 to `--user admin`.
3. **Verify NetBox + Zabbix tokens** (S12-R5) — 2 minutes. Run with working root token:
   ```
   vault kv get secret/netbox/api    # confirm field name 'token' or 'api_token'
   vault kv get secret/zabbix/api    # confirm field 'api_token'
   ```
   If paths don't exist or fields differ, edit Day-1 script accordingly.

**DEFER Task 8 (Restic backup expansion)** until backup chain is fixed (S12-R1). Adding Studio dirs to a backup that doesn't run is paper-only.

**Acknowledge** Headscale is a fresh mesh (S12-R4). Don't expect Tailnet-level fanciness; validate over LAN IP first.

**Optional improvement to script:** add a smoke test in Task 6 that actually invokes a Mini-side LiteLLM route (S12-R9) before declaring done.

### Estimated time

Plan estimates "8 tasks, 30 min each cap = 4 hours max." With pre-Day-1 actions: add ~10 min. With Task 5 model pulls: add 30–90 min depending on LAN bandwidth (50 GB).

Realistic Day-1 completion: 5–6 hours wall-clock, of which ~1 hour is operator attention (gates) and the rest is downloads + verification.

---

## Section 11 — Vault Failures Root Cause Analysis [STRUCTURAL]

Source: `/tmp/audit-section-11-vault-rca.md` — full forensic report (2,700 words, with cited file paths + line numbers + live command output). Synthesis below.

### The reframe that matters most

**Vault has not failed. The operator culture around Vault has failed.** Vault 2.0 has run cleanly since 2026-04-26. Every "Vault incident" was a session where the operator (or an autonomous agent) modified Vault config, deleted a volume, or ran `operator init` against production. The platform does not have a Vault reliability problem; it has a Vault *operability* problem. The fix is missing operator culture (audit, backup, rehearsal, guardrails), not a different secret store.

This reframe inverts the natural reaction ("replace Vault with SOPS"). SOPS would lower the consequences of an incident at the cost of giving up centralized rotation/audit. For a single-operator, ~20-service platform that will move to Linux + Mac Studio compute, the right move is to **keep Vault and add the missing operator culture**.

### Incident timeline (collapsed)

| # | Date | Severity | Root cause | Patched? |
|---|---|---|---|---|
| 0 | 2026-04-26 | Migration | Dev mode = in-memory storage; restart loses state | Yes — dev→server migration; Shamir 5/3; root token saved |
| 1 | 2026-04-28→29 | Sev-2 | Stale auth state post-migration; `/sys/generate-root` permission gates | Yes — manual re-shamir, re-issue tokens, repopulate KV |
| 2a | 2026-04-30 ~13:00–17:00 | Sev-2 | `api_addr` = host LAN IP saturated Docker Desktop's userland-proxy | Yes — one-line fix in two files |
| 2b | 2026-04-30 14:52 | Sev-2 (collateral) | Mis-diagnosed "Vault deadlock"; ran `operator init` on healthy Vault → wiped `secret/` mount | KV rebuilt overnight; **6 paths still listed as missing in CLAUDE.md, all confirmed phantom in this audit** |
| 3 | 2026-04-30 ~17:00–22:00 | Sev-2 | 5-hour autonomous debug window; `docker volume rm` of seal-vault data; Transit auto-unseal broke | Yes — Path A reset; Vault 2.0 dropped `token_file` in seal stanza (undocumented breaking change) |

The user's "3 vault failures" reasonably collapses 2a, 2b, 3 into a single 9-hour 2026-04-30 cascade.

### Cross-incident patterns (P1–P6)

**P1 — All operator/agent-initiated.** Vault has been stable.

**P2 — Missing safety nets at the moment they were needed.** The CLAUDE.md "Outstanding" list still names: audit device disabled, `scripts/backup.sh` log redirect bug, no baseline Restic snapshot. **All three are still open today (2026-05-01).** This is the textbook "documentation as substitute for execution" anti-pattern.

**P3 — Documentation drift inside the same incident.** The KV-loss postmortem listed lost paths using one naming scheme; the rebuild used a different one. CLAUDE.md flags the drift but doesn't reconcile it. The audit confirms all 6 "ambiguously missing" paths are phantom (4 are flat-out wrong path-name predictions — `litellm/db`, `zabbix/web`, `control-plane/backup`, `mcpo/api-key` — no consumer references them; `headscale/oidc-client-secret` is conditional on OIDC being configured; `obot/db` is real but obot uses a literal `POSTGRES_PASSWORD=obot` baked into compose, no Vault sourcing). **The CLAUDE.md outstanding line for these 6 paths can be closed today.**

**P4 — Out-of-repo compose edits not captured.** `~/control-center-stack/stacks/vault/` and `…/seal-vault/` are bind-mounted into runtime but not in git. Every recovery touched them. The rewire log has not kept pace.

**P5 — Tight coupling to a known-fragile substrate.** Three of three incidents were macOS/Docker-Desktop-specific (`disable_mlock=true`, no `IPC_LOCK`, userland-proxy queue saturation, Colima VZ post-restart kernel state breaks Vault listener init). Linux migration would eliminate this entire failure class.

**P6 — Sidecar `Exited (0)` is correct.** The 28 vault-agent sidecars are documented one-shot pattern (`exit_after_auth = true`, with `depends_on: condition: service_completed_successfully`). XF-1 in this audit's preamble was a misread — corrected here. Architectural cost: secret rotation requires explicit sidecar restart + consumer restart, with no in-container renewal. That's a deliberate trade-off, not a bug.

### Systemic root causes (S1–S5)

1. **Vault is correctly chosen but undersupported.** Vault assumes operator culture (pre-change snapshots, audit-on, tested backups, peer-reviewed runbooks). This deployment has Vault without any of that culture.
2. **No test/staging Vault.** Every recovery experiment touches production. Effort to fix: **1 hour** to stand up `vault-test` on its own bridge with separate volumes/Shamir.
3. **Autonomous agents are dangerous near Vault.** The 2026-04-30 5-hour window deleted seal-vault's data volume during a debugging cascade. Recovery handoff doc added rules (no `docker volume rm`, no `colima delete`, 30-min cap) but they live in docs, not in `PreToolUse` hooks.
4. **Backup doctrine without verification is self-deception.** CLAUDE.md says "Restic backups run nightly" and "test restore quarterly." Reality: zero snapshots have ever existed. Cron writes to unwritable log path; failure is silent.
5. **6-month "Linux migration" defers fragility instead of paying it down.** D#32 workarounds in `seal-vault` compose may be vestigial — never re-validated as steady-state-needed.

### Outstanding items confirmed open today

| # | Item | Status |
|---|---|---|
| O1 | Vault audit device | OFF — `vault audit list` returns "No audit devices are enabled." Last `audit.log` write 2026-04-30T13:21Z (~16h ago at audit time) |
| O2 | `scripts/backup.sh` log redirect | Crontab still writes to `/var/log/restic-backup.log` (not writable by admin) |
| O3 | Baseline Restic snapshot | None. Worse: `restic snapshots` returns `s3.getCredentials: no credentials found` — repo is unreachable from operator shell, so we can't even verify whether snapshots exist |
| O4 | Postmortem path reconciliation | All 6 phantom — see P3 above. Can be closed today |
| O5 | `backup` AppRole missing in Vault | Confirmed by data-flow agent — `vault list auth/approle/role` returns 29 roles, `backup` is not one. Root cause of O3. |

### Closed since postmortem

- All 47 enumerated KV leaf paths populated (vault-RCA agent verified by root-token enumeration across 16 parents)
- All 29 service AppRoles re-issued, sidecars rendering credentials.env successfully
- Transit auto-unseal verified across two restart cycles
- vault-server `command:` wrapper reads `VAULT_TOKEN` from mounted file (working around Vault 2.0 dropping `token_file` in seal stanza)

### Five things this week regardless of any other audit recommendation

Ranked by ratio of (incident-prevention value) / (operator effort). Total: under 6 operator-hours.

1. **Fix `scripts/backup.sh` and witness one verified Restic snapshot land.** Until this exists, every other fix is decorative. Without it, the next KV-touching incident is unrecoverable. Steps: (a) move log redirect inside script (`exec >> "$LOGFILE" 2>&1` after `mkdir -p`), default `LOGFILE=$HOME/Library/Logs/restic-backup.log`; (b) replace silent `restic init` fallback with `restic snapshots || { echo FATAL; exit 2; }`; (c) re-provision the missing `backup` AppRole; (d) initialize repo manually; (e) run script interactively and verify snapshot lands; (f) add Zabbix item that fails if `restic snapshots --no-lock | tail -1` is older than 30h. **~2h.**
2. **Re-enable Vault audit device.** `docker exec vault-server vault audit enable file file_path=/vault/logs/audit.log`. **~10 min.**
3. **`PreToolUse` hooks blocking `docker volume rm`, `colima delete`, `vault operator init`, `vault operator unseal`** without per-action approval. The 2026-04-30 5-hour window proves docs alone are insufficient. Use the `update-config` skill. **~2h.**
4. **Stand up `vault-test` on a separate bridge.** Removes "production is the only place to learn." This single change would have prevented the 2026-04-30 14:52 wipe. **~1h.**
5. **Reconcile postmortem outstanding-path list with reality** (per P3 above) and update CLAUDE.md. Closes a documentation-drift item that would otherwise mislead the next session. **~30 min.**

---

## Section 1 — Service Inventory [VERIFIED]

Source: `/tmp/audit-sections-1-3-inventory.md` — full inventory matrix (3,300 words, 63 containers + 28 sidecars classified). Headlines below; cite the source for the full per-container table.

### Headline

63 running containers resolve to **~32 application services + 28 vault-agent sidecars + 3 special-lifecycle MCP**. Caddy advertises 29 routes against ~26 unique `*.internal` upstreams. Three application containers run from SHA-pinned digests with no semantic tag (`mkdocs`, `structurizr`, `openhands-app` — XF-4 in preamble); a dozen run rolling/`latest` tags. The 28 vault-agent sidecars in `Exited (0)` state are operating as designed (XF-1 corrected here — see Section 11 P6).

### Layer breakdown

| Layer | Count | Examples |
|---|---|---|
| Control plane (CP) | 8 | caddy, homepage, homarr, ai-platform-dashboard, mkdocs, structurizr, topology-api, docker-socket-proxy-control |
| Observability (OBS) | 12 | vm, vmagent, grafana-obs, loki, promtail, uptime-kuma, cadvisor, node-exporter, zabbix × 5 |
| Secrets (SEC) | 3 + 28 sidecars | vault-server, seal-vault, vaultwarden + all `vault-agent-*` |
| LLM | 5 | litellm-gateway, open-webui, anythingllm, openhands-app, obot |
| MCP | 7 | mcp-{filesystem, docker, docs}-remote, plex-mcp, mcpo-proxy, sms1obot × 2 |
| Platform (PLT) | 18 | plane × 7, netbox × 6, inventree × 4, nextcloud × 2, homeassistant |
| Network (NET) | 1 | headscale |
| Media (MED) | 4 | prowlarr, sonarr, radarr, sportarr (Plex itself runs on QNAP) |
| Misc | 2 | upgrade-receiver, upgrade-watcher (Diun) |

### Image hygiene anomalies

- **SHA-only (no tag):** mkdocs, structurizr, openhands-app, upgrade-receiver. Reproducibility risk if Docker prunes the image and the build context is gone.
- **Rolling/`latest` tags:** vault-server, vaultwarden, cadvisor, headscale, obot, anythingllm, litellm-gateway (`:main-latest`), open-webui (`:main`), homarr, docker-socket-proxy-control, homeassistant (`:stable`), upgrade-watcher, mcp-docs-remote (`:latest`), zabbix-postgres (`timescale:latest-pg16`). Recommend pinning to digest or semver during Phase 15 hardening.

### Stopped containers worth noting (XF-3 follow-up)

- `control-plane` (Exited 0, 16h ago): per ARCHITECTURE.md, the platform's roadmap-execution control-plane container. Confirmed by inventory agent as "Phase 15 cleanup target" — intentional, not abandoned.
- `catt-controller` (Exited 0, 16h ago): Catt (cast-all-the-things) deferred — also intentional.
- `docker-plane-migrate-1`, `docker-plane-minio-setup-1` (Exited 0, 2d ago): one-shot setup containers — correct.

XF-3 downgrades from MEDIUM to INFO.

---

## Section 2 — ADR Validation [VERIFIED]

Source: `/tmp/audit-sections-2-4-6-foundations.md` Section 2 — full ADR-by-ADR table. Headlines:

### Most ADRs FULLY-IMPLEMENTED. Two with material drift:

**ADR-A-014 (NetBox CMDB authority) — MAJOR DRIFT.** CLAUDE.md claims `CMDB_SOURCE` default is `netbox` as of Phase 14 D-DOC. **Only true for one consumer (`scripts/cmdb_source.py`).** Three other consumers still default to `yaml`:
- `scripts/validate-cmdb.sh:24` defaults to `yaml`
- `docker/topology-api/server.py:39` defaults to `yaml`
- `docker/topology-api/docker-compose.yml:18` sets `CMDB_SOURCE: "${CMDB_SOURCE:-yaml}"`
- `docker/control-plane/app/modules/registry.py:69` defaults to `yaml`
- **Live `topology-api` container is reading `service-registry.yaml.DEPRECATED`** (verified by `docker exec topology-api env`)

**ADR-A-015 (staged-toggle migration) — same drift.** Step 4 ("flip the default") only landed in one of four CMDB consumers.

**Fix path:** flip the four remaining defaults; redeploy topology-api with `CMDB_SOURCE=netbox`; remove `.DEPRECATED` mount. The `.DEPRECATED` file remains as A-012 deprecation-gate fallback.

### ADRs with stale text

**ADR-A-004 (Local Ollama 6-model fleet).** Cloud-fallback wording contradicts current LLM Access Doctrine (Phase 13.5 deleted `secret/anthropic/api`, removed `claude-sonnet/haiku/gpt-4o` routes). Hardware spec says "M4 Pro 64 GB" — actual is 48 GB per CLAUDE.md correction 2026-05-01. **Action:** rev to A-004.1 or supersede.

**ADR-A-007 (Syncthing media sync) — governance violation.** Currently dirty in working tree (`git diff` shows credential rotation post-2026-04-28 reinstall + new "Operational lessons (Phase 15, 2026-05-01)" section). Content is appropriate — it documents real Syncthing operational reality. But **ADR README says "ADRs are immutable once Accepted (create a new ADR to supersede)"** — modifying in-place violates that rule. **Action:** either (a) revert and file A-018 ("Syncthing operational lessons"), or (b) amend the README to allow clearly-demarcated "Operational lessons" appendices on existing ADRs. Recommend (b) — operational truth needs to live next to the original decision.

**ADR-A-009 (Vault as authoritative secret store).** Text still names `docker/nextcloud/.env`, `docker/vaultwarden/.env`, `docker/zabbix/.env` as plaintext-credential holdouts. CLAUDE.md §6 says "all 16 covered." Drift in either direction — text needs an update.

**ADR-A-016 (canonical patterns registry).** Registry has 1 entry. `vault-agent` canonical pattern lives at `config/vault-agent-canonical-pattern/` instead of `docs/canonical-patterns/vault-agent.md` per ADR. Move it.

---

## Section 3 — Redundancy + Conflict Analysis [VERIFIED]

Source: `/tmp/audit-sections-1-3-inventory.md` Section 3. Headlines:

### Three categories show real overlap; the rest are justified

**KEEP-ALL — monitoring stack.** Zabbix and VictoriaMetrics are complementary, not redundant: VM cannot do SNMP; Zabbix cannot scale Caddy/cAdvisor metric series cheaply. Uptime Kuma is a third axis (synthetic probes with operator UI). The CLAUDE.md "Known Hardening Trade-offs" section is consistent with this. **No consolidation needed.**

**CONSOLIDATE — dashboard layer.** Six surfaces: homepage, homarr, ai-platform-dashboard, grafana-obs, mkdocs, structurizr. Only **homepage ↔ homarr is true duplication** (both Docker-socket-driven tile dashboards, no documented role split). The other four are non-overlapping niches. **Recommend retiring homarr.**

Bonus removal: **`docker-socket-proxy-control`** is up but unreferenced — both dashboards bind-mount the socket directly. Dead infrastructure.

**CONSOLIDATE — end-user LLM chat UI.** Open WebUI vs AnythingLLM are both chat UIs over Ollama. Open WebUI is the documented primary (ARCHITECTURE.md), integrates with mcpo-proxy + litellm. **AnythingLLM has no compose file in the standard inventory and no documented integration.** Strong removal candidate (after operator confirms).

**KEEP-BOTH — Obot vs OpenHands.** Different user journeys (MCP routing/RBAC gateway vs autonomous coding agent web UI).

**KEEP-BOTH — mcpo-proxy vs mcp-filesystem-remote.** Different protocols (OpenAPI vs streamable HTTP), different consumers (Open WebUI vs Obot).

**KEEP-ALL — secret management (clean separation).** Vault = infra; Vaultwarden = end-user passwords; no overlap.

**KEEP-ALL — databases (5 Postgres at 3 versions).** Per-app isolation is correct; the version split (15/16/17) reflects vendor constraints, not sprawl. Redis vs Valkey split is incidental and harmless (NetBox upstream switched to valkey in 4.x).

**LLM Access Doctrine — VERIFIED INTACT.** `litellm_config.yaml` has zero cloud routes. Open WebUI and OpenHands both target local Ollama. Phase 13.5 cleanup is real, not paper.

### Top 5 removal candidates

1. **homarr** — duplicates homepage; no unique role. Removes one direct-Docker-socket mount.
2. **docker-socket-proxy-control** — provisioned but unreferenced.
3. **sportarr** — niche (port 1867); not in Caddy routes; not in ai-platform-dashboard env vars. Confirm with operator.
4. **upgrade-receiver + upgrade-watcher pair** — Diun + bespoke `pip install requests on every restart` python:3.12-slim runtime. If user doesn't subscribe to image-update notifications, pair is overhead.
5. **homeassistant (containerized)** — Caddy proxies `homeassistant.internal` to the **physical hub at .141**, NOT the local container. The Mac-Mini-resident container has no traffic routed to it. Worth asking what it's for.

### Top 3 "what is this for?" services (need user input)

1. **anythingllm** — what does it do that Open WebUI doesn't?
2. **homeassistant container** — see #5 above
3. **sportarr** — actively used?

---

## Section 4 — Configuration Consistency [VERIFIED]

Source: `/tmp/audit-sections-2-4-6-foundations.md` Section 4. Headlines:

### Excellent adherence to security baseline. Drift in resource/logging baseline.

**`cap_drop:[ALL]` adherence: excellent.** All 5 sampled compose files have it. Documented exceptions (mcp-docker-remote, sms1obot-* shims, seal-vault per D#32, linuxserver/* arr containers needing 4 caps for s6-overlay) are correctly carved out.

**`security_opt:[no-new-privileges:true]`: universal across sampled files.**

**`read_only: true`: rare** — 1 hit across all stacks (`stacks/catt/docker-compose.yml:28`). CLAUDE.md says "where image supports" — many don't, but this is a low-coverage area worth a sweep for stateless services.

**`mem_limit`: under-applied** — 2 of ~25 sampled services. Postgres, Redis, NetBox, Plane API, Open WebUI all run unconstrained. Postgres especially needs limits because shared_buffers headroom matters.

**`logging:` driver: never declared** — relying on Docker daemon defaults. No per-service rotation policy at compose level.

### Caddyfile — strong

- 100% adherence to `(access_log)` snippet (29 of 29 sites). VERIFIED matches CLAUDE.md D-LOG claim.
- Pruned routes from commit 3db56c7 (2026-04-29) verified — `manyfold.internal`, `gitea.internal` correctly return TLS internal error.
- 2 hardcoded IPs: `homeassistant.internal → 192.168.10.141:8123` (documented exception, HA on different host) and Caddy admin `0.0.0.0:2019` (security finding, see Section 6).
- Mix of `host.docker.internal:port` (24 sites, legacy mac Docker Desktop pattern) vs Docker DNS service names (5 newer Phase 14 sites). Standardize on Docker DNS where both endpoints share a network.

### Vault-Agent templates — consistent

All 5 sampled `vault-agent.hcl` files are **byte-identical** including `exit_after_auth = true` (XF-1 confirmed intentional). Credential templates follow `secret/data/<service>/<class>` consistently.

**One latent risk:** Plane DSN templates render passwords directly into URLs (`postgresql://plane:{{ .Data.data.password }}@plane-db/plane`) with no URL-escaping. CLAUDE.md anti-pattern: "URL-embedded credentials using non-URL-safe characters." If the Vault-stored password contains `/+=`, Plane will fail to parse the DSN. **Mitigation:** require all secrets used in DSN templates to be hex-only (or URL-safe). No tooling enforces this today.

### Top 5 config drift items

1. **CMDB_SOURCE default not flipped in 3 of 4 consumers** (see ADR-A-014).
2. **`mem_limit` set on only 2 of ~25 sampled services.**
3. **`logging:` driver/rotation not declared in any compose file.**
4. **`read_only: true` set on only 1 of 25+ services.**
5. **Caddyfile mixes `host.docker.internal:port` (24 sites) with Docker DNS service names (5 sites).**

---

## Section 5 — Data Flow Validation [VERIFIED LIVE]

Source: `/tmp/audit-sections-5-7-8-flows.md` Section 5. Headlines:

### Vault → service credential flow: WORKING AS DESIGNED, with two unalerted failure modes

Verified live for nextcloud, litellm-gateway, inventree: AppRole logins succeed; `credentials.env` files exist (133 B, 87 B, 396 B) with mode `0444`; consumers source them via entrypoint `set -a && . /vault/secrets/credentials.env`.

**Architectural properties operators must know:**
- Files persist after sidecar exit. Containers re-source on restart.
- **No active renewal.** If anyone adds a leased value to a template, it will silently expire. None of the sample templates produce leased credentials today, but there is no compile-time guard.
- **No rotation pickup.** KV value rotation is invisible until sidecar re-runs.
- **Sidecar status not monitored.** `Exited (0)` indistinguishable from `Exited (1)` to anything not reading exit codes.

### Media pipeline: works, but seedbox half is fragile

- Plex Media Server runs on **QNAP**, not Mac Mini. Sonarr/Radarr write to `/Users/admin/mnt/qnap-downloads` (SMB mount, 23 TB, 37% used).
- Sync mechanism is Syncthing (per A-007 just-updated). **Seedbox-side Syncthing has no process supervisor** — only `~/bin/syncthing` with `@reboot` cron entry. If it dies mid-session, transfers stop silently.
- 2026-04-28 incident: seedbox provider's `resilio-sync` systemd unit started by hosting provider, bound port 26401, blocked Syncthing. Syncthing failed silently (no log written). **No alert exists if rslsync ever returns.**

### Metrics flow: 4 of 63 containers scraped (~6% coverage)

Configured scrape jobs: node-exporter, caddy, mcp-docs (currently DOWN), cadvisor, zabbix-exporter, vmagent self. **No application metrics for nextcloud, inventree, netbox, plane, vault, loki, vm itself, openhands, obot, open-webui, anythingllm, headscale, vaultwarden, homeassistant.**

### Logs flow: caddy-only

`promtail-config.yaml` has 2 scrape jobs: `system` (the promtail container's `/var/log/*log`, near-empty) and `caddy-access` (the actual log shipping). Confirmed via `curl /loki/api/v1/label/job/values` → `["caddy"]`.

**Postmortem evidence on the 2026-04-30 KV mount loss had to come from `docker logs vault-server` (volatile) and the Vault audit log (currently disabled).** This is a regression risk: the next incident will have even less forensic data.

### Plane → executor: NOT WIRED (design intent only)

`find ~/repos -name "*.py" | xargs grep -l "plane.*webhook\|plane.*executor"` returns no results. The `iap-trigger-watcher.sh` allow-list is `backup`, `regression-probe`, `credential-rotate` — **no Plane consumer**. Last trigger-watcher log entry: `2026-04-29 02:05 — DONE regression-probe` (one execution in two days). All Plane → execution today is human-in-the-loop with Claude Code reading Plane via MCP.

This is an important gap to surface for Section 13 (autonomy) — the platform is not actually autonomous, regardless of architectural framing.

### Top 5 broken/incomplete data flows

1. **Restic backup → Vault AppRole auth → S3** — broken end-to-end (see Section 8).
2. **Plane → executor** — design intent, not wired.
3. **Service logs → Loki** — 1 of 63 services shipped.
4. **Service /metrics → vmagent** — 4 of 63 containers in scrape inventory.
5. **Seedbox-side media sync** — no supervisor, no monitoring.

---

## Section 6 — Security Posture [VERIFIED]

Source: `/tmp/audit-sections-2-4-6-foundations.md` Section 6. Headlines:

### Top 5 security risks (ranked by impact)

1. **[CRITICAL] Vault audit device DISABLED for ~20+ hours.** All KV reads/writes since 2026-04-30 KV-loss recovery are not being recorded. Breaks ADR-A-005 ("Audit log enabled; every operation in `/vault/logs/audit.log`"). Defeats the operator's ability to forensically reconstruct the next incident. **Single most consequential outstanding item.** Fix: `docker exec vault-server vault audit enable file file_path=/vault/logs/audit.log`.

2. **[HIGH] Multiple high-value services bind `0.0.0.0` directly to LAN, bypassing Caddy.** Vault `:8200`, Vaultwarden `:8083`, Headscale `:50443`/`:8082`, MinIO `:9000-9001`, Plane API `:8000` are LAN-reachable independent of Caddy's `*.internal` routes. ADR-A-005 implies Caddy is the sole user-facing entry; implementation does not match. Fix: rebind duplicates to `127.0.0.1` OR amend ADR-A-005 to acknowledge dual-path posture and rely on OPNsense for LAN-perimeter enforcement.

3. **[HIGH] Possibly-real Plane API token in `stacks/gateways/.env.example:5`.** `PLANE_API_TOKEN=plane_api_f6c2c3cc049d4fedb24b0f62acbfc00b` looks live, not placeholder. `.env.example` files are committed. Even if rotated, the value should not be in repo. Fix: rotate in Plane and replace with `PLACEHOLDER`.

4. **[HIGH] Caddy admin endpoint exposed on `0.0.0.0:2019` with no authentication.** Anyone on LAN with the Caddy admin API can reload routes and arbitrarily proxy traffic. Fix: rebind to `127.0.0.1:2019` (or docker-network only); update healthcheck to use in-container loopback.

5. **[MEDIUM] `autounseal-token` host file mode** — agent reported `0644` world-readable; my live check showed `0600` (`-rw-------`). Possible the agent saw a different file (`stacks/vault/autounseal-token` vs `~/vault-server-autounseal-token-20260430.json`) — both should be `0600`. Worth a sweep: `find ~ -name "*autounseal*" -exec ls -la {} \;`.

6. **[INFO] Stale `~/vault-init-keys.txt` root token (XF-5).** Pre-recovery file lists a token rejected by current cluster. Operators or agents reading this file will get a token that fails. Rename to `*-PRE-KV-LOSS-INVALID.txt`; add fresh file pointing at current root token + recovery shamir keys.

### Anti-pattern scan: clean

- No `--no-deps` with sidecar pattern
- No `sh -c` without `exec`
- `bin/oss_wave_*` launchers still present (NOT FULLY VERIFIED whether functional). Worth a confirmation.

### Vault policies: least-privilege

5 sampled (grafana-obs, plane-api, control-plane, headscale, obot) — all `read`-only or list. `control-plane-policy.hcl` is exemplary with explicit `deny` on `sys/policies/acl/*` and `auth/approle/role/*`. Best policy in set.

### TLS: all Caddy routes use TLS (local CA). Vault listener uses plain HTTP on Docker network (acceptable per ADR-A-005).

---

## Section 7 — Observability Coverage [CRITICAL FINDINGS]

Source: `/tmp/audit-sections-5-7-8-flows.md` Section 7. Headlines:

### Coverage matrix headline numbers

- **App metrics scrape coverage: 4 of 63 containers (~6%).**
- **Loki log shipping: 1 service (caddy access log only).**
- **Healthcheck definition: 46 of 63 containers (~73%).**
- **Uptime Kuma: 12 monitors total — 11 reporting DOWN.**

### [CRITICAL] Uptime Kuma is silently broken

All 11 HTTP monitors targeting `mac-mini.internal` URLs report DOWN with `getaddrinfo ENOTFOUND mac-mini.internal`. The hostname is unresolvable from inside the Kuma container's DNS namespace. **Every target service is actually UP per `docker ps` and direct host probes.** The one UP monitor (Home Assistant .141) uses a literal IP.

Kuma has been showing all-red indefinitely. There's no alerting wired off Kuma so no one was paged, but the dashboard is unusable for actual outage detection. **Fix:** add `mac-mini.internal` to Kuma's `/etc/hosts` (via extra_hosts in compose) or change all monitors to use container DNS service names / literal IPs.

### [CRITICAL] Zero production alerts exist

| Scenario | Alert exists? |
|---|---|
| Vault sealed | NO |
| Disk >85% full | NO (data is in VM but no rule references it) |
| Container restart loop | NO (cAdvisor labels broken on Docker Desktop — see CLAUDE.md "cAdvisor friendly-name labels missing") |
| Backup job failed | NO |
| TLS cert expiring <14d | NO |

**vmalert is not deployed.** No Grafana unified-alerting rules. Zabbix has 2 active triggers — both stale "Zabbix agent not available" for self-template hosts (orphaned templates, not meaningful alerts).

The 2026-04-30 KV mount loss (Sev-2) is exactly the kind of incident that would have been caught by a 2-line vmalert rule on `vault_core_unsealed{} == 0` if Vault telemetry were scraped.

### Top 5 observability gaps that would have caught past incidents

1. **No `vault_core_unsealed == 0` alert.** Two of three recent Vault failures involved Vault going sealed/unreachable.
2. **No `up == 0` alert across vmagent targets.** mcp-docs has been DOWN for unknown duration.
3. **No alert on vault-agent sidecar non-zero exit.** Past silent-credential-failure incidents would not have been caught.
4. **Uptime Kuma silently broken** (above).
5. **No backup-success heartbeat metric.** Backups silently failing for ~2 days. A 1-line `backup_last_success_timestamp` emit + 36h-stale alert would have surfaced this.

---

## Section 8 — Backup + DR Validation [CRITICAL]

Source: `/tmp/audit-sections-5-7-8-flows.md` Section 8. Headlines:

### Backup chain is broken end-to-end

**The `backup` AppRole does not exist in Vault.** Verified live: `vault list auth/approle/role` returns 29 roles, `backup` is not one. Cause: lost in 2026-04-30 KV mount loss; no `provision-backup.sh` script ever re-ran (every other AppRole has one; `backup` is the only AppRole that needs separate manual provisioning since it's not provisioned alongside a service compose).

**Cron has been running nightly at 02:00 for ~2 days post-rebuild.** Each run fails immediately at AppRole login, logs nothing because `/var/log/restic-backup.log` is not writable by `admin` (the §8.1 redirect bug), and produces no Restic snapshot. **Snapshot inventory: zero.**

This is **the highest-priority finding in the entire audit**. Until fixed, every other recommendation is decorative.

### What SHOULD be backed up that isn't

`BACKUP_DIRS` lists files that are mostly **already in git** (`config/`, `docs/`, `scripts/`, etc.). **Not in any backup:**

- `~/.vault-approle/` (29 service AppRole credentials) — bootstrap deadlock if lost
- `~/control-center-stack/` — canonical out-of-repo compose definitions for 8 stacks (per CLAUDE.md, this is exactly the data you can't regenerate from git)
- All stateful Docker volumes: nextcloud-data, inventree-postgres-data, netbox-postgres-data, docker_plane-db-data (601-item roadmap), vaultwarden-data, zabbix-pgdata, obot-data, loki_loki-data
- `~/vault-init-keys*.txt` (Shamir + root token) — should be in offline storage too

### Restore runbook: never tested end-to-end

`docs/runbooks/vault-restore-from-backup.md` (189 lines, Phase 14 D-DOC):
- Step 2 assumes the `backup` AppRole works. It doesn't.
- Step 4 references volume name `vault-server-data`; actual volume is `vault_vault-data` (`docker volume ls`).
- No step to re-enable audit device after restore.
- 2026-04-30 KV loss was recovered by *re-provisioning* (running `provision-*.sh` for all services), not by *restoring* from Restic snapshot. **The runbook has never been exercised end-to-end.**

### RTO/RPO

| Scenario | RTO | RPO |
|---|---|---|
| Mac Mini hardware dies | **Multi-day** (Colima/Docker rebuild + clone repo + reconstruct `~/control-center-stack/` from commit history + Vault re-init from Shamir if stored offline + re-provision 29 AppRoles + re-populate KV from canonical recovery sources + restore stateful volumes from… nowhere) | **Infinite for everything except files in git** |
| Single Docker volume corruption | **Infinite** (no volume backup) | **Infinite** |
| Vault data corruption (rehearsed 2026-04-30) | Hours (rebuild from `provision-*.sh`) | Any KV value not pre-known to a provisioning script is lost |

### Top 3 backup gaps that risk unrecoverable data loss

1. **Backups aren't running** — the most critical finding in the audit.
2. **`~/control-center-stack/` and all stateful Docker volumes not on backup list** even when backups resume.
3. **Restore runbook references wrong volume name and has never been tested.**

---

## Section 9 — Documentation Completeness

**Method:** enumerated `docs/` tree (4 root entry-point docs claimed by CLAUDE.md, 18 runbooks, 17 ADRs, 1 troubleshooting decision-tree + 1 issue-pattern doc + 5 known-issues files, 54 phase-13 docs, 11 phase-14 docs, 9 phase-15 docs). Cross-checked CLAUDE.md's documentation pointers against actual file presence. Spot-read recent docs for date currency vs. operational reality.

### S9-F1 (BLOCKER): CLAUDE.md "Quick Start" points to three documents that do not exist

CLAUDE.md tells every new Claude session:
> 1. **Read the docs first:** All context is in `docs/ARCHITECTURE.md`
> 2. `docs/DEPLOYMENT_GUIDE.md` — How to operate services
> 3. `docs/TROUBLESHOOTING.md` — Issue resolution
> 4. `docs/HANDOFF_GUIDE.md` — Session continuity instructions

Verified: `docs/ARCHITECTURE.md` exists. `docs/DEPLOYMENT_GUIDE.md`, `docs/TROUBLESHOOTING.md`, and `docs/HANDOFF_GUIDE.md` **do not exist** (and grep across `docs/` finds no file with those names anywhere). CLAUDE.md repeats the broken pointers in the "Critical Behavioral Rules" section ("How do I deploy X" → DEPLOYMENT_GUIDE; "Service not working" → TROUBLESHOOTING) and again in the "Project Structure" listing.

This is the single most damaging documentation defect in the repo. Every fresh Claude session is instructed by CLAUDE.md to begin by reading docs that don't exist. The closest substitutes:
- `docs/troubleshooting/common-issues.md` and `docs/troubleshooting/DECISION_TREE.md` for "Service not working" (both exist, both useful, neither linked from CLAUDE.md)
- No equivalent for "How do I deploy X" — operational deployment lives implicitly in the runbooks (`add-new-service.md`, `restart-services.md`) plus out-of-repo `~/control-center-stack/stacks/*` compose files
- No equivalent for "session continuity" — `docs/PHASE_LOG.md` and `docs/PHASE_ROADMAP.md` are the closest, but neither claims that role

**Fix:** either create the three documents, or amend CLAUDE.md to point to what actually exists. The latter is faster (~30 minutes) and lower-risk; rolling new "guide" docs invites stale duplication. Recommend: replace the three pointers with `docs/troubleshooting/`, `docs/runbooks/restart-services.md` + `docs/runbooks/add-new-service.md`, and `docs/PHASE_ROADMAP.md` + `docs/phase-NN/PHASE_NN_EXECUTION_HANDOFF_*.md` respectively.

### S9-F2 (MAJOR): Critical operational runbooks missing

Audited the runbook collection against the failure modes surfaced in Sections 6, 8, and 11. Present (18 runbooks): vault-unseal, vault-rekey, vault-token-rotation, vault-recovery-from-shamir, vault-restore-from-backup, rotate-credentials, restart-services, add-new-service, add-new-host, add-new-mcp-server, regression-probe-failure, drift-detection-procedure, incident-response, operating-model, plane-web-auth, migrate-source-of-truth, what-changed-last-24h, H1-rollback. Missing — each tied to a real, recurring or imminent failure mode:

| Missing runbook | Failure mode it covers | Evidence it's needed |
|---|---|---|
| `vault-audit-enable.md` | Re-enable audit device after maintenance/recovery | Audit device disabled since 2026-04-30; CLAUDE.md outstanding item; `vault-restore-from-backup.md` Step 8 says "Confirm audit log alive" but never says how to *enable* it if missing |
| `backup-failure-recovery.md` | Restic backup chain broken (Section 8) | Backups have been silently failing; nothing tells the operator how to diagnose `scripts/backup.sh` failures, fix the log redirect, take baseline snapshot |
| `mac-studio-day1.md` | Mac Studio physical integration | Day-1 work currently lives in two ad-hoc files at `~/mac-studio-day1-{checklist,execute}.{md,sh}` outside the repo — not version-controlled, not findable by future sessions |
| `mcp-server-recovery.md` | MCP server failure (Section 7 monitoring gap) | `docs/troubleshooting/common-issues.md` covers symptom-level only; no systematic recovery procedure for the 7-server fleet (filesystem, docker, docs, plex, mcpo-proxy, sms1obot pair) |
| `cmdb-source-rollback.md` | Roll back from `CMDB_SOURCE=netbox` to YAML | ADR-A-014 doctrine is netbox-default but YAML retained as deprecation-gate fallback (per A-012); no procedure for the rollback itself |
| `certificate-renewal.md` | Caddy local-CA rotation, internal cert rollover | Certs are auto-managed by Caddy today, but no doc explains what happens at rotation or how to rebuild the trust store |
| `syncthing-rebuild.md` | Syncthing reconfiguration after credential rotation | ADR-A-007 unsanctioned amendment shows credentials were rotated 2026-04-28 with no procedural reference; future operator has no rebuild path |

The pattern: every recent Sev-2 incident produced an *incident document* (`PHASE_15_VAULT_*`, `POST_H1_BACKUP_REPAIR`) but did not produce a *runbook*. Postmortems describe what happened; runbooks describe what to do next time. Phase 15 has 6 incident docs and 0 new runbooks.

### S9-F3 (MAJOR): ADR governance broken — three distinct violations

The ADR README (line 46) declares: **"ADRs are immutable once Accepted (create a new ADR to supersede)."**

**Violation 1 — silent in-place edit:** `docs/adr/ADR-A-007-media-sync-syncthing.md` is currently dirty in the working tree (per `git status` at session start). The pending edit adds operational lessons learned and rotated-credentials notes from a 2026-04-28 reinstall. ADR-A-007's status field reads "Accepted (2026-04-27)" — by the README rule, this should be a new ADR (e.g., ADR-A-017 amending A-007), not an in-place edit. The fact that it is uncommitted means there is still time to do this correctly.

**Violation 2 — ADR README index is stale:** the index table in `docs/adr/README.md` lists ADRs A-001 through A-013. The directory contains A-001 through A-016. Three ADRs (A-014 NetBox CMDB authority, A-015 staged toggle migration, A-016 canonical patterns registry) exist but are not in the index. A-014 is one of the most consequential ADRs in the repo (defines source-of-truth for service inventory) — its absence from the index makes it discoverable only by `ls`.

**Violation 3 — no ADR-A-NNN naming consistency:** A-001 through A-006, A-008, and A-009 use bare names (`ADR-A-001.md`); A-007, A-010 onward use slug-suffixed names (`ADR-A-014-netbox-cmdb-authority.md`). The README template doesn't specify which is required. Cross-references in other docs (e.g., `ADR-A-011-ivv-loop-pattern.md` referenced in operating-model.md line 5) assume slug suffixes — links to bare-name ADRs from external docs are fragile if anyone renames.

### S9-F4 (MAJOR): Documentation conflict — multiple "canonical" overview docs

`docs/PLATFORM_OVERVIEW.md` (297 lines, mtime 2026-04-29) and `docs/ARCHITECTURE.md` (262 lines, mtime 2026-04-29) both exist. CLAUDE.md says: *"`docs/ARCHITECTURE.md` — start here (supersedes PLATFORM_OVERVIEW.md)"*. The supersession is correct in the directive but is **not marked in PLATFORM_OVERVIEW.md itself** — there is no banner, no DEPRECATED header, no redirect. A new reader who lands on PLATFORM_OVERVIEW.md (which is alphabetically earlier in `ls` and historically the canonical name) has no signal it has been replaced.

Same pattern with phase summary docs:
- `docs/phases/phase-1-10-summary.md` (consolidated)
- `docs/phases/phase-11-complete.md` (per-phase)
- `docs/phase-13/PHASE_13_INVENTORY_2026-04-28.md`, `PHASE_13_BLOCK_*_RESULTS_*.md` (54 files)
- `docs/PHASE_LOG.md` (79 lines, mtime 2026-04-27 — predates Phase 14 closeout and all of Phase 15)
- `docs/PHASE_ROADMAP.md` (277 lines, mtime 2026-04-30 — current)

`PHASE_LOG.md` is **3 days stale** vs current state. It does not reflect Phase 14 closure, Phase 15 KV loss, or Phase 15 vault recovery work. Anyone using it as a "what's done" reference will be misled.

### S9-F5 (MINOR): Phase document naming convention only partially enforced

CLAUDE.md mandates: `docs/phase-NN/PHASE_NN_<TYPE>_<YYYY-MM-DD>.md`. Audit:

- **phase-15/** (9 files): 8 conform, 1 deviates (`seal-vault-compose-BROKEN-2026-04-30.yml` — a YAML artifact, arguably not a "phase document")
- **phase-14/** (11 files): conforms, with 5 `.log` files for regression baselines (allowed by spirit of the rule)
- **phase-13/** (54 files): mostly conforms — but mixed `INCREMENT_*`, `PHASE_13_BLOCK_*`, `PRE_BLOCK_*`, `POST_BLOCK_*`, `STATE_*` prefixes. The `PHASE_NN_<TYPE>` formal pattern is the minority.

This isn't a high-severity finding (the docs are all findable by `ls docs/phase-13/`), but the convention as written in CLAUDE.md does not reflect what the directory actually contains. Either tighten enforcement going forward or amend CLAUDE.md to acknowledge the broader naming patterns observed.

### S9-F6 (MINOR): Known-issues registry under-utilized

`docs/known-issues/` contains 5 files (KI-001 through KI-004 plus KI-RETIRED-rclone-sftp). Compare against this audit's findings: backup chain broken, audit device disabled, Uptime Kuma 11/12 monitors down, vmalert not deployed, ADR-A-014 drift, 6 phantom Vault postmortem paths, mac-mini.internal DNS resolution failure inside containers — *none of these have KI entries*. The registry is treated as an archive of past pains rather than a living catalog of currently-known limitations.

The "Known Hardening Trade-offs" section in CLAUDE.md (ICMP/fping monitoring, cAdvisor friendly-name labels, etc.) is a richer current-state catalog than `docs/known-issues/`. Either consolidate (CLAUDE.md is the registry; retire `docs/known-issues/`) or backfill (each Known Hardening Trade-off becomes a KI file).

### S9-F7 (MINOR): No "as-built" architecture diagram

`docs/architecture/dependency-graph.md` and `docs/architecture/mcp-server-architecture.md` exist (small, 3 files total in `docs/architecture/`). Spot-read: text-based diagrams, last touched mid-Phase 13. The audit's Section 1 inventory is now the most current "what is actually deployed" reference. No image, no Mermaid, no auto-generated topology from NetBox — despite NetBox being the authoritative service registry per ADR-A-014. This is a missed integration: NetBox could be the source for a generated architecture diagram, removing the staleness problem.

### S9 — recommended documentation actions, prioritized

**Same-week:**
1. **Fix CLAUDE.md broken doc pointers (S9-F1)** — ~30 min, removes the single most misleading instruction in the repo
2. **Update `docs/PHASE_LOG.md`** to reflect Phase 14 closure + Phase 15 work — ~20 min, restores its claim to currency
3. **Add ADR-A-014/15/16 to the ADR README index (S9-F3 violation 2)** — ~5 min
4. **Resolve the dirty ADR-A-007 working-tree edit (S9-F3 violation 1)** — either commit as a new ADR-A-017 amending A-007, or revert and write a separate operational notes doc

**Within Phase 16:**
5. Author the missing critical runbooks (S9-F2): `vault-audit-enable.md`, `backup-failure-recovery.md`, `mac-studio-day1.md` first (these three close real outstanding incident gaps); the rest as time permits
6. Add a DEPRECATED banner to `docs/PLATFORM_OVERVIEW.md` pointing to ARCHITECTURE.md (S9-F4) — or delete it outright if ARCHITECTURE.md is fully complete
7. Reconcile known-issues registry with CLAUDE.md "Known Hardening Trade-offs" (S9-F6) — pick one canonical location

**Phase 17+:**
8. Generate as-built architecture diagram from NetBox CMDB (S9-F7)
9. Consider documentation linting (e.g., `mkdocs-link-check` or similar) in CI to prevent broken-doc-pointer regressions

---

## Section 10 — Tool Fitness and Alternatives

**Method:** for each major tool family in the stack, asked: (a) what job is it doing? (b) is it the right shape for that job? (c) what would the platform look like without it? (d) what's the next-most-likely tool we'd pick if starting clean today? Findings are recommendations, not directives.

### 10.1 Stack-defining tools — keep, with caveats

| Tool | Job | Verdict | Note |
|---|---|---|---|
| **HashiCorp Vault** | Secret store, dynamic creds, audit | **Keep** — but the "1 KV mount loss = full re-provisioning" failure mode (Section 11) means we either need vault-test environment OR migrate stateful KV out of "config drift on the same instance kills production" risk model |
| **Caddy 2** | Reverse proxy, local CA, `*.internal` routes | **Keep** — best-in-class fit; near-zero config tax; auto-cert; Phase 14 D-LOG access-log integration was clean |
| **Docker Compose** (out-of-repo at `~/control-center-stack/`) | Service lifecycle | **Keep substrate, fix process** — the out-of-repo location is Section 4's biggest config-consistency liability. Move to repo OR establish git-tracked snapshot mechanism. Compose itself is not the problem |
| **Colima** (macOS Docker host) | Linux VM for Docker on Mac | **Keep for now, monitor** — works, but the Mac-specific gotchas (no IPC_LOCK, disable_mlock, named-volume-not-bind-mount Phase 12 finding) accumulate. Linux Threadripper migration is the long-term answer |
| **VictoriaMetrics + vmagent** | Metrics TSDB | **Keep** — Prometheus-compatible, lighter than Prom + Thanos for this scale (~30 services); zero operational complaints |
| **Grafana** | Dashboards | **Keep** — universal default; no realistic alternative |
| **Loki + Promtail** | Log aggregation | **Keep** — Phase 14 D-LOG deployment was clean; LogQL fits the per-site Caddy use case |
| **Restic** | Backup engine | **Keep** — but the chain is currently broken (Section 8); fix before judging the tool |
| **MinIO** | S3 backend on QNAP | **Keep** — single-node MinIO is exactly right for "S3 API for one Restic client" |
| **NetBox** (ADR-A-014) | CMDB / service inventory | **Keep, accelerate consolidation** — only 1 of 4 consumers defaults to it (Section 4 drift). Either commit fully (delete `service-registry.yaml.DEPRECATED` and force CMDB_SOURCE=netbox everywhere) or admit it's optional and update ADR-A-014 to match reality |

### 10.2 Tools where the verdict is "marginal — revisit at next forcing function"

**Plane CE.** Does its job (Plane is the Phase-13+ roadmap source); operational footprint is non-trivial (Postgres + Redis + multiple frontend services); 429 retry quirks documented (memory file `plane_deployment.md`). The platform mostly uses it through `mcp__plane-roadmap__*` MCP server, not directly. **Alternative:** GitHub Issues + Projects gives 80% of the value with zero ops cost. Decision will be forced when Plane next has an outage that consumes >2h to fix; at that point, evaluate whether the remaining 20% of value justifies the cost.

**Zabbix.** Heavyweight (Postgres + TimescaleDB + Zabbix server + frontend + agent + custom exporter). Legitimate use case is host-OS monitoring (CPU, memory, disk on Mac Mini host vs. inside containers — see CLAUDE.md note about NET_RAW exclusion). Phase 14 D-ZBX bridge to vmagent shows we already need to translate Zabbix into Prometheus to consume it. **Alternative:** node_exporter on macOS via `darwin_exporter` or a small launchd-managed Python collector hitting `system_profiler`/`sysctl`/`iostat`. Decision will be forced if Zabbix needs a major version upgrade requiring schema migration.

**Obot (MCP gateway).** Carries 3 of the 3 documented "permanently non-compose-hardened containers" (D#30: mcp-docker-remote, sms1obot-mcp-server, sms1obot-mcp-server-shim). Delivers MCP server orchestration but at the cost of bypassing the platform's container hardening doctrine for those three. **Alternative:** systemd-style supervisor or even direct Docker management with a thin compose lifter for each MCP server. Decision will be forced when Obot's "config API" gap (D#30 root cause) is either filled upstream or no longer worth waiting for.

### 10.3 Tools where the verdict is "evaluate alternatives now"

**Uptime Kuma.** Section 7 finding: 11 of 12 monitors are DOWN due to `mac-mini.internal` DNS resolution failure inside the Uptime Kuma container. The deeper issue: Uptime Kuma runs *inside* Docker but is being asked to monitor services *outside* Docker (the Caddy host listener) using their `*.internal` hostnames. Either the monitor moves outside Docker (launchd-managed `monitoring-plane.py` script) or the monitor uses container-internal addresses. **Alternative:** custom Python health-check script published to vmagent's textfile collector — same metric format, no DNS-context mismatch, ~50 LOC.

**vmalert** is mentioned in Section 7 as not deployed — but VictoriaMetrics ships it as a first-class component. **Recommendation:** deploy vmalert and a small Alertmanager (or Grafana 11+ unified alerting if already wired) before Phase 16 begins. The platform has zero production alerts today — that's not a tool fitness problem, it's a *missing* tool.

**Headscale + 1 client.** Section 1 noted Headscale runs but is barely used (single client = MacBook Pro M5 future parity). At one client, Tailscale's free tier is genuinely zero-cost and zero-ops. Headscale is the right call only if (a) we pass 5 clients, (b) we have a Tailscale-incompatible privacy or vendor-independence requirement, or (c) Mac Studio + future Linux compute join the mesh and tip us over the threshold. With Studio integration imminent, defer the decision 60 days then re-evaluate.

### 10.4 Tools NOT in the stack that probably should be

| Missing tool | Job it would do | Cost estimate |
|---|---|---|
| **vmalert / Alertmanager** | Production alerting (Section 7 gap — zero alerts exist) | ~2h to deploy, ~4h to author initial alert rules |
| **A "vault-test" instance** | Pre-prod for Vault config + policy changes (Section 11 RCA root cause) | ~1h to stand up; saves the next KV-loss incident |
| **PreToolUse hooks for destructive Vault ops** | Prevent the next "I meant to disable transit, not the secret/ KV" mistake | ~2h to author hook + test |
| **`darwin_exporter` or equivalent** | True host-OS metrics from the Mac Mini (replaces partial Zabbix coverage) | ~3h |
| **Diagram generator from NetBox** | Auto-generated as-built architecture (Section 9 F7) | ~6h initial + ongoing low-touch |

### 10.5 Stack complexity — qualitative ranking

Rough mental model: **complexity = (services × interactions) - shared substrate**. The platform's complexity hot-spots are:
1. **Vault + Vault Agent + 28 sidecars** — large interaction surface, but shared substrate (one pattern, replicated). Net-acceptable.
2. **`~/control-center-stack/stacks/*`** — out-of-repo + unsnappable + no diff. The single highest-leverage simplification would be moving these into the repo.
3. **Phase 13 Block 4.C migration substrate** — many CMDB-source-of-truth toggles (per ADR-A-015) running concurrently. Drift in Section 4. Self-resolves as toggles flip and DEPRECATED files delete.
4. **MCP server fleet** — 7 servers, 3 of them outside compose (D#30). Recommended consolidation: bring all 7 under one supervision pattern.

---

## Section 13 — Autonomous Operation Feasibility

**Question:** is the platform ready to operate as "autonomous AI infrastructure" — meaning Claude (or another agent) can be given high-level goals and execute against this platform without human intervention for routine operations?

**Short answer: No, not yet, and the gap is mostly about safety rails — not capability.**

### 13.1 What "autonomous operation" would actually require

A useful definition: a Claude session, given a goal like *"the InvenTree database is full of stale supplier data; refresh from Mouser, run reconciliation, document discrepancies"*, can:
1. **Verify** the goal is well-formed and within scope
2. **Plan** the execution against current state
3. **Execute** safely against production systems
4. **Detect** when something has gone wrong
5. **Recover** or **escalate** appropriately
6. **Report** truthfully to a human reviewer

The platform's current state against each:

| Capability | Current state | Gap |
|---|---|---|
| **Verify** | Strong — CLAUDE.md doctrine ("verification doctrine: every claim verified by command output or cited source") | Minimal |
| **Plan** | Strong — operating-model.md is mature, IV&V loop pattern is well-codified | Minimal |
| **Execute safely** | **Weak** — no PreToolUse hooks; root token in `~/.vault-token` accessible to any session; destructive Vault commands are one keystroke from disaster (Section 11 root cause) | **Significant** |
| **Detect failure** | **Weak** — Section 7 monitoring gaps mean the agent has no canonical "is the system healthy?" signal; backup chain silently broken (Section 8) | **Significant** |
| **Recover** | Mixed — runbooks exist for Vault, but Section 9 finding shows critical gaps (vault-audit-enable, backup-failure-recovery, mcp-server-recovery) | **Moderate** |
| **Report** | Strong — phase doc convention, audit logs (when audit device is enabled), git history | Minimal once Vault audit re-enabled |

### 13.2 The three blocking issues for autonomy

**Blocker 1: No PreToolUse hooks for destructive Vault operations.** The 2026-04-30 KV loss (Section 11) was a Claude session running a Vault command intended to fix one mount but applied to another. A pre-execution hook that intercepts `vault secrets disable secret/`, `vault delete sys/...`, `vault token revoke -orphan`, etc., and requires a typed confirmation **would have prevented the incident outright**. Without these hooks, every autonomous session is one mistyped command away from a Sev-2.

**Blocker 2: No "is the platform healthy?" single source of truth.** An autonomous agent needs an oracle: "before I proceed, is the system OK?" Today: Uptime Kuma is mostly broken, no vmalert, no aggregated health endpoint. The closest thing is `docs/phase-13/h1-regression-probe.sh` — but that's a manual-trigger 30-second script, not a continuous signal. Without a health oracle, the agent cannot safely choose between "execute" and "stop and surface."

**Blocker 3: No vault-test environment.** The agent cannot rehearse Vault changes before applying them to production. Every Vault policy edit, every AppRole rotation, every KV restructure is currently first-touch in production. For a human, this is uncomfortable. For an autonomous agent — where the cost of a wrong action is the same as a human error but the rate of actions is potentially much higher — this is unacceptable.

### 13.3 The smaller gaps (solvable in Phase 16-17)

- **Backup chain broken** (Section 8) means autonomy has no rollback — fix this first regardless of autonomy ambitions
- **Configuration drift across 4 CMDB consumers** (Section 4 / ADR-A-014) means the agent has no single answer to "what services exist?"
- **Out-of-repo `~/control-center-stack/`** means the agent cannot reason about service definitions from git alone
- **No `darwin_exporter`** means host-OS health is mostly invisible
- **Phantom paths in postmortems / inconsistent ADR index** (Section 9) means the agent's documentation reading is sometimes false

### 13.4 What partial autonomy looks like — recommendation

Full autonomy is a Phase 18+ ambition. **Partial autonomy is achievable in Phase 16:**

- **Tier 1 (today, low blast):** Read-only operations — "audit X", "summarize Y", "compare Z". The platform is already ready for this; this audit document itself is an example.
- **Tier 2 (after blockers 1 + 2 fixed):** Bounded write operations against non-Vault systems — adding NetBox records, creating Plane issues, updating dashboards, refreshing InvenTree from Mouser/DigiKey. Blast radius limited; recovery is straightforward.
- **Tier 3 (after blocker 3 fixed):** Vault-touching operations against vault-test first, then production after equivalence verified. The ADR-A-012 equivalence harness doctrine is exactly the right shape for this.
- **Tier 4 (Phase 18+):** End-to-end autonomous execution of multi-system goals. Requires production maturity of Tiers 1-3 plus ongoing-cost monitoring and tighter Section 7 observability.

**Most important single unlock:** PreToolUse hooks for Vault. ~2 operator-hours, removes the worst-case incident class, makes Tier 2 safely possible.

---

## Section 14 — Cost and Complexity Analysis

**Method:** estimate where operator-hours are going, where dollar costs are going, and where the ratio of value-delivered to complexity-carried is suspect. Numbers are estimates from observable indicators (commit frequency, doc volume, incident count) — not stopwatch data.

### 14.1 Hardware capital — single largest line item

| Item | Cost (est.) | Status |
|---|---|---|
| Mac Mini M4 Pro 48 GB | ~$2,400 | Deployed (control plane) |
| Mac Studio M3 Ultra 96 GB | ~$5,500 | Arrives 2026-05-01 |
| MacBook Pro M5 (parity node) | ~$3,500 | Block 3 future |
| QNAP NAS (storage backend) | ~$1,500 | Deployed |
| **Total capital** | **~$12,900** | Mostly delivered |

For an enterprise-equivalent compute capability, this is genuinely cheap — comparable cloud instances would burn this in 2-3 months. Capital is well-spent.

### 14.2 Recurring services — minimal

| Item | Monthly cost (est.) | Note |
|---|---|---|
| Anthropic Pro subscription | $20 | Personal subscription, not platform-billed |
| ChatGPT Plus | $20 | Personal |
| Mouser/DigiKey API | $0 | Free tier sufficient for InvenTree use |
| Domain (nodbox.io.host or similar) | ~$1 | If not already owned |
| Strava API | $0 | Free tier |
| **Cloud LLM API spend** | **$0** | Phase 13.5 deprecated all cloud LLM routes |

The Phase 13.5 cloud-LLM deprecation (CLAUDE.md "LLM Access Doctrine") is a major win on this dimension — the platform has zero LLM-API cost exposure. Anthropic Pro use happens *outside* the platform via `claude-pro` shell function.

### 14.3 Operator-hour spend — the real cost

Estimates from commit history and phase docs:
- **Phase 13** (Apr 28-29, ~2 days): ~50-80 operator-hours (54 phase-13 docs, multi-block work)
- **Phase 14** (Apr 29-30, ~2 days): ~25-40 operator-hours (11 phase-14 docs)
- **Phase 15** (Apr 30 - May 1, ~2 days, in-progress): ~30-50 operator-hours so far (9 docs, plus a Sev-2 incident response)

Implied operator burn rate: **~25-40 hours per active calendar day during phase work.** This is sustainable for short bursts, unsustainable indefinitely. The operator is the bottleneck, not the hardware.

### 14.4 Where complexity exceeds value (audit findings)

1. **Vault Agent sidecar pattern with 28 instances.** Right pattern, right scale — but the operational visibility is poor. When a sidecar fails to authenticate, troubleshooting requires `docker logs <sidecar>` per service. **Cost:** opacity in failure. **Recommendation:** add a single Grafana panel aggregating sidecar exit codes / last-success timestamps from container labels.

2. **3 simultaneous CMDB-source-of-truth toggles in flight (ADR-A-014/A-015 + A-012 equivalence).** Each toggle is doctrinally sound but the cumulative cognitive load is high. **Cost:** Section 4 drift findings (only 1 of 4 consumers defaults to netbox). **Recommendation:** flip remaining toggles to default-netbox and delete deprecated YAML this Phase 16; do not let ADR-A-015 toggles accumulate beyond 2 concurrent.

3. **6 incident docs in 9 phase-15 files.** Sev-2 incident rate during a 2-day window is unsustainable. Root causes from Section 11 (no pre-prod, no PreToolUse hooks) point to systemic safety gaps, not random bad luck. **Cost:** every incident is ~4-8h operator time + risk to production. **Recommendation:** Section 13 Blocker 1 (PreToolUse hooks) is the single highest-leverage cost reduction in the audit.

4. **CLAUDE.md drift (3 broken doc pointers + outdated outstanding items).** **Cost:** every fresh Claude session wastes 5-15 min on discovery dead-ends. ~10 fresh sessions/week × 10 min = ~1.5 hour/week steady-state cost. **Recommendation:** Section 9 same-week fix list is ~1 operator-hour total and pays back continuously.

5. **Out-of-repo `~/control-center-stack/`.** **Cost:** every config change requires either manual snapshot to a `/rewire-log/` doc or accepts that the change is invisible to git. **Recommendation:** Phase 16 work to bring `~/control-center-stack/stacks/` into the repo is high-effort (~8-15h) but eliminates a recurring ~30-60 min/week cost and several Section 4 findings.

### 14.5 Where complexity is well-matched to value (don't simplify these)

- **NetBox CMDB authority** — ADR-A-014 is doctrinally correct even though Section 4 shows incomplete adoption; complete it, don't abandon it
- **Vault-as-secret-store** — the 2026-04-30 incident was a *process* failure (no pre-prod), not a *tool* failure. Vault is the right choice; the safety rails around it need work
- **Container hardening doctrine** (cap_drop, no-new-privileges, mem_limit) — the 3 documented exceptions (D#30) are real and bounded; the other 25+ services correctly hardened
- **IV&V loop pattern + folded gates doctrine** — the 17 ADRs and 364-line operating-model runbook have built genuine operational maturity. This is worth its weight

### 14.6 Recommended cost-benefit-ranked actions

| Action | Operator-hours | Value | ROI |
|---|---|---|---|
| Fix CLAUDE.md broken doc pointers (S9-F1) | 0.5 | Continuous: every session reads better docs | **Very high** |
| PreToolUse hooks for destructive Vault ops | 2 | Prevents next Sev-2 KV loss class | **Very high** |
| Re-enable Vault audit device (CLAUDE.md outstanding) | 0.2 | Restores forensic capability + compliance | **Very high** |
| Fix backup chain end-to-end (S8) | 2 | Restores RPO/RTO promises | **Critical** (without this nothing else recovers) |
| Add ADR-A-014/15/16 to ADR README index | 0.1 | Discoverability | Very high (10× return on time) |
| Stand up vault-test instance | 1 | Removes "production is first-touch" risk class | **High** |
| Move `~/control-center-stack/` into repo | 8-15 | Closes Section 4 drift class permanently | Medium-high (depends on recurrence rate) |
| Deploy vmalert + initial alert rules | 4-6 | Production alerting, Section 7 gap closes | High |
| Author 7 missing runbooks (S9-F2) | 14-21 | Reduces incident MTTR | Medium |
| Generate as-built diagram from NetBox | 6 | Discoverability + autonomous-agent enablement | Medium |

**The first five items total ~5.8 operator-hours and resolve the audit's highest-severity findings.**

---

## Consolidated Risk Register

Severity ranking based on combined likelihood × blast-radius × time-to-detect. All risks are derived from findings in Sections 1-14 and cross-cutting XF-1 through XF-5.

### CRITICAL — fix this week regardless of other priorities

| ID | Risk | Source | Likelihood | Blast | Action |
|---|---|---|---|---|---|
| R-01 | **Backup chain end-to-end broken; no recovery for any service** | S8, S11 | Certain (already true) | Catastrophic — entire platform at RPO=∞ | Same-week action #1 (2h) |
| R-02 | **Vault audit device disabled — no forensic trail for current operations** | S11, CLAUDE.md outstanding | Certain (already true) | Major — next incident has no record | Same-week action #2 (0.2h) |
| R-03 | **Next destructive Vault command can repeat 2026-04-30 KV loss** | S11 RCA | High (process unchanged) | Catastrophic — Sev-2 incident class | Same-week action #3 (2h, PreToolUse hook) |
| R-04 | **System is silent on its own failure — zero production alerts** | S7 | Certain (already true) | Major — failures discovered hours/days late | Phase 16: deploy vmalert + initial rules (4-6h) |

### HIGH — close in Phase 16

| ID | Risk | Source | Likelihood | Blast | Action |
|---|---|---|---|---|---|
| R-05 | Stale Vault root token in `~/vault-init-keys.txt` misleads next incident response | XF-5 | Medium (incident frequency × file usage) | Major — wasted minutes during outage | 5 min file rename + new file write |
| R-06 | CMDB drift — 4 consumers, only 1 defaults to NetBox; live `topology-api` reads YAML | S4, ADR-A-014 | Certain (already true) | Medium — autonomous-agent enablement blocked | Phase 16: complete A-014 migration, delete deprecated YAML |
| R-07 | `~/control-center-stack/` out-of-repo; config changes invisible to git | S4, S10 | Certain (already true) | Medium — diagnostic friction, drift accumulates | Phase 16-17: bring stack into repo (8-15h) |
| R-08 | Production Vault changes are first-touch — no pre-prod | S11, S13 Blocker 3 | High (every Vault change) | Catastrophic when it goes wrong | Same-week action #4: stand up vault-test (1h) |
| R-09 | CLAUDE.md broken doc pointers misdirect every fresh Claude session | S9-F1 | Certain (already true) | Medium — wasted context, wrong assumptions | Same-week action #6 (0.5h) |
| R-10 | Uptime Kuma broken DNS — 11 of 12 monitors DOWN; appears healthy | S7 | Certain (already true) | Medium — false confidence in monitoring | Phase 16: replace Uptime Kuma OR fix DNS context |
| R-11 | Vault Agent sidecar exits silently if Vault token rotation fails | XF-1, S11 | Medium (depends on rotation cadence) | Medium per service | Phase 16: aggregate sidecar exit metrics to Grafana |

### MEDIUM — Phase 16-17

| ID | Risk | Source | Likelihood | Blast | Action |
|---|---|---|---|---|---|
| R-12 | ADR governance broken — 3 violations including in-place A-007 edit | S9-F3 | Certain (already true) | Low-medium — doctrine erodes | Resolve A-007 dirty edit; update README index; same-week (0.5h) |
| R-13 | Locally-built images without tags (`mkdocs`, `openhands-app`, `structurizr`) | XF-4 | Low (image prune required) | Medium per service if hit | Phase 16: tag images and push to local registry |
| R-14 | `control-plane` and `catt-controller` containers exited 16h ago, undetected | XF-3 | Already happened | Unknown — depends on what they do | Phase 16: investigate and fix or document one-shot intent |
| R-15 | 7 critical runbooks missing (vault-audit-enable, backup-failure-recovery, etc.) | S9-F2 | High (runbook gaps mean longer MTTR) | Medium per incident | Phase 16: author top 3 (vault-audit-enable, backup-failure-recovery, mac-studio-day1) |
| R-16 | No "is the platform healthy?" oracle — autonomy blocked | S13 Blocker 2 | Certain (already true) | Blocks Tier 2-4 autonomy | Phase 17: aggregated health endpoint |
| R-17 | `vault-restore-from-backup` runbook has never been tested end-to-end | S8 | High (next test = real incident) | Critical when it matters | Phase 16: dry-run quarterly per CLAUDE.md, starting next week |
| R-18 | Mac Mini hardware single point of failure — no platform-wide HA | S8 RTO=multi-day | Low per year | Catastrophic when it happens | Phase 17+: define HA strategy (or accept and document) |

### LOW — backlog / informational

| ID | Risk | Source | Likelihood | Blast | Action |
|---|---|---|---|---|---|
| R-19 | Documentation conflict — PLATFORM_OVERVIEW.md vs ARCHITECTURE.md no banner | S9-F4 | Low (most readers find ARCHITECTURE first) | Low | Phase 16: add deprecation banner OR delete |
| R-20 | Phase doc naming convention partially enforced | S9-F5 | Low | Low | Either tighten or amend CLAUDE.md |
| R-21 | Known-issues registry under-utilized vs CLAUDE.md hardening trade-offs | S9-F6 | Low | Low | Pick one canonical location |
| R-22 | No as-built architecture diagram | S9-F7 | Low | Low | Phase 17: generate from NetBox |
| R-23 | Headscale at 1 client — operational tax exceeds value | S10 | Low | Low | Defer 60d, re-evaluate post-Studio |
| R-24 | Plane CE marginal value vs operational cost | S10 | Low | Low | Decide at next forcing function |

**Risk count by severity:** CRITICAL 4, HIGH 7, MEDIUM 7, LOW 6 — total **24 tracked risks**.

---

## Phase 17+ Forward Roadmap (audit-driven)

The existing `docs/PHASE_ROADMAP.md` (2026-04-30) sets out Phase 16 as "Compute Expansion + Data Integrations" — Mac Studio enabled, InvenTree real-data, NetBox+InvenTree+Plane+ADR cross-index, Phase 13 closure. **This audit doesn't displace that plan; it adds a parallel track of operational-maturity work that should run alongside the roadmap's capability work.**

### Phase 16 — recommended additions (parallel to roadmap's existing 16.A-D scope)

**Track O (Operational Maturity) — ~30-40 operator-hours total:**

| Block | Scope | Effort | Closes |
|---|---|---|---|
| **16.O.1** Same-week fix list (this audit's exec summary) | Backup, audit, hooks, vault-test, phantom paths, CLAUDE.md docs | 6h | R-01, R-02, R-03, R-08, R-09 |
| **16.O.2** Production alerting | vmalert deploy + initial alert rules + Grafana unified-alerting wire-up | 4-6h | R-04 |
| **16.O.3** CMDB consolidation | Flip remaining 3 of 4 consumers to CMDB_SOURCE=netbox default; delete `service-registry.yaml.DEPRECATED`; verify `topology-api` switch | 4h | R-06 |
| **16.O.4** Sidecar observability | Aggregate vault-agent sidecar exit codes + last-success timestamps to Grafana dashboard | 3h | R-11 |
| **16.O.5** Stack-into-repo migration | Move `~/control-center-stack/stacks/*` to `repo/control-center-stack/`; symlink for compatibility; document rewire | 8-15h | R-07 |
| **16.O.6** Critical runbook authoring | `vault-audit-enable.md`, `backup-failure-recovery.md`, `mac-studio-day1.md`, `mcp-server-recovery.md` | 8-12h | R-15 |
| **16.O.7** Restore drill | Execute `vault-restore-from-backup.md` end-to-end against vault-test (now exists per 16.O.1); fix runbook bugs found | 4h | R-17 |
| **16.O.8** Image tagging | Tag and push `mkdocs`, `openhands-app`, `structurizr` to local registry; reference by tag in compose | 2h | R-13 |
| **16.O.9** Uptime Kuma replacement OR DNS fix | Either fix container-DNS for `*.internal` OR replace with launchd-managed Python health-check published to vmagent textfile collector | 4-6h | R-10 |
| **16.O.10** Documentation hygiene | ADR README index update; A-007 dirty-edit resolution; PHASE_LOG.md refresh; PLATFORM_OVERVIEW.md deprecation banner | 2h | R-12, R-19 |

**Phase 16 = capability roadmap (existing) + Track O (~40h). Total Phase 16 effort: ~125-170h.**

### Phase 17 — autonomy enablement + observability depth (~80-120h)

The existing roadmap doesn't yet name a Phase 17. This audit recommends:

| Block | Scope | Why |
|---|---|---|
| **17.A** Health oracle | Aggregated `/health` endpoint that returns single GO/NO-GO + per-component status; consumable by autonomous agents | R-16, S13 Blocker 2; unlocks Tier 2 autonomy |
| **17.B** Tier 2 autonomy bounded write ops | Restricted execution profile for Claude sessions: NetBox/Plane/InvenTree write ops permitted; Vault read-only; no destructive Docker | S13.4; first real-world autonomy validation |
| **17.C** As-built diagram from NetBox | Generated topology diagram (Mermaid or D2) auto-built from NetBox CMDB on commit; published to `docs/architecture/` | R-22, S9-F7 |
| **17.D** Mac Studio compute productionization | (Per existing roadmap 16.A — may fold in if delayed) Ollama on Studio; LiteLLM Studio backend; smart routing extension | Capability |
| **17.E** Darwin host metrics | `darwin_exporter` or equivalent on Mini + Studio; replaces Zabbix host monitoring partial coverage | S10.4 |
| **17.F** Backup coverage expansion | Add `~/control-center-stack/`, all stateful Docker volumes, Plane DB, NetBox DB to Restic backup paths; verify test-restore | S8 RTO/RPO gap |

### Phase 18+ — long-horizon

| Item | Why |
|---|---|
| **HA strategy decision** | R-18; Mac Mini single-point-of-failure resolved by HA cluster, hot spare, or accepted-and-documented |
| **Tier 3 autonomy** | Vault-touching operations through vault-test→prod pipeline; equivalence harness (A-012) extended to operational changes, not just data migrations |
| **Multi-host scheduling** | Real workload distribution between Mini and Studio (today, Mini does everything; Studio is "specialized compute" in roadmap but mechanism is unclear) |
| **Linux Threadripper migration** | If macOS-specific gotchas accumulate; per CLAUDE.md "future blocks beyond Block 3"; revisit when Mac-specific issue count crosses ~5 documented exceptions |

### Sequencing principle

The audit's strongest recommendation: **do Phase 16 Track O.1 (same-week fix list) before any Phase 16 capability work begins.** The capability work is fine to plan in parallel, but executing capability work against a platform with broken backups, no audit trail, no alerts, and no PreToolUse hooks compounds risk on every change. ~6 hours invested in Track O.1 buys orders-of-magnitude reduction in incident severity for the rest of Phase 16.

---

## Audit Closeout

**Document status:** Complete. All 14 sections delivered (reordered: 12, 11, 1-9, 10, 13, 14, exec summary, risk register, roadmap).

**Source artifacts (preserved for traceability):**
- `/tmp/audit-section-11-vault-rca.md` — Vault forensic deep-dive (~2700 words)
- `/tmp/audit-sections-1-3-inventory.md` — Service inventory + redundancy (~3300 words)
- `/tmp/audit-sections-2-4-6-foundations.md` — ADR + config + security (~3800 words)
- `/tmp/audit-sections-5-7-8-flows.md` — Data flows + observability + backup (~3800 words)
- `/tmp/audit-containers.txt`, `/tmp/audit-stopped.txt` — container snapshots

**Caveats and limitations:**
- Audit conducted in single ~6h session; some findings (especially Section 7 monitoring depth and Section 14 operator-hour estimates) would benefit from longer observation windows
- Vault root-token instability during audit (XF-5) prevented some forensic queries; conclusions in Section 11 partly inferred from logs and postmortems rather than live `vault audit list` output
- Out-of-repo `~/control-center-stack/` was inspected but not exhaustively enumerated; Section 4 findings are likely floor-not-ceiling on drift
- Mac Studio not yet present at time of audit; Section 12 GO recommendation is based on artifact review (checklist + execute script + Mini state), not Studio-side validation

**Recommended next session goals (in order):**
1. Execute the 6 same-week actions (~6 operator-hours total) from the executive summary
2. Run Mac Studio Day-1 with the three pre-Day-1 confirmations from Section 12
3. Open Phase 16 with both Track O (operational maturity, this audit) and the existing capability roadmap

**Audit signoff:** Claude Code (claude-opus-4-7), 2026-05-01, running on `mac-mini.internal`.
