# Brief D LAN-Session Plan — Phase 17 Closeout Finalization

**Author:** Claude Code (Opus 4.7, 1M context)
**Date:** 2026-05-11
**Repo state:** main HEAD `15793e24` (post-orchestration-rebuild-audit merge); branch `feat/phase-17-brief-d-plan` cut from this commit
**Plan home:** `docs/_planning/phase-17-brief-d-plan-2026-05-11.md`
**Frame:** Review material — not an executable brief. Per-WP executable briefs get drafted at LAN-session-open against fresh pre-flight reads of platform state.

**Anchors:**
- `docs/_audit/phase-17-closeout-audit-2026-05-11.md` (Criteria 2 + 4 + 8 LAN-gated; §6 operator Q-list; §7 risk register including F7 spot-check row)
- `docs/_audit/orchestration-layer-rebuild-audit-2026-05-11.md` (14 NOT-DELIVERED rows; 11 LAN-gated)
- `docs/PROJECT_FRAMEWORK.md` §9 (D-17-43/45/115 IN PROGRESS with Brief D carry-forward annotations)
- `docs/known-issues/{KI-010,KI-011,KI-012}-*.md` (close-paths documented)
- `docs/adr/ADR-A-014-netbox-cmdb-authority.md` (Status: Accepted 2026-04-30; NetBox is the declared CMDB authority)

---

## §1 Summary

Brief D is the LAN-gated execution context that finalizes Phase 17. Scope spans **9 work packages** (WP-D-01 through WP-D-09) covering closeout audit Criteria 2 + 4 + 8, D-17-115 Phase 2, KI-010/011 closure, F7 spot-check sweep, the 11 LAN-gated NOT-DELIVERED rows from the orchestration-rebuild audit, and the `phase-17-final` tag-cut.

This is a **plan, not a brief**: it enumerates work and dependencies for operator review and per-WP executable-brief authoring at LAN-session-open. No commands, no syntax, no execution-time pre-flight values — those belong in the per-WP briefs drafted when the operator confirms the LAN session is open.

Critical path: WP-D-01 (LAN reachability verification) gates everything; WP-D-08 (closeout criteria re-eval) + WP-D-09 (tag-cut) bracket the session close. Parallelizable mid-session block: WP-D-02 + WP-D-03 + WP-D-04 + WP-D-06 are independent once WP-D-01 is green. WP-D-05 and WP-D-07 have explicit upstream dependencies.

---

## §2 Prerequisites for LAN session open

Each prerequisite must be operator-verifiable before any WP-D-* executes. Per-WP briefs assume these are all green.

| # | Prerequisite | Verification surface (informational, not prescribed) |
|---|---|---|
| P1 | Operator physically on-LAN at home OR Headscale-connected to LAN | `tailscale status` returns logged-in state + reachable peers; OR LAN-direct ping to .145 |
| P2 | Mac Mini (`192.168.10.145`) reachable + ssh-authable | `ping` + `ssh` connectivity probe |
| P3 | Mac Studio (`192.168.10.142`) powered on + reachable + ssh-authable | `ping` + `ssh` connectivity probe; pre-Brief-D operator may need to wake-on-LAN |
| P4 | QNAP (`192.168.10.201`) reachable for NetBox + container-roster pulls | `ping` + Caddy-fronted `https://qnap.internal/` reachability |
| P5 | Caddy host (Mac Mini Docker `caddy` container) running and serving `*.internal` | `https://caddy.internal/` or any other `*.internal` domain probes 2xx/3xx (modulo trust-state before WP-D-02) |
| P6 | NetBox (`netbox.internal`) running and authenticated query path live | NetBox API token in Vault; UI loads; GraphQL/REST returns 200 for an `/api/dcim/devices/` probe |
| P7 | Operator decision gates Q1–Q5 (§3) resolved before WP-D-* execution begins | Operator updates this plan doc OR per-WP brief with explicit Q-answer before brief is dispatched |

**P3 nuance.** Mac Studio was physically delivered 2026-05-01 (D-17-15) but has NOT been joined to Headscale per KI-010 / CLAUDE.md L95. Headscale join itself is a Brief D pre-WP if Mac Studio has never been enrolled; not separated out as its own WP because it's atomic with WP-D-01 ("LAN reachability verification").

---

## §3 Decision gates — operator resolves BEFORE Brief D opens

