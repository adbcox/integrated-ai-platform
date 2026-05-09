# Full Upgrade Master Project Plan — 2026-05-09

**Status:** AUTHORED (branch `feat/full-upgrade-master-plan`)
**Date:** 2026-05-09 (Tokyo, pre-Singapore)
**Scope:** The entire current upgrade — hardware migration + software/AI/agent layer + cross-track sequencing — as ONE coordinated project plan
**Supersedes (in scope, not in detail):** `runbooks/d-17-211-master-project-plan.md` (hardware-only), `_audit/travel-doable-work-2026-05-08.md` (trip subset only), `architecture-facts/2026-05-08-platform-unified-architecture.md` (mapping only)

## Why this plan exists

Three prior planning artifacts each captured one slice:
- D-17-211 master project plan codifies the hardware migration with phases A-F + follow-ons G/H/I
- Platform unified architecture maps software surfaces to hardware organs (placement, not sequencing)
- Travel-doable backlog enumerates parallel work usable while operator is away from home

None of those is the merged sequenced upgrade plan covering BOTH tracks as one coordinated effort. That gap caused scope drift during the 2026-05-08 Tokyo session — work advanced on each track independently without a single source of truth for cross-track dependencies and ordering. This document is that single source of truth.

## Scope statement

**In scope:** all work currently committed across the upgrade initiative —
- Track A: hardware migration onto MS-01 converged appliance (D-17-211 family)
- Track B: software/agent/AI surface evolution (LocalAIConfig codification, T1-T4 locked roadmap progression, RSS systems D-17-136/137, article-intake protocol + Sakana Conductor-pattern POC, §33 backlog sweep, MacBook M5 parity / Block 3)
- Cross-track: master log artifact ingest, doctrine refresh, follow-on integrations (Service Registry MVP, NetBox)

**Explicitly out of scope** (separate operational tracks; do not pull in):
- D-17-MEDIA media stack work (D-17-153 through D-17-160) — separate operational track on `travel/2026-05-07/...` branch
- Pre-existing in-flight deliverables not connected to the upgrade (e.g. D-17-46 Scraparr metrics, D-17-114 Plex client verification)
- Phase 18 unrelated work
- New deliverables not yet in PROJECT_FRAMEWORK.md §9

**Caveat on completeness:** this plan is authored from the artifacts in the integrated-ai-platform repo plus the operator's locked-roadmap memory entries. It does NOT yet incorporate the master log content (still PENDING-OPERATOR-INGEST). When the master log lands on QNAP and is xindex-consultable, this plan should be reviewed for additions.

## Two tracks, one project

