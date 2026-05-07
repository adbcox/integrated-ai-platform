# D-17-MEDIA Master Plan: Seedbox + qBittorrent + Full Media Stack

**Status:** ACTIVE
**Owner:** Adrian Cox
**Created:** 2026-05-07
**Last updated:** 2026-05-07 (flight session)
**Branch:** travel/2026-05-07/documentation-hardening
**Update cadence:** After each WP closure or status change

---

## Executive summary

Migrate the media acquisition + library stack from current state (seedit4me + rTorrent + Syncthing + Plex) toward target state (Whatbox NL + qBittorrent + Syncthing + open-source media servers) with TRaSH-aligned paths, Recyclarr-driven config-as-code, and Goose-driven operational agents.

Scope split into **8 independently-executable deliverables (D-17-153 through D-17-160)** so work can pause and resume without losing momentum. Each deliverable has its own WBS, acceptance criteria, and rollback plan.

---

## Master tracker

| ID | Deliverable | Priority | Status | Blocked by | Est. effort | Started | Completed |
|---|---|---|---|---|---|---|---|
| D-17-153 | Seedbox migration (Whatbox NL + qBittorrent) | P1 | NOT STARTED | none | 2-4 hr active + 30 days parallel | — | — |
| D-17-154 | Sync transit hardening (Syncthing throughput verify) | P1 | NOT STARTED | D-17-153 WP-04 | 2 hr | — | — |
| D-17-155 | TRaSH path discipline migration | P1 | NOT STARTED | D-17-153 WP-02 | 3-5 hr | — | — |
| D-17-156 | arr-stack TRaSH alignment (Recyclarr) | P2 | NOT STARTED | D-17-155 | 4-6 hr | — | — |
| D-17-157 | Music stack completion (Navidrome verified) | P2 | NOT STARTED | D-17-156 | 2-3 hr | — | — |
| D-17-158 | Audiobook stack (Audiobookshelf + Readarr) | P3 | NOT STARTED | D-17-155 | 3-4 hr | — | — |
| D-17-159 | Plex vs Jellyfin decision + execution | P3 | NOT STARTED | D-17-156 | 1 hr decision + 4-8 hr if migrate | — | — |
| D-17-160 | Goose media-ops recipe library | P2 | DESIGN STARTED | D-17-149 design | 4-6 hr | 2026-05-07 | — |

Status values: `NOT STARTED` | `IN PROGRESS` | `BLOCKED` | `WAITING REVIEW` | `DONE` | `DEFERRED`
Priority: P1 (critical path) | P2 (high value) | P3 (nice to have)

---

## D-17-153: Seedbox migration (Whatbox NL + qBittorrent)

**Goal:** Replace seedit4me/Hetzner Falkenstein/rTorrent with Whatbox NL/qBittorrent 5.2 without service interruption.

**Acceptance criteria (DONE = all true):**
- Whatbox NL account active with qBittorrent 5.2 running
- Throughput verified: ≥50 Mbps sustained from Whatbox to QNAP
- All arr-apps reconfigured to use Whatbox qBit
- 30-day parallel run completed; seedit4me cancelled
- Final state documented in this file under "Decisions log"

**Work packages:**

