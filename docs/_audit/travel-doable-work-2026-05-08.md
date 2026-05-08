# Travel-Doable Work Backlog — 2026-05-08

**Date:** 2026-05-08
**Status:** ACTIVE — operator-curated working list for travel sessions
**Branch:** `travel/2026-05-07/documentation-hardening`
**Scope frame:** all platform work that does NOT depend on the home network, D-17-211 hardware migration, or destructive surfaces requiring operator presence at the carriage house

## Why this list exists

The D-17-211 architectural rework (8 hardware artifacts + project plan) is gated on operator-presence pre-flight items and will execute when home. **In parallel**, substantial platform work CAN ship from a MacBook on travel — design, spec, doc, decision, code-that-deploys-later, and any item explicitly scoped to be substrate-independent. This list catalogs that parallel track so the trip stays productive and we don't accidentally let it idle waiting on the migration.

The D-17-MEDIA master plan (created 2026-05-07 on this branch) already structures 10 of these as P1/P2/P3 deliverables. This document widens the catalog with: visualizations, operator surfaces, RSS feeder (NEW per operator 2026-05-08 input), 3D-model provenance schemas, and pending in-progress items that don't need home presence.

## Category 1 — Media stack work (D-17-MEDIA master plan items)

Per `docs/decision-records/D-17-MEDIA-master-plan.md`. All of these are travel-doable in their **design + spec + repo-config-authoring** phases. Deployment phases gate on home-network access.

| ID | Deliverable | Travel-doable scope | Status |
|---|---|---|---|
| **D-17-150** | Tailscale CLI consolidation | DECISION DONE; execution pending 24-48h verification window | DECISION DONE, EXECUTION PENDING |
| **D-17-153** | Seedbox migration (Whatbox NL + qBittorrent) | Full WP-01..04 design + qBittorrent compose + path-mapping schema. Cutover gates on home. | NOT STARTED → can advance to design-complete |
| **D-17-154** | Sync transit hardening (Syncthing throughput) | Throughput-test plan authoring + telemetry schema | NOT STARTED → spec-doable |
| **D-17-155** | TRaSH path discipline migration | Full path-mapping spec + per-app config plan | NOT STARTED → fully spec-doable |
| **D-17-156** | arr-stack TRaSH alignment via Recyclarr | Recyclarr config-as-code authoring (yaml in repo) | NOT STARTED → fully authorable in repo |
| **D-17-157** | Music stack — Navidrome verification path | Test plan + verification checklist | NOT STARTED → spec-doable |
| **D-17-158** | Audiobook stack — Audiobookshelf + Readarr | Compose authoring + provenance + acquisition flow | NOT STARTED → fully authorable |
| **D-17-159** | Plex → Jellyfin migration | DECISION DONE [B]; migration steps gated on Mac Mini access | DECISION DONE, EXECUTION GATED |
| **D-17-160** | Goose media-ops recipes | DESIGN COMPLETE; 5 recipes specified | DESIGN COMPLETE |

**Travel-week recommendation:** push D-17-153 through D-17-156 from NOT STARTED to DESIGN COMPLETE. That's 4 deliverables advanced via repo authoring, no home presence required.

## Category 2 — Visualizations & operator surfaces (existing dashboards)

Repo already has:
- `docs/dashboards/logical-service-architecture.html` — D-17-17 (Phase 16 carry-over)
- `docs/dashboards/physical-architecture.html` — D-17-18 (Phase 16 carry-over)

These are HTML files. Editable + previewable in browser from MacBook. Travel-doable enhancements:

- Update with the new D-17-211 architecture (organs, MS-01 convergence, TB segment, circulatory metaphor visualization)
- Add the unified hardware × software/AI mapping from `2026-05-08-platform-unified-architecture.md`
- Surface live-utilization hooks (consume Topology API JSON when home network accessible) — design-only on travel
- Operator Control Plane / Homarr / Homepage UI improvements — design + mockup only

Effort: each dashboard refresh ~M (medium); 2-3 sessions to advance both.

## Category 3 — RSS feeder + AI enhancement pipeline (NEW per operator 2026-05-08)

### Quick evaluation per article-intake-protocol

**Step 1 — Source:** operator-provided in-chat document covering RSS feed taxonomy + integration pipeline + curation tools across AI/home automation/ARR-self-hosting/hardware/3D-design domains.