```
TRACK A — Hardware (home-only execution; mostly serial; gates Phase B/E/F)
  Pre-flight (P-01..11, operator-owned)
        ↓
  Phase A — Hypervisor + OPNsense migration  (G0, G1)
        ↓
  Phase B — Linux VM + service migration  (G2)
        ├──→ Phase C — Thunderbolt segment  (parallel)
        ├──→ Phase D — Pi monitoring  (parallel)
        ↓
  Phase E — Decommissioning
        ↓
  Phase F — Doctrine + audit refresh  (PROJECT A COMPLETE)
        ↓
  Follow-ons: Phase G (Service Registry × OPNsense API), Phase H (NetBox)


TRACK B — Software / Agent / AI surface (mostly travel-doable design; deploy gated on Track A milestones)

  B1 — MacBook parity (Block 3) + LocalAIConfig codification
        Status: DONE in stages 2026-05-07/08; ongoing maintenance
        Includes: Aider/Goose/OpenCode/Cline/Continue/Serena/OpenHands
        config templates already authored (see /Users/adriancox/LocalAIConfig/agents/)

  B2 — Coding agent stack replacement  (v3 master plan core correction)
        ARCHITECTURAL INTENT (v3 master plan §0): the target is NOT
        "Aider + helpers." It is a local open-source agent stack with
        clear authority boundaries. Aider is the baseline-to-beat,
        NOT the permanent center. Multi-component evaluation and
        deployment, not a single tool swap.

        Components (v3 §5):
        B2.1 — OpenCode  (PRIMARY Claude Code-style terminal candidate; v3 §5.1, §7)
              Status: config codified in LocalAIConfig; evaluation NOT done
              Decision: replace Aider as primary terminal coding lane if OpenCode beats it on benchmark
        B2.2 — Goose  (broad workstation / Aether agent; v3 §5.2, §8)
              Status: installed + configured; used minimally
              Decision: broad workstation agent for non-coding agentic tasks
              Note: locked roadmap T3 frames this as "Goose adoption" — that is ONE component of B2, not the whole sub-track
        B2.3 — Aider  (current baseline + fallback; v3 §5.3, §6)
              Status: ACTIVE CENTER currently; explicit decision is "do not delete, do not destination, baseline-to-beat"
              Decision: keep until OpenCode (or another tool) beats it
        B2.4 — Cline  (IDE-supervised autonomous lane; v3 §5.4)
              Status: config codified; not deployed
        B2.5 — Continue  (IDE helper, autocomplete, checks lane; v3 §5.5)
              Status: config codified; not deployed
        B2.6 — Serena MCP  (semantic code intelligence tool layer; v3 §5.6)
              Status: config codified; not deployed
        B2.7 — OpenHands  (sandboxed full-project autonomy lane; v3 §5.7)
              Status: config codified; not deployed
        B2.8 — Verifier artifacts  (judge layer; v3 §0)
              Status: existing benchmark substrate (D-17-126 multi-file orchestration, D-17-129 codex51 campaign, D-17-XXX RAG context pack) plays this role
              Decision: extend benchmark suite to evaluate B2.1-B2.7 head-to-head against Aider baseline

        Critical conclusion: B2 is an EVALUATION + MIGRATION sub-track, not an "add Goose" item. The benchmark substrate (B2.8) decides which components advance to active deployment.

  B3 — Model layer (locked T1-T4 roadmap)
        T1 — System Prompt Library + Cisco Provenance Kit
              Status: DONE (D-17-122 closed Cisco; System Prompt Library committed)
        T2 — Model upgrade benchmark (Gemma 4 vs Qwen3-Coder-Next)
              Status: NOT STARTED; gates T3-locked-roadmap and T4
              Note: T2 selects MODELS that B2 components consume; B2 evaluation can proceed against current models, but switching primary model affects B2 results
        T3 (locked roadmap framing) — Goose adoption
              Status: this is B2.2 in agent-stack framing; cross-reference, not duplicate
        T4 — exo distributed inference (Mac Mini Pro + Mac Studio MLX pool)
              Status: GATED on T2 + macOS 26.2 on both Macs

  B4 — RSS systems (codified 2026-05-08)
        D-17-136 — Technical Intelligence RSS  (IN PROGRESS, PENDING-OPERATOR-INGEST)
        D-17-137 — Personal Briefing Engine    (IN PROGRESS, PENDING-OPERATOR-INGEST)
        Status: design substrate locked; deploy gated on Track A Phase B (Linux VM available)

  B5 — Article intake protocol + Conductor-pattern POC
        Article intake protocol: DONE (committed on feat/d-17-211-rearchitecture)
        Sakana evaluation: DONE; verdict adopt-pattern-not-implementation
        Conductor-pattern POC: NOT STARTED; gated on B3.T2 outcome (orchestrator model decision) and B2 evaluation (which agent surface routes Conductor decisions)

  B6 — §33 master log backlog sweep
        Status: DONE on chore/master-log-backlog-sweep-v2 (15 entries appended; 1 duplicate skipped)


CROSS-TRACK
  Master log artifact ingest (D-17-37/D-17-39 substrate)
        Status: PENDING-OPERATOR-INGEST; requires QNAP mount on macmini (home presence)

  Doctrine refresh waves
        Wave 1: after Track A Phase F (CLAUDE.md, PROJECT_FRAMEWORK.md, dependency graph)
        Wave 2: after B2.T2 outcome (system prompts + routing rules updated)
        Wave 3: after B3 RSS deploy (article intake doctrine becomes operational)
```