| WP | Description | Status | Est. | Notes |
|---|---|---|---|---|
| WP-153-01 | Pre-signup verification: ping Whatbox NL netblock from Comcast home IP. Verdict ≤50ms RTT, ≤1% loss = proceed. >50ms or loss = abort, try Bytesized | NOT STARTED | 15 min | DO NOT skip — repeats seedit4me mistake otherwise |
| WP-153-02 | Sign up Whatbox NL with qBittorrent 5.2 selected at signup. Configure WebUI auth, IP allowlist for home IP only, SSH key auth | NOT STARTED | 30 min | $15/mo |
| WP-153-03 | Set up TRaSH-aligned categories on qBit: `tv-sonarr`, `movies-radarr`, `music-lidarr`, `books-readarr` (placeholder). Each with TRaSH save paths | NOT STARTED | 30 min | |
| WP-153-04 | Throughput baseline test: SCP a 100MB test file home→Whatbox AND Whatbox→home. Record results in Decisions log | NOT STARTED | 15 min | Gates WP-153-05 |
| WP-153-05 | Update Prowlarr connection to point at Whatbox qBit API. Old seedit4me rTorrent stays connected (parallel) | NOT STARTED | 30 min | |
| WP-153-06 | Update Sonarr/Radarr/Lidarr download client list: add Whatbox qBit as **secondary** (not primary yet) | NOT STARTED | 30 min | Parallel mode preserved |
| WP-153-07 | Pilot test: Lidarr-first. Add 1 album. Verify route → Whatbox qBit → sync to QNAP → Lidarr import → Navidrome serves | NOT STARTED | 1 hr | Smallest blast radius |
| WP-153-08 | Pilot test: Sonarr (1 episode) | NOT STARTED | 1 hr | After WP-07 passes |
| WP-153-09 | Pilot test: Radarr (1 movie) | NOT STARTED | 1 hr | After WP-08 passes |
| WP-153-10 | Promote Whatbox qBit to primary; demote seedit4me rTorrent to secondary | NOT STARTED | 15 min | New downloads now go to Whatbox |
| WP-153-11 | Parallel run period: 30 days. Old torrents on seedit4me continue seeding for ratio. New torrents on Whatbox | NOT STARTED | 30 days | Calendar |
| WP-153-12 | End of parallel: confirm no active torrents on seedit4me. Cancel seedit4me subscription | NOT STARTED | 15 min | |
| WP-153-13 | Final documentation in Decisions log + close D-17-153 | NOT STARTED | 30 min | |

**Risks:**
- Whatbox NL has same routing issue as Hetzner: WP-01 catches this BEFORE signup
- qBit 5.2 has bugs incompatible with arr-apps: WP-07/08/09 piloted in low-risk order
- Some old torrents fail to migrate: acceptable — let them age out

**Rollback (any phase):**
- Pre-WP-10: just cancel Whatbox, keep seedit4me as primary
- Post-WP-10: re-promote seedit4me as primary, debug Whatbox issue, retry pilot

---

## D-17-154: Sync transit hardening

**Goal:** Verify and harden seedbox→QNAP sync. Default Syncthing; fallback to Mullvad-on-QNAP if Whatbox routing also degraded.

**Depends on:** D-17-153 WP-04 (throughput baseline)

**Acceptance criteria:**
- Sustained throughput ≥50 Mbps over 24-hour test
- Sync completes within 5x file-size-on-fastest-link (e.g., 5GB file ≤8min on 100Mbps link)
- Sync resumes correctly after network interruption
- Documented in `docs/runbooks/seedbox-sync.md`

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-154-01 | Install Syncthing on Whatbox seedbox; pair with QNAP Syncthing instance | NOT STARTED | 30 min |
| WP-154-02 | Configure folders: `tv/`, `movies/`, `music/`, `books/` with one-way send-only from seedbox | NOT STARTED | 30 min |
| WP-154-03 | 24-hour throughput test: record min/avg/max throughput, completion time for known file sizes | NOT STARTED | 24 hr passive |
| WP-154-04 | If WP-03 ≥50 Mbps avg: write `docs/runbooks/seedbox-sync.md` and close. ELSE proceed to WP-05 | NOT STARTED | 30 min |
| WP-154-05 | (Conditional) Set up Mullvad VPN on QNAP, route only seedbox-pull traffic via Mullvad | NOT STARTED | 1 hr |
| WP-154-06 | (Conditional) Re-run throughput test through Mullvad path | NOT STARTED | 24 hr passive |
| WP-154-07 | Document final architecture and rollback in runbook | NOT STARTED | 30 min |

**Rollback:** Revert to current Syncthing on seedit4me until D-17-153 closes; Mullvad cancellable monthly.

---

## D-17-155: TRaSH path discipline migration

**Goal:** Reorganize QNAP filesystem to TRaSH-aligned `/data/{torrents,media}/{movies,tv,music,books}/` layout with hardlinks.

**Depends on:** D-17-153 WP-02 (need TRaSH categories defined first)