Each gate maps to specific WPs. Recommended defaults are stated; operator may override.

| Q# | Decision | Recommendation | Affects WP | Rationale |
|---|---|---|---|---|
| Q1 | CMDB authority: re-affirm NetBox per ADR-A-014, or alternative? | **Re-affirm NetBox** — ADR-A-014 Status: Accepted 2026-04-30; the Phase 14 D-DOC commit `60aeb96` already flipped `CMDB_SOURCE` default to `netbox`. Re-affirmation is procedural | WP-D-05 + closes D-17-43/45 | The decision was made nine months ago; Brief D only needs the operator to confirm no architectural change has happened in the interim |
| Q2 | D-17-115 Phase 2 target hosts — Mac Mini + Mac Studio + MacBook, or different set? | **Mac Mini + Mac Studio + MacBook** (per D-17-115 row's stated Phase 2 plan) | WP-D-02 | The row explicitly names these three hosts; the operator-confirmation here is whether the trust-script has been tested on at least one host in advance and whether iOS/iPad/Apple TV/Android devices fold in as a stretch goal |
| Q3 | KI-011 surface post-vllm-mlx pivot — is the closure target still "move vllm-mlx to Mac Studio and run N=3-5 probe there", or has the model swap deprecated that ask? | **OPERATOR INPUT REQUIRED** — KI-011's closure procedure assumes vllm-mlx moves to Mac Studio; but operationally vllm-mlx is the MacBook-only off-LAN stunt-double (per LiteLLM Tier 2). If vllm-mlx stays on MacBook permanently, the N=3-5 probe runs on MacBook against MacBook vllm-mlx, not Mac Studio. Mac Studio Tier 3 separately runs Ollama with `qwen3-coder:30b-coding` (env-var-driven). Two viable readings; operator picks. | WP-D-03 | Reading A: KI-011 means "move vllm-mlx to Mac Studio and run probe there." Reading B: KI-011 means "run probe wherever vllm-mlx lives — that's MacBook, and the test can land in any session." LiteLLM config has Tier 2 (vllm-mlx, port 8500) and Tier 3 (Mac Studio Ollama, env-var-driven) as separate paths |
| Q4 | F7 spot-check sweep scope — full §18.O Goose-pipeline-authored DONE row sweep, or narrowed to the two committed cell-artifacts? | **Narrowed to the two committed artifacts** — `opnsense-dhcp-dns-push.md` (D-17-54 session 2, partially F7'd already; Brief C corrected to scope-revised) and `openproject-sync-and-enrich.md` (D-17-53 Session 9; the cell's only OTHER committed artifact). All Sessions 10/11/12/13 outputs were rejected (Posture 0 demotion); the cell is now Posture 0 SUSPENDED. Universe is small | WP-D-06 | Brief C precedent verified existence-level F7 (file claimed but not authored). Brief D F7 sweep should add citation-level verification (the deeper risk per D-17-53 chronicle — Sessions 11/12 fabricated source-citation line numbers in non-committed outputs; Session 9 was "likely a lucky draw" per sampling-artifact hypothesis). Spot-checking Session 9 artifact's citations is the natural F7 extension |
| Q5 | Phase 18 work bundling — does the tag-cut close the session, or does Phase 18 work bundle into the same on-LAN session? | **Tag-cut closes the session** — Brief D is already 3-5 hours of substantial work; bundling Phase 18 risks both incomplete Brief D and incomplete Phase 18 work. Operator may extend if WP-D-* run faster than estimated, but plan-default is single-purpose | WP-D-09 + post-tag scope | Bundling pressure to wrap-up Phase 17 should not push Phase 18 work to be hastily started in the same window; clean separation supports the closeout audit's integrity |

---

## §4 Work packages

Each WP carries: title, dependencies, scope summary, success criteria, gate references. **No prescribed command syntax** — that's session-time work for per-WP executable briefs.

### WP-D-01 — LAN reachability verification

- **Dependencies:** None (this is the gate-keeping WP for every other Brief D WP)
- **Scope:** Verify each prerequisite (P1–P7 in §2) is green from the LAN-session operator surface. Surface any prerequisite that fails. Verify operator-decision gates Q1–Q5 (§3) are resolved.
- **Success criteria:** All 7 prerequisites pass; all 5 decision gates have operator-confirmed answers recorded against this plan; per-WP brief drafting can proceed.
- **Gate references:** P1–P7 + Q1–Q5.
- **Failure handling:** If any prerequisite fails, surface the failure and STOP. Brief D does not advance from WP-D-01 until reachability is established. Mac Studio Headscale join may need to be a pre-WP if Mac Studio has never been enrolled.

### WP-D-02 — D-17-115 Phase 2: Caddy CA trust completion

- **Dependencies:** WP-D-01; Q2 resolution.
- **Scope per the existing D-17-115 row's Phase 2 plan:** extract Caddy CA cert via `docker exec` on Mac Mini; commit `deployment/caddy/internal-root.crt`; fill SHA-256 fingerprint and issuer DN placeholders in `docs/runbooks/caddy-internal-ca-trust.md`; run `scripts/caddy-ca-trust-macos.sh` on Mac Mini + Mac Studio + MacBook; verify `curl https://<test>.internal/` succeeds without `-k`; flip §9 D-17-115 status IN PROGRESS → DONE.
- **Success criteria:** Three macOS hosts trust Caddy CA without warnings; runbook fingerprint placeholders populated; row flipped to DONE.
- **Gate references:** Closeout audit §3.4 Criterion 4 partial unblock (TLS-trust prerequisite for NetBox API queries from MacBook); KI-012 (decade-horizon companion KI stays OPEN — not Brief D scope).

### WP-D-03 — KI-010 + KI-011 closure

- **Dependencies:** WP-D-01; Q3 resolution (KI-011 reading).
- **Scope:**
  - **KI-010:** run `scripts/verify-model-provenance.sh --hf Qwen/Qwen3-Coder-30B-A3B-Instruct` on Mac Studio (96 GB unified memory clears the BF16 fingerprint OOM that hard-stops on Tier 1/2). Expected verdict `verified-specific` or `verified-base-family`. Per-model JSON record overwritten; `docs/_provenance/backfill-2026-05-10.md` gets a "Promotion" subsection; integration test §9 line updated; KI-010 flipped to RESOLVED.
  - **KI-011 (per Q3):** Reading A — deploy vllm-mlx to Mac Studio with `--max-num-seqs 4`, run N=3-5 concurrent probe, capture results. Reading B — run N=3-5 probe on MacBook against MacBook vllm-mlx (the actual stunt-double host). Either reading: integration test §9 "Concurrent-load validation status:" line updated; KI-011 flipped to RESOLVED.
- **Success criteria:** Both KIs status OPEN → RESOLVED; close-out summaries appended; integration test §9 reflects new evidence.
- **Gate references:** Closeout audit §3.5 Criterion 5 (KI register triage — moves KI-010/011 from accept-as-deferred to resolved).

### WP-D-04 — D-17-01 v2 stack audit re-run

- **Dependencies:** WP-D-01.
- **Scope:** Re-run D-17-01 against current platform state.
  - Probe Mac Mini Docker daemon: `docker ps -a` + `docker images` + per-container config dump for the canonical roster.
  - Pull service-registry inventory from NetBox (`netbox.internal` GraphQL/REST) + cross-reference `~/.platform-registry/inventory.json` runtime cache + cross-reference `config/service-registry.yaml.DEPRECATED` (fallback only).
  - Compare against canonical Local AI Workstation Roadmap §2.1 target architecture + roadmap §3.2 known versions baseline.
  - Surface drift items: services running but not in registry; registry entries with no running container; version drift since 2026-05-06 roadmap baseline.
  - Identify any NEW "evaluated individually" findings (closeout audit Criterion 2 success criterion = zero such findings).
- **Success criteria:** `docs/_audit/stack-audit-v2-2026-05-MM.md` authored on branch (with the LAN-session date in the filename); drift surfaced for operator review; criterion-2 zero-new-findings check passes OR drift items are explicitly scoped to follow-on WPs.
- **Gate references:** Closeout audit §3.2 Criterion 2 closure WP-2.1.
- **Discovery vs corrective.** This WP is discovery only — corrections are downstream WPs (sub-WPs of WP-D-04 or escalations to Phase 18). Surfacing drift is the deliverable; fixing drift is out-of-scope for the criterion.

### WP-D-05 — NetBox vs container roster reconciliation

- **Dependencies:** Q1 resolution; WP-D-04 (stack audit data feeds this reconciliation).
- **Scope per Q1 resolution:**
  - **Re-affirm NetBox (default):** pull NetBox container/service inventory via API; reconcile against WP-D-04's `docker ps` output; surface delta. Close §9 D-17-43 + D-17-45 rows. Document the reconciliation in the same `stack-audit-v2-2026-05-MM.md` artifact OR a sibling `docs/_audit/netbox-container-reconciliation-2026-05-MM.md`.
  - **Alternative authority (override):** re-scope D-17-43/45 to the new authority surface; escalate to Phase 18 via CR-17-007 (new CR per closeout audit §7 risk register row).
- **Success criteria:** D-17-43/45 §9 rows flip to DONE (Q1 = NetBox path) OR get explicit re-scope annotation + Phase 18 CR (Q1 = alternative path).
- **Gate references:** Closeout audit §3.4 Criterion 4 closure WP-4.1.

### WP-D-06 — F7 spot-check sweep (per Q4 narrowed scope)

- **Dependencies:** WP-D-01; Q4 resolution.
- **Scope (Q4-narrowed):** spot-check the two committed §18.O Goose-pipeline-cell artifacts:
  - `docs/runbooks/opnsense-dhcp-dns-push.md` (D-17-54 session 2; already partially F7'd by Brief C — verify the remaining content is faithful to its source verification by operator).
  - `docs/runbooks/openproject-sync-and-enrich.md` (D-17-53 Session 9; the cell's other committed artifact; per chronicle, Session 9 was "likely a lucky draw" — Brief D should verify source-citation line numbers are not fabricated like Sessions 11/12 outputs were).
  - **Citation-level F7 check:** for each artifact's source citations (line-number references to scripts/config files), verify the cited content actually appears at the cited line. Sessions 11/12 fabricated such citations; Session 9 was passed as clean; Brief D re-verifies the pass.
  - **Path C corrective pattern** (per Brief C precedent): if a false-positive surfaces, descope to a new D-NN-MM Phase 18 row and update the §9 row with scope-revision annotation citing F7 + Brief D investigation.
- **Success criteria:** Both artifacts pass citation-level F7 spot-check OR false-positives are corrected via Path C. Audit doc §10.1 (F7 self-correction) updated with Brief D evidence.
- **Gate references:** Closeout audit §7 risk register row "F7 false-positive completion pattern (Brief C surfaced one in §9 D-17-54)..." with Brief D mitigation handoff.

### WP-D-07 — Orchestration-rebuild audit NOT-DELIVERED row resolution

- **Dependencies:** WP-D-01.
- **Scope:** address the 11 LAN-gated NOT-DELIVERED rows from `docs/_audit/orchestration-layer-rebuild-audit-2026-05-11.md` §5:
  - Roadmap WBS 2.1 Configure Thunderbolt Bridge (Mac Mini ↔ Mac Studio per errata E-003)
  - Roadmap WBS 2.3 Firewall Ollama (Mac Studio host-side)
  - Roadmap WBS 3.2 Mount QNAP artifact path (verify on Mac Mini)
  - Roadmap WBS 4.1 Install/update Ollama on Mac Studio (verify live; resnapshot inventory)
  - Roadmap WBS 5.1 Install OpenCode (home Mac Mini) — *optionally pre-Brief-D off-LAN per §6 cleanup option*
  - Roadmap WBS 5.5 Install Cline (VS Code extension visibility probe on Mac Mini)
  - Roadmap WBS 5.6 Install Continue (same)
  - Roadmap WBS 5.7 Install OpenHands (sandbox launch verification per spec §15.1)
  - Roadmap WBS 6.5 Configure Continue (gated on 5.6)
  - Roadmap WBS 6.6 Configure Cline (gated on 5.5)
  - Roadmap WBS 11.1 + 11.2 OpenCode A/B + Serena impact (gated on 5.1)
  - **WBS 5.5 Cline canonical-surface install on Mac Mini** — MacBook install landed off-LAN via Thread A WP-3 (extension `saoudrizwan.claude-dev` v3.82.0 confirmed installed; verified canonical per `docs/runbooks/foundation-install-status-track-2.md` Stage 3 + `https://github.com/cline/cline`); Mac Mini canonical-surface install (§1.2: "Mac Mini should run … Cline …") carries to this WP via `code --install-extension saoudrizwan.claude-dev`. Verify VS Code CLI (`which code` OR `/Applications/Visual\ Studio\ Code.app/Contents/Resources/app/bin/code`) is available on Mac Mini before issuing the install command.
- **Per-row disposition:** execute the missing work in-session OR re-scope to Phase 18 with explicit deferral note citing Brief D investigation date. Roadmap WBS 12.2 (v1 baseline tag) is WP-D-09, not WP-D-07.
- **Success criteria:** each of the 11 rows either landed-as-delivered OR explicitly carried to Phase 18 with a paper-trail annotation. Orchestration-rebuild audit §5 gap classification updated (or sibling audit-Brief-D-landing note appended) reflecting the disposition.
- **Gate references:** Orchestration-rebuild audit §5 + §7 risk register row "Track 2 install completeness mis-stated for Cline / Continue".
- **Scope-expansion risk.** 11 rows is the upper bound; per §7 risk register row (e), this WP may exceed time-budget. Per-row time-boxing recommended at brief-drafting.

### WP-D-08 — Phase 17 closeout criteria re-evaluation

- **Dependencies:** WP-D-04 + WP-D-05 + WP-D-06 + WP-D-07 satisfied.
- **Scope:** update `docs/_audit/phase-17-closeout-audit-2026-05-11.md`:
  - Append `§11 Brief D landing note` capturing per-WP outcomes + any Path C scope-corrections + any §9 row flips landed.
  - Re-evaluate Criterion 2 (stack audit re-run zero NEW findings) per WP-D-04 evidence.
  - Re-evaluate Criterion 4 (NetBox vs container roster) per WP-D-05 evidence.
  - Finalize 8-criterion scorecard: each criterion is either GREEN (satisfied) or YELLOW (satisfied-with-explicit-deferral per Brief C precedent).
  - Update §7 risk register: close mitigated rows, add any new risks surfaced during Brief D execution.
- **Success criteria:** 8-criterion scorecard either all-GREEN or all-explicit-on-deferrals; closeout audit doc updated with Brief D landing note + scorecard finalization + risk register reconciliation.
- **Gate references:** all 8 closeout audit §3.* criteria.

### WP-D-09 — `phase-17-final` tag-cut

- **Dependencies:** WP-D-08 satisfaction (scorecard finalized; all criteria green or explicitly-deferred).
- **Scope:** cut the `phase-17-final` tag with a comprehensive tag message citing the closeout chain — Brief A (`834eb86f`) + Brief B (`31345a0b`) + Brief C (`06a31741`) + Brief D (current HEAD) + the closeout audit doc + the orchestration-rebuild audit doc + the Brief D plan (this doc). Push the tag to origin.
- **Success criteria:** Tag `phase-17-final` exists locally + on remote; tag message references the closeout chain commits and audit deliverables; main HEAD at tag points to the Brief D merge commit.
- **Gate references:** Closeout audit §3.8 Criterion 8 closure WP-8.1.
- **Annotated tag.** Per established pattern: `git tag -a phase-17-final` with multi-paragraph message authored via heredoc; no `--force`; signed-tag policy per operator preference.

---

## §5 Sequencing graph

Dependency tree (root → leaves; parallel siblings share the same indent level):

```
WP-D-01 LAN reachability verification (gate-keeper)
   │
   ├─ WP-D-02 D-17-115 Phase 2 — Caddy CA trust completion
   │
   ├─ WP-D-03 KI-010 + KI-011 closure (Q3 dependency)
   │
   ├─ WP-D-04 D-17-01 v2 stack audit re-run
   │     │
   │     └─ WP-D-05 NetBox vs container roster reconciliation (Q1 dependency)
   │
   ├─ WP-D-06 F7 spot-check sweep (Q4 dependency)
   │
   └─ WP-D-07 Orchestration-rebuild NOT-DELIVERED resolution
         │
         (WP-D-04 + WP-D-05 + WP-D-06 + WP-D-07 all complete)
                  │
                  └─ WP-D-08 Closeout criteria re-evaluation
                              │
                              └─ WP-D-09 phase-17-final tag-cut
```

**Parallelization windows:**

| Window | Parallel WPs |
|---|---|
| Mid-session, post WP-D-01 | WP-D-02, WP-D-03, WP-D-04, WP-D-06 (all independent) |
| Post WP-D-04 | WP-D-05 starts (NetBox reconciliation consumes WP-D-04's stack-audit data) |
| Sequential close | WP-D-08 → WP-D-09 (criteria reval gates tag-cut) |

WP-D-07 (orchestration-rebuild NOT-DELIVERED resolution) can run anywhere post WP-D-01 but its time-box is variable, so plan-default sequences it AFTER WP-D-02/03/04/06 to avoid scope-expansion blocking the other LAN-gated WPs.

---

## §6 Off-LAN cleanup bundles (pre-Brief D options)

The orchestration-rebuild audit identified 3 off-LAN-executable items that could land BEFORE the LAN session opens. Two options for handling these:

**Option A — Pre-Brief-D off-LAN cleanup pass.** Author a separate Brief C.1 (or Brief D-pre) that lands these three items in the current off-LAN window, reducing Brief D's WP-D-07 scope from 11 rows to 8 rows:

1. Roadmap errata branch merge to main (`docs/local-ai-workstation-roadmap-errata` at `3efc27d5`) — single no-ff merge, no conflicts expected (greenfield file at `docs/architecture-facts/local-ai-workstation-roadmap-errata.md`).
2. OpenCode install target clarification (per orchestration-rebuild audit §7 risk register row "Errata E-002 unverified" — confirm install source URL ahead of WBS 5.1 install).
3. Cline + Continue VS Code extension state probe — can be done from any VS Code workspace operator opens; reportable in `LocalAIConfig/agents/{cline,continue}/README.md`.

**Option B — Fold into WP-D-07.** Leave these three items as part of WP-D-07's 11-row resolution scope; let Brief D handle them in-session.

**Recommendation tradeoff:** Option A reduces Brief D session length but adds another off-LAN brief overhead; Option B keeps the closeout sequence compact (4 briefs total: A/B/C/D) at the cost of WP-D-07 carrying more rows. Operator preference — surface for review; not blocking the plan as authored.

---

## §7 Risk register

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| a | Mac Studio still unreachable when LAN session opens (Headscale enrollment not done; wake-on-LAN fails; hardware issue) | LOW-MEDIUM | Most WPs blocked (WP-D-02 partially / WP-D-03 fully / WP-D-04 partially / WP-D-05 partially); session may need to abort post-WP-D-01 | Mac Studio Headscale enrollment becomes a pre-Brief-D operator-task; OR Brief D re-scoped to MacBook-only readings (KI-011 Reading B; Mac-Mini-only stack audit) |
| b | NetBox deployed at `docker/netbox/` but operational state unverified at LAN-open | LOW-MEDIUM | Q1 NetBox re-affirmation may need to defer until NetBox health is itself a Brief D pre-WP | NetBox health-check folded into WP-D-01 prerequisite P6; if NetBox is broken, escalate to Phase 18 via CR-17-007 |
| c | KI-011 target ambiguity post-vllm-mlx pivot (Q3) | MEDIUM | Q3 resolution may require operator input mid-session if not resolved pre-flight | Plan-default surfaces Q3 as REQUIRED pre-flight resolution (not deferred to in-session); operator answers Q3 before WP-D-03 brief drafts |
| d | F7 spot-check (WP-D-06) surfaces fabricated citations in `openproject-sync-and-enrich.md` (Session 9 cited as "likely a lucky draw") | LOW-MEDIUM | WP-D-06 scope expands; Path C scope-correction needed; phase-17-final tag delays | Per Brief C precedent — Path C scope-split is a well-rehearsed corrective action; doctrine response already chronicled in audit §10.1; tag-cut acceptable with explicit-deferral per Brief C precedent |
| e | Service registry build failure on Mac Mini (D-17-29 `~/.platform-registry/inventory.json` stale or absent) | LOW | WP-D-04 may need fallback to manual `docker ps` roster build; criterion-2 success still achievable but evidence chain weakens | Stack audit accepts either substrate (NetBox API or runtime registry); document substrate used in the v2 audit artifact |
| f | Brief D session length exceeds operator's available window (3-5 hour estimate may be optimistic if WP-D-07 has 11 rows + WP-D-06 surfaces F7) | MEDIUM-HIGH | Tag-cut slips to a follow-on session; closeout chain extends to Brief D + Brief D.1 | Plan defaults to NOT bundling Phase 18 work into the same session (Q5); per-WP time-boxing recommended at brief-drafting; WP-D-07 scope can be split across two LAN sessions if needed |
| g | Headscale control-server (`vpn.reivernet.com:8082`) unreachable from operator location at LAN-open (currently logged out per off-LAN MacBook probe) | LOW-MEDIUM | Operator can't connect to LAN via VPN; must be physically on-LAN at home for Brief D | Verify Headscale control-server health as part of P1 prerequisite; if down, Brief D requires physical home presence (LAN-direct) |
| h | Per-WP brief drafting at session-open consumes more time than allotted | MEDIUM | Plan-to-execution lag; session length grows | Pre-WP-* per-WP brief drafts may be authored during the operator's pre-flight check window; this plan is the substrate for those drafts |

---

## §8 Estimated session shape

Time-block sketch (estimates only; actual times depend on Mac Studio rejoin smoothness, NetBox reachability, and F7-surface count):

| Block | WPs | Estimated duration | Notes |
|---|---|---|---|
| 1 | WP-D-01 (LAN reachability verification + Q-gate confirmations) | ~10 min | Gate-keeper; serialized first |
| 2 | WP-D-02 + WP-D-03 + WP-D-06 (parallel: Caddy CA trust + KI-010/011 closure + F7 spot-check) | ~60–90 min | All independent post WP-D-01; vllm-mlx probe is the slowest if Reading A picked for Q3 |
| 3 | WP-D-04 (stack audit re-run) | ~30 min | Can run in parallel with block 2 if operator capacity permits |
| 4 | WP-D-05 (NetBox vs container reconciliation) | ~30 min | Gated on WP-D-04 + Q1 |
| 5 | WP-D-07 (orchestration-rebuild NOT-DELIVERED resolution) | ~60–120 min | Variable; depends on 11-row in-session vs Phase-18-defer split |
| 6 | WP-D-08 (closeout criteria re-eval) | ~15 min | Doc update only |
| 7 | WP-D-09 (phase-17-final tag-cut) | ~5 min | If WP-D-08 scorecard finalized |

**Total estimated session length:** 3.5–5 hours. Phase 18 work bundling NOT recommended in the same session (Q5 default).

---

## §9 Open questions deferred from plan-authoring

These are surfaced for operator review; they do NOT block the plan as authored.

| # | Question | Comment |
|---|---|---|
| OQ-1 | Pre-Brief-D off-LAN cleanup brief — Option A vs Option B (per §6)? | Operator preference; affects Brief D session length and WP-D-07 scope |
| OQ-2 | Sub-plan needed for WP-D-04 or WP-D-07 (highest-complexity WPs)? | WP-D-04 has a known shape (stack-audit re-run is a discovery task with bounded outputs). WP-D-07 has 11 rows of variable complexity; a sub-plan could improve per-row time-boxing if the operator anticipates needing it |
| OQ-3 | Is `docs/_planning/` the right home for this artifact, or should it live elsewhere (e.g., `docs/_audit/`, `docs/phase-17/`)? | `docs/_planning/` is the conventional home per the plan-not-brief framing. Alternatives: `docs/_audit/phase-17-brief-d-plan-2026-05-11.md` (audit-doc neighborhood) or `docs/phase-17/d-17-closeout/brief-d-plan-2026-05-11.md` (phase-deliverable neighborhood). No strong precedent in the repo — this is the first plan artifact in `docs/_planning/` |
| OQ-4 | Brief D commit-and-merge cadence — one merge per WP (A/B/C-style atomic) or one merge for the entire LAN session? | Per-WP atomic merges align with closeout chain pattern (Brief A/B/C each merged separately); single-merge reduces churn but loses audit anchor granularity. Plan-default: per-WP atomic merges, mirroring the established pattern |
| OQ-5 | Should this plan-doc itself be referenced from the closeout audit `§11 Brief D landing note` at session close, or only the WP-D-* commits? | Plan-default: cite both the plan-doc anchor + the per-WP commit SHAs; preserves the closeout chain integrity for future archaeology |

---

## End of plan

Plan-not-brief. Per-WP executable briefs get drafted at LAN-session-open against fresh pre-flight reads of platform state. Decision gates Q1–Q5 (§3) must resolve before WP-D-* brief drafting begins. Off-LAN cleanup (§6) is operator-optional. Tag-cut WP-D-09 closes the session; Phase 18 work bundled separately (Q5 default).