## Critical path across both tracks

The single critical path through the project:

```
Pre-flight  →  A  →  B  →  E  →  F  =  PROJECT COMPLETE (hardware side)
                    ↑
              B4 RSS deploy can land
              after Phase B (Linux VM ready)

B3.T2 model benchmark can start any time (Mac Studio independent of MS-01)
B2 agent stack evaluation can start any time (LocalAIConfig already configured)
B3.T4, B5 Conductor POC gate on B3.T2 outcome
B2 component selection cross-influences B3.T2 (preferred agent may favor specific model traits)
```

**Why this is the critical path:** Track A is the only one with hard sequencing constraints (Phase A bridges through OPNsense for Phase B; Phase E retires services that Phase B migrated; Phase F documents the final state). Track B has parallelism — T2 benchmark, B3 RSS design, B5 §33 sweep, etc. can all advance independently. The longest unavoidable chain is Track A.

**Cross-track gates that matter:**
- Master log ingest is gated on QNAP mount = home presence (any time operator is home; not strictly Phase A/B). TWO master logs need ingestion: `integrated_ai_workstation_complete_master_log.md` (Track B sources for §16, §17, §32, §33) AND `local_claude_code_replacement_architecture_master_v3.md` (Track B2 source-of-truth for the agent stack architecture).
- B4 RSS deploy is gated on Track A Phase B (Linux VM substrate)
- B2 agent stack components: each can be evaluated independently against Aider baseline; deployment gating depends on B2.8 verifier results, not on hardware
- B3.T4 (exo) + B5 Conductor POC are gated on B3.T2 outcome (not on hardware)
- B2 evaluation result MAY change B3.T2 criteria (different agents stress different model traits)


## Phase-by-phase sequenced execution

Each numbered phase is a coordinated unit of work across BOTH tracks. The phase numbers below are project-level (not WBS phases inside Track A). Within each project phase, work happens on multiple branches.

### Project Phase 0 — Current state (DONE / IN PROGRESS as of 2026-05-09)

**Track A:**
- Pre-flight items P-01..11 NOT STARTED (operator-owned; gates Phase 1)
- All architecture artifacts (8 files) authored on `feat/d-17-211-rearchitecture` (5 commits)
- Master project plan authored

**Track B:**
- B1 LocalAIConfig codification: DONE (2026-05-07, two commits on LocalAIConfig main)
- B1 MacBook parity: DONE (Aider/Goose/Ollama/CONVENTIONS/ctags/aider-conf all in place)
- B2.T1 Cisco Provenance Kit: DONE (D-17-122)
- B2.T1 System Prompt Library: DONE (committed; system-prompts tier docs in repo)
- B3 RSS systems codified: D-17-136 + D-17-137 IN PROGRESS on `feat/rss-intelligence` (2 commits with substrate doctrine + framework rows + ChatGPT pipeline corrections)
- B4 Article intake protocol: DONE (committed on `feat/d-17-211-rearchitecture`)
- B4 Sakana RL Conductor evaluation: DONE (verdict captured)
- B5 §33 backlog sweep: DONE (`chore/master-log-backlog-sweep-v2`, 15 entries + 1 duplicate skipped)

**Cross-track:**
- Master log staged at `/Users/adriancox/Downloads/integrated_ai_workstation_complete_master_log.md` — PENDING-OPERATOR-INGEST

**Travel-doable design work that COULD advance Phase 0 further before Phase 1 begins:**
- D-17-136 + D-17-137 design WPs (feed list curation, scoring rubric, sink decision, aggregator pick — all design-only)
- Visualization refresh of `docs/dashboards/{logical-service-architecture,physical-architecture}.html`
- Strategic-watch + candidate-tools post-sweep review
- Additional small `bin/` utilities (pattern proven by `branch-summary.sh`)

### Project Phase 1 — Hardware Phase A (operator at home)

**Trigger:** operator schedules maintenance window with Pre-flight P-01..11 verified