**Acceptance criteria:**
- All media on QNAP matches TRaSH layout
- Hardlinks verified (same inode, no duplicate space)
- All arr-apps' import paths updated, no orphaned references
- Documented in `docs/runbooks/trash-path-migration.md`

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-155-01 | Audit current QNAP paths: where is everything? Document in `~/repos/integrated-ai-platform/artifacts/qnap-current-paths.md` | NOT STARTED | 1 hr |
| WP-155-02 | Decide single-filesystem requirement: TRaSH needs torrents+media on same FS. Choose target QNAP volume | NOT STARTED | 30 min |
| WP-155-03 | Create TRaSH directory tree on chosen volume: `/data/torrents/{tv,movies,music,books}/`, `/data/media/{tv,movies,music,books}/` | NOT STARTED | 15 min |
| WP-155-04 | Move existing media to TRaSH paths. Use `mv` within same FS for atomic moves. Document any cross-FS copies needed | NOT STARTED | 1-3 hr depending on size |
| WP-155-05 | Update Sonarr root folder + import path to new structure | NOT STARTED | 15 min |
| WP-155-06 | Update Radarr root folder + import path | NOT STARTED | 15 min |
| WP-155-07 | Update Lidarr root folder + import path | NOT STARTED | 15 min |
| WP-155-08 | Update Plex/Jellyfin library paths to new media root | NOT STARTED | 30 min |
| WP-155-09 | Test hardlink atomicity: download a test file via Whatbox qBit, verify hardlink on import (`ls -li` shows same inode) | NOT STARTED | 30 min |
| WP-155-10 | Document final path layout + write migration runbook | NOT STARTED | 1 hr |

**Risks:**
- Cross-filesystem moves break hardlinks: WP-02 catches this; uses single-FS strategy
- arr-apps "miss" files post-move: each arr can rescan; budget 1 hr buffer

**Rollback:** All moves are reversible via `mv` if same-FS. Keep symlink-or-copy of original layout for 7 days.

---

## D-17-156: arr-stack TRaSH alignment via Recyclarr

**Goal:** Apply TRaSH-Guides quality profiles + custom formats via Recyclarr config-as-code.

**Depends on:** D-17-155 (paths must be sane first)

**Acceptance criteria:**
- Recyclarr config in repo at `recyclarr/recyclarr.yml`
- Sonarr quality profiles match TRaSH HD-1080p or UHD-2160p (operator decision)
- Radarr quality profiles match TRaSH equivalent
- Custom formats applied; release scoring matches TRaSH
- Recyclarr cron run daily, logs to QNAP
- Documented in `docs/runbooks/recyclarr-deployment.md`

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-156-01 | DECISION: HD-1080p or UHD-2160p profile for Sonarr/Radarr? Document in Decisions log | NOT STARTED | 15 min |
| WP-156-02 | Install Recyclarr (Docker container preferred) | NOT STARTED | 30 min |
| WP-156-03 | Generate baseline `recyclarr.yml` from chosen TRaSH profile | NOT STARTED | 30 min |
| WP-156-04 | Dry-run: `recyclarr sync --preview`. Review changes before applying | NOT STARTED | 30 min |
| WP-156-05 | Apply: `recyclarr sync`. Verify in Sonarr/Radarr UI | NOT STARTED | 30 min |
| WP-156-06 | Configure cron / systemd timer for daily sync | NOT STARTED | 30 min |
| WP-156-07 | Lidarr config-as-code: Recyclarr doesn't cover. Either manual or `lidarr-config-tools`. DECISION needed | NOT STARTED | 1 hr |
| WP-156-08 | Document deployment + rollback runbook | NOT STARTED | 1 hr |

---

## D-17-157: Music stack completion (Navidrome verified end-to-end)

**Goal:** Working music pipeline: Lidarr request → Whatbox qBit → QNAP music library → Navidrome serves → Amperfy/Symfonium plays.

**Depends on:** D-17-156 (Lidarr aligned)