**Step 2 — Validation:**
- Pattern is well-established (RSS aggregator → automation → AI summarization)
- Specific feeds cited (arXiv cs.AI, Hugging Face Blog, Home Assistant Blog, GitHub release atom feeds) are real and accessible
- Tools cited split: commercial (RSS.app, Inoreader, Make.com, Zapier, Feedly) vs OSS alternatives (FreshRSS, miniflux, NewsBoat, n8n, Huginn)
- **Substantiated-with-caveat:** the source recommends commercial tooling; substituting OSS alternatives is required for doctrine fit

**Step 3 — Roadmap fit:**
- **Conceptual:** STRONG. An automated RSS → AI digest pipeline directly addresses Findings AA + BB. Pairs with article-intake-protocol — pipeline produces candidates, protocol evaluates them.
- **Hardware:** fits MS-01 Linux VM post-D-17-211; can prototype on QNAP Container Station now
- **Doctrine:** OSS-fit requires substituting commercial tools with self-hosted alternatives. Compatible.
- **Recommendation:** **Adopt-pattern-not-implementation.** Self-hosted equivalent stack.

**Step 4 — Scope:**

**New deliverable: D-NN-NNN — Self-hosted RSS feeder + AI enhancement pipeline** (TBD ID; operator owns phase placement)

- **Substrate (proposed):**
  - Aggregator: **miniflux** (single-binary Go, very lightweight) OR **FreshRSS** (PHP, more features). Operator preference.
  - Automation: **n8n** (already a Symphony candidate per locked roadmap) — ingests new feed items, dispatches to AI for digest
  - AI processing: existing local Ollama via litellm-gateway with a routing rule for "rss-digest" task
  - Output: digest into Obsidian vault / Nextcloud / OpenProject ticket / direct email — operator picks