**Track A work:**
- Phase A — Hypervisor + OPNsense migration per `runbooks/d-17-211-convergence-migration.md`
- Output: MS-01 running Proxmox VE + OPNsense VM as the active network edge
- Gates: G0 (pre-flight clean) → G1 (OPNsense VM == active edge)
- Risks: R-A-01..R-A-04 from D-17-211 risk register

**Track B parallel work:**
- B2.T2 model benchmark CAN start NOW (Mac Studio is independent of MS-01)
  - Pull Gemma 4 (E4B + 26B MoE + 31B Dense variants), benchmark on Mac Studio
  - Pull Qwen3-Coder-Next (80B hybrid-attn + MoE), benchmark on Mac Studio
  - Comparison criteria: SWE-Bench, SecCodeBench, latency at Mac Studio precision, fit for orchestrator vs coder roles
  - This benchmark does NOT require Linux VM substrate; uses existing Ollama on .142

**Cross-track:**
- Master log ingest is the FIRST cross-track action operator can take when home — does not depend on Phase A. Recommend: run `scripts/roadmap-create.sh` for D-17-136 BEFORE starting Phase A maintenance window. Closes B3 PENDING-OPERATOR-INGEST status.

### Project Phase 2 — Hardware Phase B (operator at home, follows Phase 1)

**Trigger:** Gate G1 closed (Phase A complete, OPNsense VM proven active edge)

**Track A work:**
- Phase B — Linux VM + service migration
- Vault relocation Mac Mini Pro → MS-01 Linux VM (per `decision-records/D-17-213`)
- Headscale relocation to MS-01 Linux VM
- arr-stack migration onto MS-01 Linux VM
- All extended services (OpenProject, Nextcloud, all UI surfaces) onto MS-01 Linux VM
- Output: substrate consolidated; Mac Mini Pro Docker stack ready to retire (Phase E)
- Gate: G2 (Vault on MS-01, arr-stack tests pass, Mac Mini services dormant)
- Risks: R-A-05..R-A-09

**Track B parallel work:**
- B2.T2 benchmark continues (independent)
- B3 RSS systems can NOW DEPLOY onto MS-01 Linux VM substrate as soon as Phase B clears
  - Aggregator (Miniflux preferred) container
  - Python fetcher job
  - SQLite metadata store
  - QNAP raw archive mount integration
  - Ollama summarization route via litellm-gateway
  - OpenProject WP sink for D-17-136 technical digest
  - Operator decides D-17-137 sink (Obsidian / Nextcloud / email — open KI)

### Project Phase 3 — Hardware Phase C and D (parallel after Phase 2)

**Trigger:** Phase B stable for ~24-48 hours

**Track A work:**
- Phase C — Thunderbolt segment cabling
  - MS-01 USB4 #1 → QNAP TB4 (~40x improvement for arr-stack NFS)
  - Mac Studio TB5 daisy chain
  - 172.20.20.0/24 IP plan
  - mDNS reflection across segments
- Phase D — Pi monitoring tier
  - Pi 5 8GB acquisition + setup
  - Zabbix server migration onto Pi 5
  - Single-zone monitoring per circulatory doctrine

**Track B parallel work:**
- B3 RSS systems: initial production runs and tuning (post-deploy)
- B2.T2 benchmark continues if not yet complete
- B4 Conductor-pattern POC design completes (assumes T2 winner picked by Phase 3)

### Project Phase 4 — Hardware Phase E (decommissioning)

**Trigger:** Phase B services validated stable for ~7 days

**Track A work:**
- Phase E — Decommissioning per Finding 9 sub-doctrine
  - Mac Mini Docker stack retire
  - SMB mount retire (cross-host Docker pattern → QNAP-host pattern)
  - Docker Desktop retire
  - Mac Mini sleep enable (resolves D-17-213 always-on contradiction)
  - Protectli FW4B → cold spare
- Risks: R-A-10..R-A-13