**Acceptance criteria:**
- Navidrome running on QNAP, points at TRaSH music library
- 10 successful Lidarr requests end-to-end (request → playback)
- Amperfy on iOS plays from Navidrome (check via Tailscale at home, also direct LAN)
- Symfonium on Android plays from Navidrome (proprietary exception per master log §28)
- "Read-only" gate flipped only after 10 successful imports

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-157-01 | Verify Navidrome deployment on QNAP. If not running: deploy via Docker | NOT STARTED | 30 min |
| WP-157-02 | Configure Navidrome library scan against TRaSH music path | NOT STARTED | 15 min |
| WP-157-03 | Set Navidrome to READ-ONLY mode initially | NOT STARTED | 5 min |
| WP-157-04 | Install Amperfy on iPhone, configure for Navidrome via Tailscale | NOT STARTED | 30 min |
| WP-157-05 | Install Symfonium on Android, configure for Navidrome | NOT STARTED | 30 min |
| WP-157-06 | 10-album test: Lidarr requests, end-to-end verify each | NOT STARTED | 1 hr active + ongoing |
| WP-157-07 | Flip Navidrome OFF read-only after 10 successful tests | NOT STARTED | 5 min |
| WP-157-08 | Document in `docs/runbooks/music-stack.md` | NOT STARTED | 30 min |

---

## D-17-158: Audiobook stack (Audiobookshelf + Readarr)

**Goal:** Add audiobook acquisition + library + playback.

**Depends on:** D-17-155 (paths)

**Acceptance criteria:**
- Readarr running, integrated with Prowlarr
- Audiobookshelf running on QNAP
- 3 successful audiobook requests end-to-end
- iOS + Android Audiobookshelf clients work via Tailscale

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-158-01 | Deploy Readarr (Docker) | NOT STARTED | 1 hr |
| WP-158-02 | Connect Readarr → Prowlarr | NOT STARTED | 30 min |
| WP-158-03 | Configure Readarr download client (Whatbox qBit, books category) | NOT STARTED | 30 min |
| WP-158-04 | Deploy Audiobookshelf (Docker on QNAP) | NOT STARTED | 1 hr |
| WP-158-05 | Configure Audiobookshelf library against TRaSH books path | NOT STARTED | 15 min |
| WP-158-06 | 3-book pilot: end-to-end verify | NOT STARTED | 1 hr |
| WP-158-07 | Mobile clients (iOS + Android) configured | NOT STARTED | 30 min |
| WP-158-08 | Document in `docs/runbooks/audiobook-stack.md` | NOT STARTED | 30 min |

---

## D-17-159: Plex vs Jellyfin decision + execution

**Goal:** Resolve the proprietary-vs-OSS streaming server question.

**Depends on:** D-17-156 (stable arr-stack)

**Acceptance criteria:**
- Decision documented with reasoning
- If migrate: Jellyfin running, library imported, Apple TV/iOS/macOS clients verified
- If stay: doctrine update accepting Plex as proprietary exception (parallel to Symfonium)

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-159-01 | DECISION: Plex (paid, polished, proprietary exception) vs Jellyfin (free, OSS, rougher edges) | NOT STARTED | 1 hr |
| WP-159-02 | If Jellyfin: deploy Docker, point at TRaSH media paths | NOT STARTED | 1 hr |
| WP-159-03 | If Jellyfin: parallel-run with Plex 30 days | NOT STARTED | 30 days |
| WP-159-04 | If Jellyfin: configure Infuse on Apple TV (works with both) | NOT STARTED | 30 min |
| WP-159-05 | If Jellyfin: cutover, retire Plex | NOT STARTED | 1 hr |
| WP-159-06 | Document final state in Decisions log | NOT STARTED | 30 min |

---

## D-17-160: Goose media-ops recipe library

**Goal:** 5 production Goose recipes for media stack operations. Reduces manual checking.

**Depends on:** D-17-149 (Goose recipe library design — separate WBS)

**Acceptance criteria:**
- 5 recipes deployed under `~/.config/goose/recipes/` and version-controlled in repo at `goose-recipes/`
- Each recipe tested end-to-end with sample input
- Documented in `docs/runbooks/goose-media-recipes.md`

**Work packages:**