- **Hardware target:** MS-01 Linux VM post-migration; QNAP Container Station as an interim home if operator wants to deploy before D-17-211 lands
- **Initial feed list (from operator's input):**
  - **AI/research:** arXiv cs.AI, Hugging Face Blog, OpenAI News, Google AI Blog, Anthropic blog
  - **Industry/system design:** ByteByteGo, Hacker News, AIOps feeds (IBM, Dynatrace)
  - **Home automation:** Home Assistant Blog, Hackaday, IoT Tech News, Automated Home
  - **Self-hosting / ARR:** Self-Hosted Awesome List atom, Linux Journal, GitHub release atoms (Sonarr, Radarr, Lidarr, Prowlarr, Plex, Jellyfin, Navidrome, Audiobookshelf — `<repo>/releases.atom` for each)
  - **Hardware:** Ars Technica, Engadget, SparkFun product feed
  - **3D design:** Blender Nation, Two Minute Papers (YouTube atom), Dezeen
- **Effort:** medium (1-2 weeks; mostly integration plumbing once design lands)
- **Travel-doable scope:** full design + compose authoring + feed list curation + AI digest prompt design. Deployment gates on home.
- **Cross-references:** article-intake-protocol.md (pipeline produces candidates, protocol evaluates); strategic-watch.md (long-running watch items become RSS-tracked); locked roadmap T1 (System Prompt Library — digest prompts live there)

## Category 4 — Other roadmap items travel-doable

From locked roadmap (per memory) + PROJECT_FRAMEWORK section 9:

| Topic | Scope this week |
|---|---|
| 3D model license-aware schema (Manyfold + Gitea LFS) | Schema design doc; SPDX license field + reciprocal-obligation flag + attribution + modification history |
| AI 3D generation provenance (InstantMesh + TripoSR pipeline) | Provenance schema for AI-generated meshes; license inheritance rules |
| ESP32 enclosure license tracking | Asset-registry field design (CERN-OHL-P / CC-BY / CC0 / MIT preferences for printed cases) |
| Strategic-watch review | Re-evaluate watch entries; add Sakana RL Conductor entry per Sakana eval |
| Conductor-pattern POC design (per Sakana eval WP-I-06) | Meta-prompt design; LiteLLM Gateway /conductor route spec; benchmark task selection |
| D-17-129 codex51 campaign expansion | Task selection for N>=30 set (pure planning, no execution) |
| D-17-126 multi-file orchestration | Continued benchmark analysis (data analysis, no infra changes) |
| D-17-118 routing classifier alignment | WP-06 doctrine + prompt-conventions update authoring |
| D-17-XXX RAG context pack | 50-task historical re-run benchmark task selection (planning) |
| Inbox Zero deployment (BLOCKED on Gmail tier scope) | Resolve Gmail tier scope decision (pure operator decision) |
| MacBook Pro M5 parity (Phase 13 Block 3, Phase 17 OOS) | Design doc for parity scope: Ollama subset, LiteLLM client, smart routing rules |

## Category 5 — Pending operator-side actions

These do not need design - they need OPERATOR EXECUTION:

| ID | Action | When |
|---|---|---|
| D-17-115 | Install /tmp/caddy-root.crt to MacBook keychain, mark Trusted | Anytime |
| D-17-100/102 | sudo networksetup -setdnsservers Wi-Fi 192.168.10.1 then re-run Lidarr remote checks | When on home LAN or via tailnet |
| D-17-54 | Verify OPNsense Kea UI path + OpenProject rails-runner password-reset syntax | Operator-side at OPNsense GUI |
| D-17-52 | Pre-departure checklist per singapore-pre-departure-checklist.md | Before/during current trip |
| D-17-114 | Plex client verification post-plex.internal cutover | Operator-side from any client |
| D-17-150 | Tailscale.app removal (after 24-48h verification window) | Operator-side on macmini |

## Category 6 — Document the architecture rework (this session)

Already done. The 11 artifacts dated 2026-05-08 ARE this kind of work, shipped from MacBook. They are all uncommitted and pending operator decision on commit/branch.

## Suggested ordering for THIS WEEK

If operator wants high-leverage parallel work:

Highest impact, lowest dependency:
1. Commit the 11 architecture artifacts to a fresh feat/d-17-211-rearchitecture branch (or this branch)
2. D-17-153 design-complete (Whatbox NL + qBittorrent migration spec)
3. D-17-155 design-complete (TRaSH path discipline spec)
4. D-17-156 design-complete (Recyclarr config-as-code in repo)
5. RSS feeder deliverable scoping (miniflux vs FreshRSS, deployment target, compose, feed list)
6. Conductor-pattern POC design (Sakana WP-I-06): meta-prompt + LiteLLM route spec
7. Visualization refresh: update logical-service-architecture.html and physical-architecture.html for post-D-17-211 architecture
8. Strategic-watch review and add Sakana entry

Lower-leverage (still travel-doable):
9. 3D-model license-aware schema design
10. AI 3D generation provenance schema
11. ESP32 enclosure license tracking

Operator-side execution (any time):
12. D-17-115 CA install (5 min)
13. D-17-100/102 DNS change (1 min, when on home LAN or tailnet)
14. D-17-54 OPNsense + OpenProject verifications (10 min at OPNsense GUI)
15. D-17-52 pre-departure checklist (only if Singapore trip is upcoming)

## What is NOT travel-doable (gates on home network or hardware presence)

- D-17-211 Phase A (Proxmox install, OPNsense VM, cutover): physical access to MS-01 + Protectli, maintenance window
- D-17-211 Phase B (Vault relocation, arr-stack migration): gates on Phase A
- D-17-211 Phase C (TB cabling): physical cable installation at MS-01 + QNAP
- D-17-211 Phase D (Pi monitoring): Pi physical placement
- D-17-159 Plex to Jellyfin migration execution: Mac Mini access
- D-17-153 cutover to Whatbox: design happens now; cutover gates on home network for testing parallel pipelines

## Recommendations

1. Commit the 11 architecture artifacts. They are durable; uncommitted is real risk during travel-network sessions.
2. Pick 3-4 items from Suggested ordering for this week. Do not try all 8.
3. RSS feeder is genuinely valuable as a meta-tool. It feeds article-intake-protocol with candidates and reduces operator missing items between sessions.
4. Conductor POC (Sakana WP-I-06) is a natural pair with the RSS feeder: RSS finds candidates, protocol evaluates, Conductor routes high-value tasks.
5. Visualization refreshes are operator-perception-improving. Easy wins making the architecture rework feel real.

## Cross-references

- docs/decision-records/D-17-MEDIA-master-plan.md (8 media stack deliverables)
- docs/runbooks/d-17-211-master-project-plan.md (Phase A-I rearchitecture, most gated on home)
- docs/architecture-facts/article-intake-protocol.md (applied above to scope RSS feeder)
- docs/_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md (Conductor POC parent)
- docs/architecture-patterns/strategic-watch.md (where Sakana watch entry goes)
- docs/runbooks/singapore-pre-departure-checklist.md (D-17-52 travel readiness)

## Status

ACTIVE as of 2026-05-08. Operator-curated working list. Items advance via normal deliverable lifecycle (intake -> design -> close). RSS feeder is the new entry from this session and needs a real D-NN-NNN ID assignment.
