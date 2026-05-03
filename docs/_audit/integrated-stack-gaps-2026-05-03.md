# D-17-32 — Stack integration gap report

**Date:** 2026-05-03
**Inputs:** docs/_audit/integrated-stack-target-2026-05-03.md (target state),
            ~/.platform-registry/inventory.json (registry, refreshed 2026-05-03 00:07),
            OpenProject WP queue (live query 2026-05-03 ~22:00),
            docs/architecture-facts/* (8 chronicles),
            docs/PROJECT_FRAMEWORK.md §9 (28 Phase-17 deliverable rows)

**Method.** For each of the six target flows in `integrated-stack-target-2026-05-03.md`, traced actual current state against structural requirement. Then mapped each gap to (a) is there a roadmap or framework item? (b) is it in OpenProject's queryable queue? (c) is it tagged for autonomous-coding filter? Severity scale: **B** = blocks autonomous coding outright (agent cannot complete a class of integrated task); **D** = degrades quality (agent works but with manual hand-holding the integration was supposed to remove); **N** = nice-to-have hardening.

Effort estimates use the same point convention as the framework (~hours, with historical +50% discovery overhead understood).

---

## Flow A — Inference path

**Target.** Agent → registry lookup → litellm:4000 with bearer → backend (Ollama / exo) → response. All routes structurally tool-callable for the agent class consuming them.

**Actual (verified 2026-05-03).**
- Registry exists, fresh (00:07 today, 1.0s refresh, 76 services + 13 runtime orphans + 31 caddy routes + 125 credential files).
- litellm-gateway at port 4000 carries 6 routes: `qwen-coder-7b`, `qwen-coder-14b`, `qwen-coder-32b`, `devstral`, `deepseek-coder` (all Ollama-backed), `exo-qwen-coder-7b` (exo-backed). Verified with bearer auth.
- Master key in Vault (`secret/litellm/master#master_key`), fingerprint `439bcdb691d6` matches D-17-26 chronicle.
- Claude Code orchestrator → Anthropic native: works.
- Subagent → Ollama native: works.
- Goose / any other streaming OpenAI-compat agent → BLOCKED-UPSTREAM (Findings 1+2 in `local-tool-calling.md`).

### Gap A1 — No agent-consumable surface for "list current routes" beyond direct litellm call (severity D, effort 2h)

The registry lists litellm-gateway as a service and surfaces the credentials file path, but does NOT enumerate the routes litellm carries — that's litellm's `/v1/models` endpoint. An agent today must (a) consult the registry to find litellm's port + bearer credential location, (b) read the credential file (or call a python helper), (c) hit `/v1/models` directly. Three steps for "what can I route to."

- **Roadmap item?** No direct match. Nearest is RM-16-A-002 ("LiteLLM Gateway on Mini: add `studio-fast` ... routes") — that's a build item, not a "discoverability" item.
- **In OpenProject queue?** No.
- **Tagged autonomous-coding?** N/A.
- **Recommendation.** New deliverable: extend `xindex` with a `litellm` axis ingesting `/v1/models` + per-route backend health → expose via `xindex_get_inference_routes` MCP tool. Closes the seam.

### Gap A2 — Tool-calling protocol gap for non-Anthropic-native agent hosts (severity B for agent-portfolio expansion, severity N for current demo, effort: NONE — upstream-blocked)

Findings 1+2 in `local-tool-calling.md` are upstream-blocked. Goose evaluation closed BLOCKED-UPSTREAM (D-17-13). For the Saturday demo this is fine because Claude Code + subagents covers the autonomous-coding centerpiece. But it means Flow A's "any agent host" structural requirement is not met — the platform supports two specific agent paths, not a portable surface.

- **Roadmap item?** No — chronicled, watched.
- **In OpenProject queue?** No (correct: upstream-blocked work doesn't belong in queue until a revisit signal fires).
- **Recommendation.** Track upstream Ollama + Goose + exo upstream signals; no new framework item needed. Already documented in candidate-tools.md.

### Gap A3 — Mac Studio Ollama not yet contributing to litellm route inventory (severity D, effort: covered by RM-16-A-001/002)

Mac Studio is the compute node (D-17-15 done) but the routes `studio-fast` / `studio-large` / `studio-embed` are not yet wired (RM-16-A-001 + 002 backlog). Today every Ollama-backed inference call hits Mini's Ollama, leaving Studio's 96 GB pool effectively unused for autonomous-coding work.

- **Roadmap item?** Yes — RM-16-A-001 (Ollama on Studio) + RM-16-A-002 (LiteLLM gateway routes for Studio).
- **In OpenProject queue?** Yes (both Backlog under Phase-16).
- **Tagged autonomous-coding?** Items have `[auto]` description marker per D-17-31 sync output, but **NO `autonomous-coding` category** (verified — category does not exist in OpenProject; see Flow F gap F1).
- **Recommendation.** Already correctly tracked; the gap is the category-filter problem from Flow F, not a roadmap miss.

---

## Flow B — InvenTree inventory awareness

**Target.** Agent references hardware → queries InvenTree → blended with NetBox + ADR context via cross-index → grounded recommendation.

**Actual (verified 2026-05-03).**
- InvenTree running (port 8087, route `inventree.internal`, version 1.0.9, 4 workers, 10 plugins active).
- API requires authentication for any data endpoint (`/api/part/` returns 401).
- InvenTree contents: unknown to this audit, but 129-component CSV import (RM-16-B-004) is in Backlog → likely empty or mostly-empty.
- xindex MCP tools (verified): `xindex_search`, `xindex_get_adr`, `xindex_get_runbook`, `xindex_get_service`, `xindex_get_node`, `xindex_get_workpackage`, `xindex_get_plane` (deprecated alias), `xindex_get_links`. **No InvenTree axis or `xindex_get_part` / `xindex_get_supplier`.**
- Mouser + DigiKey integrations (RM-16-B-005, 006): Backlog, blocked on operator-side API key + OAuth.

### Gap B1 — InvenTree empty + cross-index has no InvenTree axis → flow inoperative end-to-end (severity D, effort ~25-40h — equals RM-16-B in full)

Even if the agent wanted to query InvenTree, there's no agent-tool surface (no MCP wrapper) and likely no data. Flow B is inoperative; the integration is structurally not present.

- **Roadmap item?** Yes — RM-16-B-004 (CSV import), RM-16-B-008 (cross-index InvenTree axis), RM-16-B-005/006 (Mouser/DigiKey).
- **In OpenProject queue?** Yes — all Phase-16 Backlog.
- **Tagged autonomous-coding?** Description `[auto]` markers present on the ones the heuristic matched; no category.
- **Recommendation.** Sequencing: B-004 (CSV import) and B-008 (cross-index axis) are the unblockers; B-005/006 layer supplier metadata. The MCP wrapper to expose InvenTree to agents (`xindex_get_part`?) is NOT in the roadmap explicitly — implicit in B-008 but worth calling out as a separate WP under that deliverable.

### Gap B2 — Hardware inventory does not include the operator's actual development hardware substrate (severity D, effort: scope of asset-management deliverable family, see Flow C)

Even with B1 closed, InvenTree as scoped today catalogs *components* (parts for builds), not the operator's *operating hardware* (Mac Mini, Mac Studio, OPNsense, QNAP, Threadripper-future). NetBox holds nodes; InvenTree holds parts. There's no surface that holds "this Mac Mini's NVMe firmware version + RAM module supplier + connected accessories." That's the asset-management substrate (Finding T) and overlaps with Flow C.

- **Roadmap item?** Asset-management deliverable family is intake-doc'd in operator memory but NOT framework-authored.
- **Recommendation.** Author the asset-management family as 4 framework rows (A/B/C/D scope from operator memory) so it appears in §9 and OpenProject. Without that, the gap is invisible to "what's next" queries.

---

## Flow C — Asset / firmware / OS state awareness

**Target.** Agent consults asset register before recommending changes; blocks recommendations that would violate version-compatibility constraints (e.g., D-17-25 macOS-alignment lesson).

**Actual.**
- No asset register exists.
- Per-host OS version is knowable via `system_profiler` / `sw_vers` on each node but is not captured in any agent-queryable registry.
- Per-container image version is in `~/.platform-registry/inventory.json` (e.g., `hashicorp/vault:2.0.0`) — that covers container layer only.
- Per-accessory firmware (Garmin, Oura, Zigbee sensors, 3D printer mainboards, ESP32) — none.
- Library / dependency versions — none.

### Gap C1 — Asset/firmware/OS register absent across all categories (severity B for the operator's stated requirement, effort: 30-50h scoped as a deliverable family)

The 2026-05-02 macOS upgrade incident IS the canonical worked example for why this matters. AI recommended an OS upgrade without consulting state because there was nothing to consult. Operator-caught; reboot already triggered.

- **Roadmap item?** Asset-management deliverable family (intake-doc'd, not framework-authored).
- **In OpenProject queue?** No (because not framework-authored → not synced).
- **Recommendation.** **Highest-leverage gap of the audit.** Promote asset-management family from intake doc to four framework rows under Phase-17 (or open Phase-17.5 / re-tier). Without this, Flow C cannot exist; with it scoped, Findings T + DD have a remediation home.

### Gap C2 — Container image staleness has no surface (severity D, effort ~6-8h)

Diun (image-watcher in upgrade-watcher work) was scoped in 16.C-003 (Upgrade watcher calibration) — Backlog. No today-surface for "which of my 84 containers are running stale images."

- **Roadmap item?** RM-16-C-003.
- **In OpenProject queue?** Yes, Backlog.
- **Recommendation.** Already correctly tracked; depends on Mac Studio being in routing rotation first (RM-16-A) so the watcher has the full container population.

---

## Flow D — Provenance gate

**Target.** Wrapper-mediated pulls; agent can enumerate provenance state.

**Actual.**
- Wrappers exist: `verify-model-provenance.sh`, `ollama-pull-verified.sh`, `hf-download-verified.sh` (D-17-10 done).
- Cisco Provenance Kit pinned at v1.0.0 (commit `5f27dc56`).
- 6 backfilled JSON records in `docs/_provenance/` (Devstral, Qwen2.5-Coder-7B + 4bit + 8bit, SmolLM2, nomic-embed) plus `overrides.log`.
- Wrapper enforcement is by *convention* — operators (and agents) must run `ollama pull` via the wrapper, not naked `ollama pull`. No technical enforcement of the convention (no shell alias, no hook).
- Agent surface: NONE. Provenance JSONs are file-based; no MCP getter, no xindex axis, no registry inclusion.

### Gap D1 — No agent-consumable enumeration of provenance state (severity D, effort ~3-4h)

Agent can `Read` `docs/_provenance/*.json` by guessing filenames or `ls` the directory — but cannot ask "is model X attested" via tool call.

- **Roadmap item?** No.
- **In OpenProject queue?** No.
- **Recommendation.** New deliverable (or scope amendment to D-17-10 follow-on): xindex axis for `_provenance/` → `xindex_get_provenance(model='...')` MCP tool. Returns verdict + top-K matches + override status. ~3-4h.

### Gap D2 — Wrapper enforcement is convention-only (severity N, effort ~1-2h)

Naked `ollama pull` works today; nothing prevents bypass. Operator and agent must remember.

- **Roadmap item?** No.
- **Recommendation.** Either a shell wrapper alias (`alias ollama=...`), a `pre-commit`-style hook on the model-cache dirs, or accept-the-convention with a doctrine note. ~1-2h. Consider after D1 because the enumeration would catch convention violations after-the-fact.

---

## Flow E — Documentation flow

**Target.** Agent → CLAUDE.md → canonical chronicle → context loaded.

**Actual.**
- CLAUDE.md is current (D-17-24 closed 2026-05-03 in commit f76ac51).
- 8 architecture-facts chronicles exist; CLAUDE.md doctrine block lists them.
- xindex MCP exposes `xindex_get_runbook`, `xindex_get_adr`, `xindex_get_service`, `xindex_get_node`, `xindex_get_workpackage`, `xindex_get_links`, `xindex_search`. **No `xindex_get_architecture_fact` or `xindex_get_chronicle`.**
- xindex_search FTS5-covers `adr/runbook/register/service/node/workpackage` — chronicles are NOT in that list.
- Per CLAUDE.md drift surface (D-17-18 chronicle): Mac Studio listed at `.146` but actual is `.142` (ping + ARP confirmed). Drift in CLAUDE.md propagated through D-17-24's rewrite — recommend follow-up correction.

### Gap E1 — Architecture-facts chronicles are not searchable via xindex (severity D, effort ~3-5h)

8 chronicles, agents must know the path. No ranked search across them. Operator-side `grep` works but agent must tool through Bash.

- **Roadmap item?** No.
- **In OpenProject queue?** No.
- **Recommendation.** Add `architecture-facts` as a xindex source axis; expose `xindex_get_architecture_fact(name='exo-cluster')` and include in `xindex_search` FTS5 corpus. ~3-5h.

### Gap E2 — CLAUDE.md hardware-block IP drift (severity N, effort ~10 min)

Mac Studio shown at `.146`, actual `.142`. Latent because most paths use TB-Bridge link-local; LAN IP only matters for non-TB consumers (Zabbix agent, monitoring scrapes).

- **Roadmap item?** No.
- **Recommendation.** Trivial doc fix; can be folded into the next CLAUDE.md edit cycle. Trigger: D-17-18 SMOKE doc surfaced this — that's the canonical reference for the correction.

---

## Flow F — Project management flow

**Target.** Agent answers "what's next?" by consulting framework §9 + OpenProject queue, filterable by autonomous-coding category.

**Actual.**
- Framework §9 is current (D-17-32 added 2026-05-03; 27 D-17-* rows + 1 D-17-22 reserved).
- OpenProject mirror has 751 WPs across versions Phase-15 (12), Phase-16 (44), Phase-17 (49), Phase-18 (25), plus 621 unversioned (legacy Plane import).
- Active backlog: Phase-16 (29 active), Phase-17 (4 active), Phase-18 (25 active).
- **Categories present in OpenProject (65 total):** A11Y, AI, APIGW, AUTO, AUTO-MECH, Architecture, BACKUP, CI/CD, CONFIG, CORE, DEV, DOCAPP, Deployment, FLOW, GOV, HOME, HW, I18N, INT, INTEL, INV, KB, LANG, LEARN, MOBILE, MONITOR, Monitoring, OBS, OPS, PERF, PERIPH, PLUGIN, QA, REFACTOR, REL, SCALE, SEC, SHOP, UI, USERMGMT, UTIL, UX, api, blocked, bug, chore, cli, compliance, data, dependency, docs, enhancement, feature, high-priority, infra, media, milestone, needs-review, quick-win, risk, security, spike, technical-debt, testing, ui-ux. **`autonomous-coding` is NOT in this list.**

### Gap F1 — `autonomous-coding` category absent in OpenProject; CLAUDE.md doctrine references nonexistent filter (severity B for the operator's "what's next" query, effort ~15 min operator + 30 min sync re-run)

Verified 2026-05-03 via API: `autonomous-coding` category does not exist. The D-17-31 sync script attempts to look up the category, gets None back, and falls back to a description-text marker (`[auto]` suffix on the category-line in the title-label per `scripts/openproject-sync-from-framework.py:630`). 21 RM items currently carry the `[auto]` description marker; 0 carry the category.

CLAUDE.md says (verbatim, line in doctrine block): *"OpenProject's queue (filter by status=Backlog/In Progress, optionally category=autonomous-coding)"*. This filter cannot be applied because the category doesn't exist — the agent following CLAUDE.md doctrine will issue a query that returns zero matches and silently get bad data.

The script's NOTE handles this gracefully (it logs a one-time warning at sync start), but the operator-side action — *"create the category via the OpenProject UI"* per the script's hint — has not been performed.

- **Roadmap item?** No (this is a remediation of a D-17-31 close-loose-end).
- **In OpenProject queue?** No.
- **Recommendation.** **Operator-side action: create `autonomous-coding` category in OpenProject UI** (~5 min via Settings → Work packages → Categories). Then re-run `python3 scripts/openproject-sync-from-framework.py --include-roadmap` (~5 min). Sync will pick up the category and apply it to the 21 `[auto]`-flagged items on next pass. Total: 15 min operator + 5 min sync. Severity B because every "what's next" query that follows CLAUDE.md doctrine is currently broken.

### Gap F2 — CLAUDE.md sync flag inventory documents a flag that doesn't exist (severity D, effort ~5 min)

CLAUDE.md (line in OpenProject paragraph, post-D-17-31): *"Convenience: `python3 scripts/openproject-sync-from-framework.py --query-backlog [--autonomous-coding-only]`."* Verified 2026-05-03: the script does NOT implement `--query-backlog` or `--autonomous-coding-only`. The implemented flags are `--dry-run`, `--phase`, `--include-roadmap`, `--roadmap-only`, `--dedup-phase17`. The doctrine misleads the agent into trying a flag that errors out.

- **Roadmap item?** No (D-17-31 close error).
- **Recommendation.** Either (a) implement `--query-backlog` (~30 min, would actually be useful — read-only query mode that lists backlog with status + version + category filters), OR (b) correct CLAUDE.md to remove the false reference. Option (a) is preferred because the use case is real; option (b) is the fast fix.

### Gap F3 — 621 unversioned WPs from legacy Plane import (severity N, effort ~1-2h cleanup OR 0h ignore)

Of OpenProject's 751 WPs, 621 carry no Version assignment (these are the original Plane-import set from D-17-04 WP-17-04-03, predating the regex patch that enabled Phase-17 WPs to import). They contribute to backlog noise — `Backlog` count is 587 globally.

- **Roadmap item?** No.
- **Recommendation.** Either bulk-assign the 621 to a `Phase-15` or `Imported-Pre-Sync` version (so they're filterable-out), or accept-as-historical and rely on Version filtering to exclude them. Low priority unless an agent's "what's next" query is dominated by them.

### Gap F4 — RM-HW-* scope stranded in plane archive, never carried into OpenProject (severity D, effort ~30 min triage + 0-2h carry-forward decision)

Surfaced via the parallel-session audit (operator concern that another Claude window may have created an ESP32-related roadmap artifact). That session produced no artifact, but the audit found two pre-existing items in `docs/_archive/plane-export-2026-05-02.json` that were NOT migrated into OpenProject during the D-17-04 plane retirement:

- `RM-HW-001` — "AI-assisted electrical design workflow for ESP32 and Nordic hardware" (strategic 4/5, architecture fit 4/5, execution risk 3/5, target horizon: later)
- `RM-HW-002` — "Flipper-style embedded shell for ESP32 and Nordic devices" (strategic 3/5, architecture fit 4/5)

Verified 2026-05-03 via OpenProject API: keyword search across all 609 WPs for `esp32 / kicad / digikey / mouser / electronic design / project capture / schematic / pcb / eda` returns zero hits matching this scope. The items are present in the archived JSON but invisible to "what's next" queries, framework §9, PHASE_ROADMAP.md, and the agent's xindex search.

This is a *D-17-04 close-loose-end*, not a parallel-session error. The plane-import path filtered out items without canonical RM-NN-X-NNN identifiers; `RM-HW-*` did not match the regex.

- **Roadmap item?** Items exist in archive only. Not in any active surface.
- **In OpenProject queue?** No.
- **Tagged autonomous-coding?** N/A (not present at all).
- **Recommendation.** **NEW deliverable proposed (D-17-NN, do NOT auto-create in T5):** RM-HW-* triage. Outcomes: either (a) carry-forward into Phase-18 roadmap as `RM-18-A-006` / `RM-18-A-007` (fits the Phase-18 hardware-axis grouping), OR (b) document explicitly as deliberately-not-carried with rationale (e.g., "ESP32/Nordic hardware design is out of scope for the current platform horizon — revisit in Phase-19+"). Operator decision in next planning pass; sized at 30 min triage + 0-2h depending on outcome.

---

## Cross-flow gaps (apply to multiple flows)

### Gap X1 — Registry has no MCP/agent surface beyond CLAUDE.md convenience snippet (severity B for D#25 doctrine consistency, effort ~3-5h)

D#25 doctrine says "consult registry before any port/dependency op." Registry is fresh (`launchctl list | grep platform-registry` not registered yet — Finding Y; refresh runs manually or via subprocess). The CLAUDE.md "convenience reader" snippet is a 4-line python invocation. **There is no MCP tool wrapping it.** Every agent session that follows D#25 must spawn Bash + run the snippet. This works but is friction-heavy and doesn't enumerate the registry's full shape (`runtime_orphans`, `caddy_orphans`, `credentials_summary`, etc.).

- **Roadmap item?** No (registry is fresh — D-17-29 closed) — but the agent-surface for it was not part of D-17-29's scope.
- **In OpenProject queue?** No.
- **Recommendation.** New deliverable (~3-5h): xindex MCP wraps the registry. Tools: `registry_get_service(name)`, `registry_list_orphans()`, `registry_get_credentials(service)` (metadata only — fingerprint/path/mode, never values). Closes the seam between D#25 doctrine and agent execution.

### Gap X2 — Launchd registration of registry refresh is pending (severity N, effort ~5 min next login)

Finding Y: 14 IAP launchd plists in `~/Library/LaunchAgents/` but `launchctl list | grep com.iap` returns zero post-reboot. Auto-recovery on next login per macOS launchd convention. Until then, registry refresh runs only when manually triggered.

- **Recommendation.** Defer to next operator login; if registry staleness becomes load-bearing, fall back to `scripts/platform-registry/refresh.sh` manually.

### Gap X3 — Cold-start / Vault-unseal automation absent (severity N, effort: post-demo decision per Finding Z reservation)

Operator considered Vault retirement during D-17-28 recovery. Reservation: post-demo deliverable, not pre-empting the architectural decision. Currently a 30+-service downtime risk on every routine OS upgrade.

- **Roadmap item?** Reserved post-demo.
- **Recommendation.** Defer per operator framing. Mention in WP-05 backlog only as low-priority follow-on.

### Gap F5 — Health checks validate container liveness, not integration paths (severity B, effort: deliverable family ~20-40h)

Phase 6/7 hardening introduced container-level health checks (Docker `HEALTHCHECK` + Uptime Kuma + Zabbix host monitoring). Those signals validate "container is up + responding to liveness probe" but do NOT validate end-to-end flows. A container can be `(healthy)` while its downstream integration is silently broken.

**Empirical confirmation (2026-05-03 evening):** the QNAP SMB mount used by Sonarr's media library was broken for an unknown duration. Sonarr's container health check returned green throughout. The break was only surfaced when the operator observed import failures in a separate troubleshooting session. **No platform health signal caught it.** This is the canonical worked example for the gap, parallel to the role D-17-25's macOS-upgrade incident plays for C1.

This cross-cuts:
- **B3 (C1, asset-mgmt family)** — asset register would catch firmware/OS drift; F5 catches *flow* drift. Different surfaces, both needed.
- **The broader operator framing:** "subsystems work but integration doesn't." Container-level health is subsystem-level closure; integration-path health is the missing surface.

For autonomous coding, this is severity B by extension: an agent that consults health-check signal (Zabbix triggers, Uptime Kuma status, container `(healthy)` state) and trusts it will operate on false-positive state. Recommendations grounded in "service X is healthy, so the integration through it works" can be wrong.

Examples of integration-path checks that would belong in the new family:
- **Sonarr import end-to-end:** SMB mount reachable + container can read mount + new file lands + library refresh picks it up
- **Vault → Vault Agent sidecar → container env propagation:** secret X in Vault matches what `/proc/1/environ` reads inside container Y (per Finding DD doctrine — `docker exec env` is the wrong probe)
- **exo cluster → litellm → Open WebUI roundtrip:** a real chat-completion request flows through all three layers and returns expected output (D-17-30 verified this manually once; no recurring check)
- **Backup chain:** Restic snapshot create + restore-to-tmpdir verify, scheduled monthly minimum

- **Roadmap item?** No. Phase 6/7 closeouts assert "monitoring complete" — that scope was container-layer, not integration-layer. The integration-layer claim is doctrine drift not previously surfaced.
- **In OpenProject queue?** No.
- **Tagged autonomous-coding?** N/A.
- **Recommendation.** **NEW deliverable family proposed (do NOT auto-create in T5):** end-to-end integration health checks. Separate from registry consultation (which proves what *should* exist) — this proves what *actually flows* through the stack. Sized at ~20-40h depending on flow coverage; could be tiered like the asset-mgmt family (e.g., F5-A inference path, F5-B media stack, F5-C secret propagation, F5-D backup verification). Doctrine outcome: explicit chronicle "container `(healthy)` is not `(integration working)`" plus per-flow probes captured as runbooks or scheduled scripts.

### Gap F8 — QNAP SMB mount persistence work blocked behind Finding Y; mount failures are silent until import attempted (severity D, effort ~30 min once Y resolves)

The 2026-05-03 evening recovery (referenced in F5) restored the QNAP SMB mount manually via `mount_smbfs`, which gets the arr-stack working in-session but **does not survive Mac Mini reboot**. The persistence path — keychain entry + LaunchAgent at `~/Library/LaunchAgents/com.iap.qnap-downloads-mount.plist` + `launchctl bootstrap gui/$(id -u)` — is fully prepared in `docs/runbooks/qnap-downloads-mount.md` but cannot execute today: every `launchctl bootstrap gui/$(id -u) ...` against any `com.iap.*` plist returns `Bootstrap failed: 125: Domain does not support specified action` (Finding Y, X2 above). Adding a 14th unloadable plist while Y is active would only muddle the diagnosis.

The recurring-pain-point shape:
- **Silent until exercised.** SMB mount loss surfaces no health signal — Sonarr container reports `(healthy)`, Uptime Kuma stays green, Zabbix triggers stay dormant. The first symptom is an import failure inside Sonarr's UI/API, hours or days after the mount went away.
- **Multiple loss vectors.** Reboot (no LaunchAgent), Mac sleep/wake (smbfs does not auto-reconnect after extended idle), `umount`, container restart timing relative to mount establishment.
- **Mount-after-container has its own failure mode.** Docker Desktop's filesystem bridge does not pick up SMB overlays onto an existing bind path; the container continues to see the empty pre-mount directory until restarted (`docker restart sonarr radarr`). This is documented in the runbook's failure-modes table but is not platform-detected.

**Cross-reference to F5.** This is the canonical concrete instance of the F5 family — F5 is the doctrine ("container-healthy is not integration-working"); F8 is the specific work item that would close the *persistence* half of the F5-B media-stack tier. The *detection* half (probing whether `/Users/admin/mnt/qnap-downloads` resolves to a populated SMB tree from inside the arr containers) is still F5 family work.

- **Roadmap item?** No.
- **In OpenProject queue?** No.
- **Tagged autonomous-coding?** N/A.
- **Trigger condition.** Finding Y (X2) resolved — verified by any successful `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.iap.<any>.plist` exit 0. At that point execute `docs/runbooks/qnap-downloads-mount.md` Steps 1–5; mount becomes reboot-persistent.
- **Pending-followup link.** `~/Documents/pending-platform-followups.md` carries the active item so the Finding Y resolution session executes it without re-discovery.
- **Recommendation.** Defer until Finding Y resolves (next operator login should auto-resolve via macOS launchd convention). No new deliverable needed — this is a runbook execution gated on an upstream condition. If F5 family is authored, this work folds in as F5-B-001 (or equivalent). If Finding Y does NOT auto-resolve at next login, escalate Y itself to a B-severity blocker since 14 IAP LaunchAgents will be unloadable (registry refresh, this mount, and 12 others).

### Gap F9 — Conversation-as-completion regression: PDF / binary persistence pattern never built (severity B, effort: covered by D-17-35 + ~2-4h pattern doctrine)

Prior chat sessions ingested PDFs (and other binaries) into context for derivation work, then derived facts were persisted via the auto-memory layer — but the source binaries themselves did NOT persist. When a later session needs the originals (for re-extraction at different granularity, for downstream deliverables that consume more than the previously-derived facts, or for verification), the operator must re-paste the same binary attachment a second (and third) time.

**Empirical confirmation (2026-05-03 D-17-35 T0):** the operator's Ono Island carriage-house design chat (claude.ai chat 7bdfb1b5-...) produced derived facts (lot dimensions, carriage-house orientation, flood-zone, structural pile spec) that were captured into operator-locked-fact memory. But the underlying 36-page permit set PDF (`Cox_V3_-_CD_05__Permit_Set__All__signed__25-03-10__House.pdf`) was never persisted to a durable location. The operator is now re-pasting the same PDF a second time today to enable D-17-35 ingestion, which then unblocks D-17-33 Overwatch (camera/sensor placement reads E-1/E-2/E-3 sheets directly from the permit set, not from the derived-facts summary).

This is the **third** "conversation-as-completion" pattern surfaced this session, joining:
- **D-17-34** — audit recommended HA container retirement; conversation agreement was treated as completion; container kept running for ~48h.
- **F5** — container `(healthy)` signal treated as completion of integration validation; Sonarr/QNAP SMB mount silently broken.
- **F9** — PDF ingestion to context treated as completion of persistence; binaries lost on session end.

The underlying anti-pattern: **derivation outputs are persisted; raw inputs are not**. Memory is great for distilled facts, terrible for the originals those facts came from. Property plans, vendor PDFs, screenshots, RFCs, large reference docs, exported reports — all share this shape.

For autonomous coding, this is severity B because:
- It blocks any deliverable whose work product needs structured access to the original document (per-page/per-sheet extraction, geometry/coordinate reads, image-content queries) rather than the conversation-derived summary.
- It creates a recurring re-paste burden that scales with how often the same binary is referenced — D-17-35 unblocks at least D-17-33, and any future property-related deliverable would need the plans again.
- It silently violates the verification doctrine: a future agent asked "where are the planned exterior cameras?" cannot answer from memory alone (memory has the derived-facts summary, not the E-series sheets); the only answer requires re-ingesting the PDF the operator already pasted twice.

**Cross-reference to F7 (architecture-facts doctrine, 2026-05-03 close).** F9 is the binary-asset analogue of F7: F7 says recommendations require executed validation, not conversation agreement; F9 says raw inputs require executed persistence, not conversation ingestion. Both are conversation-as-completion regressions in different layers of the work product.

- **Roadmap item?** No.
- **In OpenProject queue?** No.
- **Tagged autonomous-coding?** N/A — D-17-35 is the carrying deliverable for the property-plans instance.
- **Recommendation.** Two-part close:
  1. **D-17-35 itself** delivers the *property-plans* instance: durable out-of-repo home (`~/Documents/property/<parcel>/source/`, 700 admin-only) + registry pointer + xindex axis with per-page/per-sheet metadata so AI queries hit `E-1/E-2/E-3` (not just an opaque PDF blob).
  2. **WP-05 doctrine deliverable** (proposed only, do NOT auto-create in T5): a *binary-asset persistence pattern* chronicle in `docs/architecture-facts/` that generalizes the D-17-35 pattern (out-of-repo location convention + registry pointer + index granularity guideline) so the next class of binary input (vendor PDFs, screenshots, RFCs) follows the same shape without re-deriving the convention. Sized at ~2-4h. Likely lives next to or merges into the F4 family (Stranded data substrates) once that family materializes.

**Status update (2026-05-03 D-17-37 close):** GAP CLOSED. D-17-37 delivered the substrate (QNAP path layout under `download/manual/roadmap-artifacts/`, qnap:// pointer schema, ingest+resolve scripts at `scripts/artifact-{ingest,resolve}.sh`, sibling registry axis at `~/.platform-registry/artifacts/`, ACL classes property/schematics/vendor-docs/source-files, launchd-chained refresh). Doctrine chronicled at `docs/architecture-facts/integration-audit-doctrine.md` Finding 5 (incl. backup posture rationale + substrate-defining-deliverable exemption pattern + smbfs cleanup gotcha). D-17-35 retrofit reduced to a single operator command once PDF lands on filesystem. Severity downgrade: B → CLOSED (was-B).

---

## Summary — gap inventory (19 gaps)

| # | Sev | Effort | Has roadmap item? | In queue? | Tagged AC? |
|---|-----|--------|-------------------|-----------|------------|
| A1 | D | ~2h | No | No | N/A (new) |
| A2 | B (portfolio) | upstream | No | No | N/A |
| A3 | D | covered | Yes (RM-16-A-001/002) | Yes | description only |
| B1 | D | ~25-40h | Yes (RM-16-B family) | Yes | description only |
| B2 | D | family | No (intake only) | No | No |
| C1 | **B** | ~30-50h | No (intake only) | No | No |
| C2 | D | ~6-8h | Yes (RM-16-C-003) | Yes | description only |
| D1 | D | ~3-4h | No | No | N/A (new) |
| D2 | N | ~1-2h | No | No | N/A (new) |
| E1 | D | ~3-5h | No | No | N/A (new) |
| E2 | N | ~10 min | No | No | N/A (trivial) |
| F1 | **B** | ~15 min op + 5 min sync | No (D-17-31 close-loose-end) | No | N/A (this IS the AC-tagging fix) |
| F2 | D | ~5 min | No | No | N/A |
| F3 | N | ~1-2h or 0 | No | No | N/A |
| F4 | D | ~30 min triage + 0-2h | No (stranded in plane archive) | No | N/A |
| F5 | **B** | ~20-40h family | No (Phase 6/7 close-extension) | No | N/A (new family) |
| F8 | D | ~30 min (Y-blocked) | No (runbook exists, gated) | No | N/A |
| F9 | **B** | covered (D-17-35) + ~2-4h doctrine | No (D-17-35 carries instance) | No | N/A (new pattern) |
| X1 | **B** | ~3-5h | No (D-17-29 close-extension) | No | N/A (new) |
| X2 | N | next login | N/A (auto-recovery) | No | N/A |
| X3 | N | post-demo | Reserved | No | N/A |

Five **B-severity** gaps blocking integrated autonomous-coding flow:
- **F1** — `autonomous-coding` category missing → "what's next" filter broken
- **C1** — No asset register → upgrade-recommendation flow cannot exist
- **X1** — Registry has no MCP surface → D#25 doctrine has no clean execution path
- **F5** — Health checks validate container liveness, not integration paths → agents trust false-positive signal (empirical: 2026-05-03 Sonarr/QNAP SMB mount break went undetected)
- **F9** — Binary inputs (PDFs etc.) ingested to context but not persisted → recurring re-paste burden, blocks deliverables that need structured per-page/per-sheet access (empirical: 2026-05-03 D-17-35 Ono Island permit set re-paste)

These are the WP-05 priority candidates.