| WP | Description | Status | Est. |
|---|---|---|---|
| WP-160-01 | Recipe 1: `goose-arr-status-summary` — pulls Sonarr/Radarr/Lidarr queue + recent imports + recent errors, outputs Markdown brief | DESIGN DRAFT | 1 hr | spec at `goose-recipes/arr-status-summary.yaml` (2026-05-07 flight) |
| WP-160-02 | Recipe 2: `goose-arr-failed-imports-triage` — examines failed imports, categorizes by failure mode, drafts Plane tickets | DESIGN DRAFT | 1.5 hr | spec at `goose-recipes/arr-failed-imports-triage.yaml` (2026-05-07 flight) |
| WP-160-03 | Recipe 3: `goose-zabbix-incident-brief` — for media stack alerts (qBit unreachable, low disk, etc.) | NOT STARTED | 1 hr |
| WP-160-04 | Recipe 4: `goose-runbook-summarizer` — compresses any runbook into action brief | DESIGN DRAFT | 30 min | spec at `goose-recipes/runbook-summarizer.yaml` (2026-05-07 flight) |
| WP-160-05 | Recipe 5: `goose-plane-ticket-drafter` — free-form input → structured Plane ticket draft | NOT STARTED | 1 hr |
| WP-160-06 | All 5 tested with real data; pass/fail per recipe | NOT STARTED | 1 hr |
| WP-160-07 | Documentation runbook | NOT STARTED | 30 min |

---

## Sequencing recommendations

**Critical path (must be serial):**
D-17-153 (seedbox+qBit) → D-17-155 (paths) → D-17-156 (Recyclarr) → D-17-157 (music) + D-17-158 (audiobooks) in parallel → D-17-159 (Plex/Jellyfin) — 6 weeks elapsed if parallel pilots take 30 days each.

**Parallel tracks:**
- D-17-154 (sync hardening) starts as soon as D-17-153 WP-04 completes
- D-17-160 (Goose recipes) can start anytime; consumes data from D-17-155+ but design doesn't block
- D-17-159 (Plex decision) can be made while waiting on D-17-153 parallel run

**Suggested first session (next time at home):**
WP-153-01 → WP-153-02 → WP-153-03 → WP-153-04. About 90 minutes. After WP-04, you have throughput baseline and the seedbox is signed up. Everything else can resume from this state.

---

## Decisions log

(Append entries as decisions are made. Format: date | WP | decision | reasoning)

| Date | Reference | Decision | Reasoning |
|---|---|---|---|
| 2026-05-07 | D-17-153 | Whatbox NL chosen over Bytesized/Seedhost/Pulsed | $15/mo, AMS peering verified by community, native qBit, EU jurisdiction preserved, $5/mo headroom under $20 cap |
| 2026-05-07 | D-17-153 | Pilot order: Lidarr → Sonarr → Radarr | Music = smallest files, easiest rollback, separate from primary TV/movie queue |
| 2026-05-07 | D-17-154 | Default Syncthing, fallback Mullvad-on-QNAP | Same as current arch; only escalate if throughput fails |
| 2026-05-07 | D-17-160 | Goose recipe library v0.1: 3 specs drafted (arr-status, arr-failed-triage, runbook-summarizer) | Flight session productive design work; specs at `goose-recipes/*.yaml` ready for testing when home stack reachable |
| 2026-05-07 | D-17-153 | WP-01 through WP-04 runbook drafted with paste-ready commands | Pre-stage so first home session is execution-only, no decision-making mid-flight |
| | | | |

---

## Risk log

| Risk | Severity | Mitigation | Owner |
|---|---|---|---|
| Whatbox NL has same Comcast routing issue as Hetzner | HIGH | WP-153-01 ping test BEFORE signup | Adrian |
| qBit 5.2 incompatibility with arr-apps | MEDIUM | Pilot WP-07/08/09 in low-risk order; rollback to seedit4me |  Adrian |
| TRaSH path migration breaks active downloads | HIGH | Run after seedit4me cancellation; or pause torrents during migration window | Adrian |
| 30-day parallel cost ($25/mo total) | LOW | Acceptable, planned, time-bounded | Adrian |
| Plex migration to Jellyfin disrupts daily use | MEDIUM | 30-day parallel; Infuse covers both | Adrian |

---

## How to update this document

After completing any WP:
1. Update the WP row's `Status` column (`IN PROGRESS` → `DONE`)
2. Update the deliverable row in Master tracker if all WPs in that deliverable are done
3. Add to Decisions log if a decision was made during the WP
4. Add to Risk log if a new risk was discovered
5. Commit with message: `docs(D-17-NNN): WP-NNN-NN status update`
6. Surface back to project manager (Claude) for any course corrections

---