**Track B parallel work:**
- B2.T2 benchmark: should be COMPLETE by this phase; T2 outcome locked
- B2.T3 Goose decision based on T2 outcome (adopt vs reject)
- B4 Conductor-pattern POC implementation begins (using T2 orchestrator winner)

### Project Phase 5 — Hardware Phase F (doctrine + audit)

**Trigger:** Phase E complete, all services running on new substrate, old substrate retired

**Track A work:**
- Phase F — Doctrine + audit refresh
  - CLAUDE.md updated (new orchestration host, new substrate paths, etc.)
  - PROJECT_FRAMEWORK.md updated (status of all migrated deliverables)
  - dependency-graph.md updated (74-service graph reflects new placements)
  - All affected doctrines updated (12 doctrines listed in unified architecture doc)
- Output: PROJECT A COMPLETE (hardware track)

**Track B parallel work:**
- B2.T3 Goose adoption (or rejection) — full implementation begins
- B2.T4 exo distributed inference — DECISION POINT (gated on macOS 26.2 status both Macs + T2 outcome)
  - If macOS 26.2 not yet available: defer T4
  - If available + T2 picks model that benefits from extended pool: deploy exo
- B4 Conductor-pattern POC implementation completes
- B3 RSS systems: stable production; article intake protocol applied to incoming feed candidates

### Project Phase 6+ — Follow-ons

**Track A follow-ons (separate scheduling, no critical-path impact):**
- Phase G — Service Registry MVP × OPNsense API automation integration
- Phase H — NetBox CMDB × physical-architecture integration
- Phase I (legacy framing): T1-T4 follow-on work — superseded by Track B in this merged plan

**Track B mature operations (steady state):**
- Continuous strategic-watch / candidate-tools maintenance (every new article evaluated per protocol)
- Periodic re-benchmark of model winners as new releases land
- B3 RSS systems generate WPs autonomously; operator triages


## Travel-doable subset (where Phase 0 work can advance during travel)

The full plan above defines six numbered project phases. While operator is away from home, **only Project Phase 0 advances** — and within Phase 0, only the design / spec / authoring work, not deployment. See `_audit/travel-doable-work-2026-05-08.md` for the detailed travel-doable backlog. Summary of what travel can ship:

| Track | What ships during travel | What does NOT ship |
|---|---|---|
| A | Architecture artifacts (DONE), master project plan (DONE), this merged plan (in progress) | Pre-flight P-01..11 all home-only |
| B1 | LocalAIConfig maintenance, MacBook utility scripts (e.g. `bin/branch-summary.sh` proof) | None (B1 is steady-state on MacBook) |
| B2.T1 | Already DONE | n/a |
| B2.T2 | Benchmark planning (criteria, tasks, scoring rubric) | Actual benchmark runs (need Mac Studio = home network or Tailscale tunnel) |
| B2.T3 | Goose recipe design refinements | Implementation gated on T2 outcome anyway |
| B2.T4 | macOS 26.2 release-watch entry maintenance | Implementation gated on macOS + T2 |
| B3 | Design WPs (feed list curation, scoring rubric, sink decision, aggregator pick), substrate doctrine refinements | Deploy gated on Phase 2 (Linux VM substrate) |
| B4 | Conductor-pattern POC design refinements, article-intake-protocol applications | Implementation gated on T2 outcome |
| B5 | DONE on chore/master-log-backlog-sweep-v2; review work travel-doable | n/a |
| Cross-track | Doctrine drafts, this merged plan, additional `bin/` utilities | Master log ingest is home-only |

**Recommended travel ordering** when operator is in Singapore (post-arrival, after rest):
1. Review / merge `chore/master-log-backlog-sweep-v2` to main (low cognitive)
2. Run `bin/branch-summary.sh` and start using it as a daily ops surface
3. D-17-153 design-complete (NOT in this plan's scope — separate D-17-MEDIA track but travel-doable; mention to keep momentum)
4. Visualization refresh
5. RSS feeder design WPs (concrete deliverable scope; produces durable artifacts)

## Risk register (cross-track)

### Track A risks (from D-17-211 plan, abbreviated)
- **R-A-01** Hypervisor selection wrong (Proxmox vs alternative) — mitigation: Proxmox VE proven at scale, broad community
- **R-A-02** OPNsense XML restore corruption — mitigation: P-02 export verified before Phase A
- **R-A-03** Vault sealed during migration — mitigation: P-03 raft snapshot + recovery key validated
- **R-A-04** OPNsense plugin incompatibility (os-caddy vs os-haproxy fallback) — mitigation: feature parity tested in Phase A; fallback path exists
- **R-A-05..R-A-13** see `runbooks/d-17-211-master-project-plan.md` for full set

### Track B risks (new, not previously enumerated)
- **R-B-01** T2 benchmark picks model that doesn't fit RTX 4070 12GB constraint — mitigation: benchmark scenarios include precision/quantization variations; fallback to existing T1 stack acceptable
- **R-B-02** Goose authority model conflicts with operator's existing Aider workflow — mitigation: T3 adoption decision can be REJECT if T2 winner doesn't slot in cleanly; recipes can be implemented for whatever orchestrator wins
- **R-B-03** RSS systems generate noise faster than operator can triage — mitigation: scoring rubric (D-17-137) prioritizes; OpenProject sink (D-17-136) batches into WPs reviewable on operator schedule
- **R-B-04** Master log §16/§17 references stale platform components beyond what unified architecture caught — mitigation: review pass on master log post-ingest; doctrine refresh wave 2 catches stragglers
- **R-B-05** exo (T4) requires Thunderbolt 5 mesh that hardware Phase C doesn't deliver — mitigation: T4 GATED on macOS 26.2 + T2; deferred until Phase 6+; topology re-evaluation point built into gate
- **R-B-06** Operator branch-hygiene issues with local model (twice observed: Aider committing to wrong branch) — mitigation: operator cuts branches manually before invoking Aider; longer-term `bin/aider_on_branch.sh` wrapper
- **R-B-07** B2 agent stack evaluation reveals that Aider remains best-in-class for the operator's specific workload, contradicting v3 master plan's "Aider not the destination" framing — mitigation: v3 framing is "baseline-to-beat," not "must replace"; if Aider wins benchmarks, the conclusion is "no replacement merited yet," which is a valid outcome. Re-evaluate when significant new agent versions land.
- **R-B-08** B2 components proliferate (7 distinct agents, 7 config files, multiple deployment lanes) creating maintenance burden that exceeds productivity gain — mitigation: stage deployment; only deploy components that win their lane in benchmark; Aider stays as fallback.
- **R-B-09** OpenCode evaluation requires significant operator time investment; benchmark substrate may not measure what matters for operator workflow — mitigation: extend benchmark suite (B2.8) before declaring B2.1 winner; subjective operator evaluation is also valid signal.

### Cross-track risks
- **R-CT-01** Master log ingest reveals decisions that contradict already-codified D-17-NNN entries — mitigation: this plan caveats (Phase 0 status: caveat on completeness section above); doctrine refresh wave addresses systematically
- **R-CT-02** Doctrine refresh after Phase F finds drift in 12+ doctrines — mitigation: Phase F is explicitly scoped for this; risk is timeline, not correctness
- **R-CT-03** Track B work piles up while Track A blocks at home — mitigation: Track B has parallelism; this plan documents which sub-tracks can advance independently
- **R-CT-04** Plan itself drifts from execution reality if not maintained — mitigation: Phase F doctrine refresh wave includes updating this document; living document, not freeze-once

## Knowledge items (cross-track open decisions)

### Track A (from D-17-211 plan)
- **KI-A-01** through **KI-A-10** — see `runbooks/d-17-211-master-project-plan.md` (operator presence schedule, hypervisor confirmation, Caddy plugin choice, Pi 5 sourcing, etc.)

### Track B (newly enumerated)
- **KI-B-01** T2 benchmark winner criteria (single number, multiple weighted dimensions, or operator subjective?)
- **KI-B-02** D-17-137 Personal Briefing Engine output sink (Obsidian / Nextcloud / daily email / markdown — operator preference open)
- **KI-B-03** Goose recipe implementation priority order (5 specs DESIGN COMPLETE; which to implement first if T3 adopts)
- **KI-B-04** Conductor-pattern POC initial task selection (which agentic flows are highest leverage)
- **KI-B-05** Aggregator pick: Miniflux vs FreshRSS (operator preference; default Miniflux per substrate doctrine)
- **KI-B-06** RSS feed list curation completion criteria (operator-curated initial list size; operator-judged sufficiency)
- **KI-B-07** B2 agent stack evaluation order — which component first? Recommended: OpenCode head-to-head vs Aider on D-17-126 multi-file orchestration suite (because v3 §0 names OpenCode as primary candidate). Alternative: Goose first if operator wants broad workstation agent ahead of coding-tool replacement.
- **KI-B-08** B2.8 verifier extension scope — does the existing benchmark suite (recurrence_rate, multi_file_orchestration metrics from D-17-126) measure what matters for OpenCode vs Aider comparison, or do we need new benchmark dimensions (planning quality, recovery rate, artifact quality)?
- **KI-B-09** v3 master plan ingest decision — should the v3 plan get its own D-17-NNN deliverable for ingest tracking (parallel to D-17-136), or is it covered by a B2 master deliverable? Recommended: new D-17-NNN at next operator-prompt opportunity, since it is its own source-of-truth document distinct from the integrated_ai_workstation log.

### Cross-track
- **KI-CT-01** When to ingest master log — pre-Phase A (recommended) vs post-Phase B (when QNAP substrate stable)
- **KI-CT-02** Whether to merge chore/master-log-backlog-sweep-v2 to main now or hold for Phase F doctrine refresh wave
- **KI-CT-03** Branch consolidation strategy — keep all six current branches or merge non-active back to main periodically

## Status snapshot — current state of every track (as of 2026-05-09)

| ID | Track | Sub-track | Status | Branch |
|---|---|---|---|---|
| D-17-211 | A | Hardware migration | PLAN AUTHORED, EXECUTION GATED ON HOME PRESENCE | feat/d-17-211-rearchitecture |
| LocalAIConfig | B1 | MacBook parity | DONE 2026-05-07 | (separate repo) |
| Agent config templates (7) | B1 | configs | DONE — codified for opencode/goose/aider/cline/continue/serena/openhands | (LocalAIConfig/agents/) |
| B2.1 OpenCode (primary candidate) | B2 | agent stack | CONFIG DONE; EVALUATION NOT STARTED | (LocalAIConfig) |
| B2.2 Goose (broad workstation) | B2 | agent stack | INSTALLED + CONFIGURED; minimal use; D-17-160 recipe specs DESIGN COMPLETE | travel/2026-05-07/... |
| B2.3 Aider (baseline-to-beat) | B2 | agent stack | ACTIVE CENTER currently; explicit decision NOT to delete | main |
| B2.4 Cline (IDE-supervised lane) | B2 | agent stack | CONFIG DONE; not deployed | (LocalAIConfig) |
| B2.5 Continue (IDE helper) | B2 | agent stack | CONFIG DONE; not deployed | (LocalAIConfig) |
| B2.6 Serena MCP (semantic intel) | B2 | agent stack | CONFIG DONE; not deployed | (LocalAIConfig) |
| B2.7 OpenHands (sandboxed autonomy) | B2 | agent stack | CONFIG DONE; not deployed | (LocalAIConfig) |
| B2.8 Verifier substrate | B2 | benchmark | EXISTS (D-17-126, D-17-129, D-17-XXX); needs B2 head-to-head extension | main |
| B3.T1 System Prompt Library | B3 | T1 model layer | DONE | main |
| D-17-122 Cisco Provenance Kit | B3 | T1 model layer | DONE | main |
| B3.T2 Model upgrade benchmark | B3 | T2 model layer | NOT STARTED — gates T3-locked, T4 | n/a yet |
| B3.T4 exo distributed inference | B3 | T4 model layer | RESEARCH ONLY; GATED on macOS 26.2 + T2 | n/a |
| D-17-136 Technical Intelligence RSS | B4 | RSS systems | IN PROGRESS, PENDING-OPERATOR-INGEST | feat/rss-intelligence |
| D-17-137 Personal Briefing Engine | B4 | RSS systems | IN PROGRESS, PENDING-OPERATOR-INGEST | feat/rss-intelligence |
| Article intake protocol | B5 | protocol | DONE | feat/d-17-211-rearchitecture |
| Sakana RL Conductor evaluation | B5 | protocol | DONE; verdict adopt-pattern | feat/d-17-211-rearchitecture |
| Conductor-pattern POC | B5 | implementation | NOT STARTED — gated on B3.T2 outcome AND B2 evaluation | n/a yet |
| §33 backlog sweep | B6 | sweep | DONE (15 added, 1 dup) | chore/master-log-backlog-sweep-v2 |
| integrated_ai_workstation master log ingest | Cross-track | substrate | PENDING-OPERATOR-INGEST | n/a (D-17-37 substrate) |
| v3 master plan ingest | Cross-track | substrate | PENDING-OPERATOR-INGEST (NEW — needs D-17-NNN ID) | n/a (D-17-37 substrate) |
| Doctrine refresh waves | Cross-track | doctrine | NOT STARTED | n/a |
| Service Registry × OPNsense API | Follow-on | Phase G | NOT STARTED | n/a |
| NetBox × physical architecture | Follow-on | Phase H | NOT STARTED | n/a |

## Cross-references

**Source artifacts merged into this plan:**
- `runbooks/d-17-211-master-project-plan.md` — Track A detail (on `feat/d-17-211-rearchitecture`)
- `architecture-facts/2026-05-08-platform-unified-architecture.md` — software/hardware mapping
- `architecture-facts/circulatory-doctrine.md` — placement principle
- `architecture-facts/2026-05-08-converged-platform-architecture.md` — hardware conclusion
- `architecture-facts/article-intake-protocol.md` — Track B4 protocol
- `architecture-facts/rss-intelligence-substrate-doctrine.md` — Track B3 substrate (on `feat/rss-intelligence`)
- `_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md` — Sakana evaluation
- `_audit/travel-doable-work-2026-05-08.md` — travel subset
- `_audit/physical-architecture-2026-05-08.md` — hardware audit
- LocalAIConfig repo at `/Users/adriancox/LocalAIConfig` — B1 codification + B2 agent config templates
- Master log at `/Users/adriancox/Downloads/integrated_ai_workstation_complete_master_log.md` — Track B research source for §16/§17/§32/§33 (PENDING-OPERATOR-INGEST)
- v3 master plan at `/Users/adriancox/Downloads/local_claude_code_replacement_architecture_master_v3.md` — **Track B2 source-of-truth** for the coding agent stack architecture; codifies "Aider is no longer the center" core correction (PENDING-OPERATOR-INGEST; see KI-B-09)

**Branches involved:**
- `main` — stable trunk
- `feat/d-17-211-rearchitecture` — Track A artifacts
- `feat/rss-intelligence` — Track B3 codification
- `chore/master-log-backlog-sweep-v2` — Track B5 sweep
- `feat/branch-summary-utility` — repo hygiene utility
- `feat/full-upgrade-master-plan` — THIS document
- `travel/2026-05-07/documentation-hardening` — D-17-MEDIA + D-17-160 (out of scope here, separate operational track)

## Status

**ACTIVE.** This plan supersedes the trip-doable backlog as the structuring frame. The trip-doable backlog remains valid as a SUBSET listing of which Phase 0 items can advance during travel.

This plan is a living document. Phase F doctrine refresh wave should update Status snapshot section + risks + KIs. Cross-track risks R-CT-04 explicitly addresses plan-vs-reality drift.

**Authored:** 2026-05-09 (Tokyo travel session, branch `feat/full-upgrade-master-plan` cut from main).
