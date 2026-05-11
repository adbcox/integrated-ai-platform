# Phase 17 closeout audit (2026-05-11)

**Trigger.** Survey Phase 17 closeout readiness against the 8 refined
criteria locked at `feat/orchestration-layer-build` commit `5f8e19d3`
(`docs/phase-17/PHASE_17_PLAN_2026-05-01.md` §"Closeout criteria").
Classify remaining work by execution-gate type. Propose closeout
sequence ordered for off-LAN execution where possible.

**Status:** AUDIT-ONLY. No closeout work executed. Subsequent execution
briefs draft from this audit's §5 + §6.

**Recommendation (one line, rationale in §5):** ~4 OFF-LAN executable
criteria can land via 3 small execution briefs from this session (KI
triage + meta-tooling hygiene + doctrine orphan-terminology + D-17-62
runbooks-index closeout); 3 criteria are LAN-gated or DECISION-gated
and require operator action; 1 criterion (phase tag) is the final
mechanical step after all others close. Phase 17 cannot tag-close
this session, but the off-LAN closeout commits substantially reduce
the remaining surface.

---

## §1 Pre-flight context

**Branch posture matters for this audit.** The 8 refined closeout
criteria themselves live on `feat/orchestration-layer-build` commit
`5f8e19d3` (unmerged to main as of audit date). The audit branch
`feat/phase-17-closeout-audit` is cut from main `8c10ec43`. Several
Phase 17 in-spirit artifacts referenced below live on other
unmerged branches:

| Branch | HEAD | Carries |
|---|---|---|
| `feat/orchestration-layer-build` | `5f8e19d3` (or successor) | Refined 8-criteria; CR-17-001–006 escalation annotations; `.claude/agents/` subagent definitions; `deployment/launchd/`; CLAUDE.md §"Current Inference Stack" / §"Network Topology" / §"Provenance Governance" / §"Common Failure Modes"; KI-010 + KI-011 |
| `feat/d-17-115-caddy-ca-trust` | `8a4c99f7` | D-17-115 Phase 1 (scripts/caddy-ca-trust-macos.sh + KI-012 + runbook extension + doctrine bullet + §9 annotation) |
| `feat/system-prompts-consolidation-audit` | `b2c4abcd` | System Prompt Library consolidation audit + MERGE-INTO-B execution |

**Closeout sequence is downstream of these merges landing on main.**
This audit classifies work assuming the merges happen first — the
closeout WPs below act on the post-merge main state. Where a criterion
depends on artifacts from a specific unmerged branch, that dependency
is flagged.

---

## §2 Method

Criteria-by-criteria survey against `feat/orchestration-layer-build:docs/phase-17/PHASE_17_PLAN_2026-05-01.md` §"Closeout criteria" (8 criteria). For each criterion:

1. Surface the criterion text verbatim.
2. Survey current state evidence on main + relevant unmerged branches.
3. Identify the gap to closure.
4. Decompose closure into work-packages (WPs).
5. Tag each WP with execution-gate classification:

| Tag | Definition |
|---|---|
| **OFF-LAN EXECUTABLE** | Can land in a Phase 17 closeout brief from off-LAN this session — pure repo work, no Mac Mini/Mac Studio/NetBox/Caddy/Headscale reachability required |
| **LAN-GATED** | Requires on-LAN access to platform infrastructure (Mac Mini at .145, Mac Studio at .142, NetBox at netbox.internal, Caddy at vault.internal etc., Headscale connectivity) |
| **DECISION-GATED** | Requires explicit operator decision before execution can proceed (CMDB authority designation, KI categorization confirmation, severity-taxonomy lock-in, etc.) |
| **ACCEPTED-AS-DEFERRED** | Legitimately carries past `phase-17-final` tag with documented deferral in the closeout doc (LAN-gated trigger with operator sign-off) |
| **ACCEPTED-AS-PERMANENT-DEBT** | Decade-horizon or operationally unbounded; tracked but not gating phase closure (e.g., KI-012 Caddy CA rotation) |

---

## §3 Criterion-by-criterion status survey

### §3.1 Criterion 1 — All Phase 17 in-spirit deliverables resolve

**Criterion verbatim:** *"All Phase 17 in-spirit deliverables resolve (DONE or explicitly DEFERRED with written reason in closeout doc). 'In-spirit' is defined as: the original 22 from this plan PLUS post-plan additions NOT escalated to Phase 18 via CR-17-001 through CR-17-006. The 39 deliverables escalated via those CRs (Aider agentic stack, music arr-stack, arr-stack expansion + observability, Codex / multifile orchestration, Goose Phase-13+ tiers, misc Phase-18) are explicitly OUT OF SCOPE for Phase 17 closure and tracked in their respective CR records."*

**Current state:** §9 survey of IN PROGRESS / NOT STARTED rows excluding CR escalations finds exactly **5 Phase-17-in-spirit IN PROGRESS deliverables** on main:

| ID | Title | Status | Sub-WP state |
|---|---|---|---|
| D-17-43 | CMDB reconciliation intake — three-substrate drift audit | IN PROGRESS | Intake/audit DONE (`docs/_audit/cmdb-substrate-inventory-2026-05-03.md` + `cmdb-drift-2026-05-03.md`); full deliverable scope at `docs/phase-18/d-17-43/SCOPE_2026-05-03.md` gated on operator authority decision at WP-04 |
| D-17-45 | CMDB reconciliation — substrate audit + canonical authority decision (intake phase) | IN PROGRESS | Intake added 2026-05-03; depends on D-17-43 WP-04 |
| D-17-54 | OPNsense DHCP DNS-push runbook + OpenProject admin recovery runbook | IN PROGRESS | Two runbooks authored via §18.O pipeline; row text suggests substantial completion, validation gate may remain |
| D-17-62 | Runbooks index + legacy-reference scan | IN PROGRESS | Added 2026-05-04 via roadmap-create.sh; no sub-WP breakdown in §9; scope = author runbooks index + scan for legacy refs |
| D-17-115 | Caddy internal-CA trust distribution | IN PROGRESS | Phase 1 DONE on `feat/d-17-115-caddy-ca-trust` (script + KI-012 + runbook extension + doctrine bullet); Phase 2 LAN-gated |

**Gap to closure (per deliverable):**

- **D-17-43**: WP-04 authority decision required from operator (NetBox vs `~/.platform-registry/inventory.json` vs `service-registry.yaml.DEPRECATED` canonical authority). DECISION-GATED. WP-05 (full deliverable scope per `docs/phase-18/d-17-43/SCOPE_2026-05-03.md`) gated on that decision.
- **D-17-45**: Sibling to D-17-43; same authority-decision gate.
- **D-17-54**: Verify runbooks meet operator review; possibly close as DONE if runbook content is adequate. Re-read both runbooks to confirm scope. Mostly OFF-LAN EXECUTABLE.
- **D-17-62**: Author runbooks index + run legacy-reference scan. OFF-LAN EXECUTABLE.
- **D-17-115**: Phase 1 DONE off-LAN (on its own branch); Phase 2 LAN-gated (extract cert via docker exec on Mac Mini; verify trust on each device). ACCEPTED-AS-DEFERRED with written reason.

**Closure WPs:**
- WP-1.1: Decompose D-17-43/D-17-45 authority decision (operator presents the 3-substrate options, picks canonical, writes the decision rationale into `docs/phase-18/d-17-43/WP-04_AUTHORITY_DECISION_MATRIX_2026-05-03.md`). DECISION-GATED.
- WP-1.2: D-17-54 closure verification — read both authored runbooks, confirm scope match, flip status DONE if adequate. OFF-LAN EXECUTABLE.
- WP-1.3: D-17-62 execution — author `docs/runbooks/README.md` index from `ls docs/runbooks/`; scan for legacy `docs/audits/` / `docs/architecture/` references; flag any stale. OFF-LAN EXECUTABLE.
- WP-1.4: D-17-115 close-as-DEFERRED — document the off-LAN-DONE state in closeout doc; Phase 2 carries forward. OFF-LAN EXECUTABLE.

### §3.2 Criterion 2 — Stack audit re-run (D-17-01 v2)

**Criterion verbatim:** *"Stack audit re-run (D-17-01 v2) shows zero NEW 'evaluated individually' findings — i.e., the Tier 5 doctrine is preventing recurrence."*

**Current state:** D-17-01 original is `docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` per the plan's Tier 1 row. Re-run v2 does not exist (find returned empty for `*stack*audit*v2*` and `*stack*re-run*`). The re-run requires reading current platform state (services / routes / dependencies) and comparing against the v1 baseline.

**Gap to closure:** Re-run the audit. Requires probing live platform state — LAN-gated for service-state queries (`docker ps`, NetBox API, `~/.platform-registry/inventory.json` consultation).

**Closure WPs:**
- WP-2.1: Author D-17-01 v2 stack audit re-run. LAN-GATED (needs Mac Mini reachability for `docker ps` + service-registry consultation).

### §3.3 Criterion 3 — Capability audit template cited outside Phase 17

**Criterion verbatim:** *"Capability audit template (D-17-02) cited at least once outside Phase 17 (proves it's load-bearing, not shelfware)."*

**Current state:** Citations to `CAPABILITY_AUDIT_TEMPLATE` / `capability-audit-template` found in 4 docs outside Phase 17:

- `docs/PROJECT_FRAMEWORK.md` (framework — Phase 17 deliverable register; counts as in-Phase-17)
- `docs/_audit/physical-architecture-2026-05-01.md` (D-17-03 physical architecture audit)
- `docs/_audit/loose-doc-inventory-2026-05-03.md` (D-17-16 inventory)
- `docs/_retired/sportarr-2026-05-01.md` (D-17-08 retirement)

D-17-03 / D-17-08 / D-17-16 are all Phase 17 deliverables themselves, so these are technically intra-Phase-17 citations. The criterion's intent ("cited at least once outside Phase 17 to prove load-bearing") may or may not be satisfied depending on whether the citations are meaningful "use of the template" vs cross-deliverable bookkeeping.

**Gap to closure:** Operator judgment call. If the criterion accepts intra-Phase-17 worked-example use (D-17-08 sportarr-fix-or-retire applied the template), then **GREEN**. If criterion requires citation outside the deliverable register entirely (e.g., a future Phase 18 deliverable applies the template), then deferral.

**Closure WPs:**
- WP-3.1: Operator judgment — does intra-Phase-17 worked-example use satisfy the criterion? DECISION-GATED.

### §3.4 Criterion 4 — NetBox service inventory matches running-state container roster

**Criterion verbatim:** *"NetBox service inventory matches running-state container roster after consolidation work (D-17-06 + D-17-07 + D-17-08)."*

**Current state:** D-17-06 (agent surface audit + consolidation), D-17-07 (topology-api audit), D-17-08 (Sportarr fix-or-retire) all DONE per §9. The NetBox-vs-container-roster reconciliation step itself is gated on:
- D-17-43 + D-17-45 CMDB authority decision (criterion 1)
- NetBox at `netbox.internal` reachability (LAN access)
- `docker ps` on Mac Mini (LAN access)

**Gap to closure:** Run the reconciliation probe after authority decision lands. Compare NetBox `dcim/devices` + `virtualization/virtual-machines` (or equivalent service registry) against `docker ps -a` on Mac Mini. Surface any deltas.

**Closure WPs:**
- WP-4.1: NetBox-vs-container reconciliation probe. **LAN-GATED + DEPENDENCY-GATED** on D-17-43/45 authority decision.

### §3.5 Criterion 5 — KI register triage

**Criterion verbatim:** *"KI register triage: all OPEN KIs at phase close are categorized — each must be one of: closed-as-resolved (work done, status flipped to RESOLVED), escalated-to-deliverable (becomes a D-NN-MM in Phase 18 or later), or accepted-as-permanent-debt (rationale entered in closeout doc with explicit operator sign-off). KIs with deferred upgrade paths (e.g., KI-010 awaiting Mac Studio reachability via Headscale) qualify as accepted-as-permanent-debt."*

**Current state:** KI inventory:

| KI | Source branch | Status | Triage disposition (proposed) |
|---|---|---|---|
| KI-001 plane-api OOM | main | RESOLVED 2026-05-01 (inline `**Status:**` header in body) | closed-as-resolved — confirm and migrate inline status to YAML frontmatter for parser-consistency |
| KI-002 mcp-docker Colima mount | main | RESOLVED (inline header) | closed-as-resolved (same migration) |
| KI-003 obot dev-mode frontend | main | OPEN per Brief 2A audit (inline header may differ) | NEEDS-OPERATOR-DECISION — confirm OPEN vs RESOLVED |
| KI-004 mcp-docs-remote startup | main | MITIGATED (YAML frontmatter) | closed-as-resolved or accept-as-debt; operator decides |
| KI-005 silent cron failure | main | CLOSED 2026-05-01 (inline) | closed-as-resolved |
| KI-009 OPNsense parity-check | main | RESOLVED at D-17-21 close (inline) | closed-as-resolved |
| KI-010 upstream Qwen scan | `feat/orchestration-layer-build` only | OPEN | accepted-as-permanent-debt — LAN-gated upgrade path documented |
| KI-011 concurrent-load validation | `feat/orchestration-layer-build` only | OPEN | accepted-as-permanent-debt — LAN-gated upgrade path documented |
| KI-012 Caddy CA rotation | `feat/d-17-115-caddy-ca-trust` only | OPEN | accepted-as-permanent-debt — decade-horizon |
| KI-RETIRED-rclone-sftp | main | RETIRED (filename prefix) | already retired; no action |

**Gap to closure:** Triage doc capturing each KI's disposition; status-field consistency across KIs (inline `**Status:**` vs YAML frontmatter); operator sign-off on the accept-as-permanent-debt categorization for KI-010/011/012.

**Closure WPs:**
- WP-5.1: Author triage doc `docs/known-issues/triage-2026-05-NN.md` enumerating each KI's disposition. OFF-LAN EXECUTABLE.
- WP-5.2: Normalize KI status fields (move inline `**Status:**` to YAML frontmatter where missing). OFF-LAN EXECUTABLE.
- WP-5.3: Operator sign-off on accept-as-permanent-debt categorizations. DECISION-GATED.

### §3.6 Criterion 6 — Doctrine consolidation (orphan terminology)

**Criterion verbatim:** *"Doctrine consolidation: orphan-terminology resolved across doctrine docs. The Path A / Path B cross-reference pattern between `docs/architecture-facts/model-provenance.md` and `docs/architecture-facts/model-provenance-doctrine.md` is the worked example; verify any other split-doc situations have either explicit cross-references in both directions OR a documented rationale for the split. CLAUDE.md / `.claude/agents/` subagent system-prompt cross-references are NOT in scope here (different artifact class)."*

**Current state:** The Path A / Path B worked example is on `feat/orchestration-layer-build` (the model-provenance bidirectional cross-references landed there). On main `8c10ec43` the cross-references don't yet exist — they merge in when that branch lands.

Other split-doc candidates surfaced via grep for "this directory is canonical" / "D#22" / "content here wins":

| Doctrine file | Has split-doc situation? | Cross-references? |
|---|---|---|
| `docs/architecture-facts/model-provenance.md` | YES (with model-provenance-doctrine.md) | resolved on `feat/orchestration-layer-build` |
| `docs/architecture-facts/capability-self-knowledge.md` | Single canonical; D-17-23 source | n/a |
| `docs/architecture-facts/exo-cluster.md` | Cross-refs `docs/system-prompts/tiers/T4-distributed.md` | uni-directional (acknowledged) |
| `docs/architecture-facts/identifier-conventions.md` | Cross-refs `PROJECT_FRAMEWORK.md §3` for taxonomy | uni-directional; PROJECT_FRAMEWORK.md §3 doesn't back-reference identifier-conventions.md |
| `docs/architecture-facts/integration-audit-doctrine.md` | Cross-refs many other doctrine docs | bidirectional in most cases |

Also the System Prompt Library consolidation on `feat/system-prompts-consolidation-audit` resolved Library A / Library B as bidirectional cross-references — that work satisfies orphan-terminology for the prompt-library axis.

**Gap to closure:** One residual orphan-terminology candidate identified — `PROJECT_FRAMEWORK.md §3` (label-format conventions) and `docs/architecture-facts/identifier-conventions.md` overlap on identifier patterns but only the identifier-conventions doc cross-references the framework, not vice-versa. Operator decides whether the asymmetry is intentional (framework is the canonical register; identifier-conventions is the extracted taxonomy for cross-doc reference) or needs back-reference.

**Closure WPs:**
- WP-6.1: Add back-reference from `PROJECT_FRAMEWORK.md §3` to `docs/architecture-facts/identifier-conventions.md` (or document the rationale for the asymmetry). OFF-LAN EXECUTABLE.

### §3.7 Criterion 7 — Meta-tooling hygiene

**Criterion verbatim:** *"Meta-tooling hygiene: CLAUDE.md reviewed for staleness and trimmed if needed (no broken `@path` imports; no stale 'current state' markers; no contradictions with current §9 status). Subagent MEMORY.md files curated (prune session-specific noise; promote stable patterns into agent system prompts where appropriate). `.secrets.baseline` reviewed for stale entries."*

**Current state:**

| Artifact | Current state | Hygiene gap |
|---|---|---|
| `CLAUDE.md` | 338 lines on main; 376 lines on `feat/orchestration-layer-build` (after §"Current Inference Stack" + §"Network Topology" + §"Provenance Governance" + §"Common Failure Modes" addition) | Post-merge state needs review for stale "current state" markers, especially the `as of HEAD 81db99ea` line and the §"Current Inference Stack" content if Phase 2 of D-17-115 lands and re-shapes the stack |
| `.claude/agent-memory/*/MEMORY.md` | 4 placeholders (state-verifier, brief-author, doctrine-author, provenance-runner) — none curated since authoring | Review for any session-specific learnings worth promoting into agent system prompts |
| `.secrets.baseline` | 14398 bytes on main; updated by D-17-115 Phase 1 + earlier work on other branches | Stale-entry review post-merge: any entries pointing at retired paths (e.g., `docs/system-prompts/modes/voice-fast.md` retired in consolidation merge)? Verify all whitelisted hashes still target live files |

**Gap to closure:** Three small review-and-update tasks. All OFF-LAN EXECUTABLE.

**Closure WPs:**
- WP-7.1: CLAUDE.md staleness sweep — re-read post-merge state, flag any TODO/FIXME/STALE/UPDATE-NEEDED markers; verify @path imports resolve; verify §"Current Inference Stack" matches running state (note: requires LAN to verify live, but file-internal consistency is OFF-LAN). OFF-LAN EXECUTABLE.
- WP-7.2: Subagent MEMORY.md curation — read each MEMORY.md, prune placeholder content if no learnings accumulated, otherwise promote stable patterns into the agent's `.claude/agents/<name>.md` system prompt. OFF-LAN EXECUTABLE.
- WP-7.3: `.secrets.baseline` stale-entry review — for each whitelisted hash, verify the referenced file still exists at the recorded path and line number. OFF-LAN EXECUTABLE.

### §3.8 Criterion 8 — Phase tag

**Criterion verbatim:** *"Phase tag `phase-17-final` cut."*

**Current state:** `git tag -l 'phase-17-final*'` returns empty. Tag not yet cut.

**Gap to closure:** Cut the tag after all other criteria GREEN.

**Closure WPs:**
- WP-8.1: `git tag -a phase-17-final -m "<closeout doc reference>"` then `git push origin phase-17-final`. OFF-LAN EXECUTABLE (assuming all preceding criteria close).

---

## §4 WP classification table

| WP | Description | Tag | Effort |
|---|---|---|---|
| WP-1.1 | D-17-43/45 authority decision matrix | DECISION-GATED | 1 brief (post-decision) |
| WP-1.2 | D-17-54 closure verification | OFF-LAN EXECUTABLE | <30 min |
| WP-1.3 | D-17-62 runbooks index + legacy-ref scan | OFF-LAN EXECUTABLE | 1-2 hours |
| WP-1.4 | D-17-115 close-as-DEFERRED documentation | OFF-LAN EXECUTABLE | <30 min |
| WP-2.1 | D-17-01 v2 stack audit re-run | LAN-GATED | 2-4 hours (LAN session) |
| WP-3.1 | Capability audit template citation criterion judgment | DECISION-GATED | <15 min |
| WP-4.1 | NetBox-vs-container reconciliation | LAN-GATED + DEPENDENCY-GATED | 1-2 hours (LAN session, post-WP-1.1) |
| WP-5.1 | KI triage doc | OFF-LAN EXECUTABLE | 1 hour |
| WP-5.2 | KI status-field normalization | OFF-LAN EXECUTABLE | <30 min |
| WP-5.3 | Operator sign-off on accept-as-debt categorizations | DECISION-GATED | <15 min |
| WP-6.1 | PROJECT_FRAMEWORK.md ↔ identifier-conventions.md cross-reference | OFF-LAN EXECUTABLE | <30 min |
| WP-7.1 | CLAUDE.md staleness sweep | OFF-LAN EXECUTABLE | 1 hour |
| WP-7.2 | Subagent MEMORY.md curation | OFF-LAN EXECUTABLE | <30 min |
| WP-7.3 | .secrets.baseline stale-entry review | OFF-LAN EXECUTABLE | <30 min |
| WP-8.1 | Cut phase-17-final tag | OFF-LAN EXECUTABLE | <5 min (gated on all above) |

**Summary:**
- OFF-LAN EXECUTABLE: 9 WPs (1.2, 1.3, 1.4, 5.1, 5.2, 6.1, 7.1, 7.2, 7.3) plus 8.1 final
- LAN-GATED: 2 WPs (2.1, 4.1) — defer to next on-LAN session
- DECISION-GATED: 3 WPs (1.1, 3.1, 5.3) — operator action required
- ACCEPTED-AS-DEFERRED / PERMANENT-DEBT: D-17-115 Phase 2, KI-010, KI-011, KI-012

---

## §5 Proposed closeout sequence

The 9 OFF-LAN-EXECUTABLE WPs naturally group into 3 execution briefs:

### Brief A — KI triage + meta-tooling hygiene

| WP | Notes |
|---|---|
| WP-5.1 KI triage doc | Authors `docs/known-issues/triage-2026-05-NN.md` |
| WP-5.2 KI status-field normalization | Migrate inline `**Status:**` to YAML frontmatter; net-add `status:` line to KI-001/002/003 |
| WP-7.3 .secrets.baseline stale-entry review | Audit hash provenance + remove stale entries (e.g., retired `docs/system-prompts/modes/*` paths if any baseline entries point there) |

Estimate: 2 hours. ~5 files touched.

### Brief B — Doctrine + framework hygiene

| WP | Notes |
|---|---|
| WP-6.1 framework ↔ identifier-conventions cross-reference | Add back-ref from `PROJECT_FRAMEWORK.md §3` to `docs/architecture-facts/identifier-conventions.md` (or doc the rationale) |
| WP-7.1 CLAUDE.md staleness sweep | Read CLAUDE.md, flag stale markers, verify @path imports, check §"Current Inference Stack" doesn't conflict with §9 |
| WP-7.2 Subagent MEMORY.md curation | Inspect 4 MEMORY.md placeholders; promote any learnings to agent prompts |

Estimate: 1.5 hours. ~5 files touched.

### Brief C — Phase-17-in-spirit deliverable closeout

| WP | Notes |
|---|---|
| WP-1.2 D-17-54 closure verification | Read both runbooks (DHCP DNS-push, OpenProject admin recovery); confirm scope match; flip §9 status to DONE if adequate |
| WP-1.3 D-17-62 runbooks index | Author `docs/runbooks/README.md`; run legacy-reference scan; flag stale `docs/audits/` / `docs/architecture/` cites |
| WP-1.4 D-17-115 close-as-DEFERRED | Author closeout doc paragraph documenting Phase 1 DONE off-LAN + Phase 2 LAN-deferred with reason |

Estimate: 2-3 hours. ~3 files touched.

### Brief D (FUTURE on-LAN) — LAN-gated work

| WP | Notes |
|---|---|
| WP-2.1 D-17-01 v2 stack audit re-run | Requires `docker ps` + NetBox API + `~/.platform-registry/inventory.json` on Mac Mini |
| WP-4.1 NetBox-vs-container reconciliation | Requires WP-1.1 authority decision first + LAN access |

**Phase-17-final tag (WP-8.1) cannot be cut until Brief D lands.** Phase 17 closeout therefore has two phases: off-LAN-close-pass (Briefs A-C this session) and on-LAN-close-pass (Brief D in a future on-LAN session). The closeout doc itself records the deferral; tag-cut waits for Brief D.

**Operator's Phase 17 closure path summary:**
1. Approve §6 decision points below.
2. Author + commit Briefs A, B, C this session (off-LAN).
3. Next on-LAN session: author + commit Brief D; close out KI register; cut phase-17-final tag.

---

## §6 Decision points for operator (ASK list)

Each is a discrete operator decision required before execution starts. Recommendations are my suggested defaults; operator may override.

| # | Decision | Recommendation | Rationale |
|---|---|---|---|
| Q1 | D-17-43 + D-17-45 CMDB authority: NetBox / `~/.platform-registry/inventory.json` / `service-registry.yaml.DEPRECATED` — which is canonical? | **NetBox** (per ADR-A-014); deprecate registry.yaml; treat inventory.json as runtime cache | ADR-A-014 already designated NetBox as CMDB authority; this just makes it operationally enforced |
| Q2 | D-17-54 closure: confirm the two authored runbooks (DHCP DNS-push + OpenProject admin recovery) are adequate without further LAN-side validation? | **CLOSE AS DONE** if the runbooks are content-complete; LAN validation can be sub-WP of next on-LAN session | Avoids blocking Phase 17 closure on procedural-doc-validation when content is authored |
| Q3 | D-17-115 Phase 2: accept as DEFERRED in closeout doc, or block phase tag? | **ACCEPT AS DEFERRED** with written reason | Phase 1 DONE; Phase 2 is mechanical fill-in once on-LAN; blocking phase tag on LAN access defeats the purpose of off-LAN closeout |
| Q4 | Criterion 3 (D-17-02 cited outside Phase 17): does intra-Phase-17 worked-example use (D-17-08 sportarr) count, or must citation be outside Phase 17 entirely? | **YES it counts** — D-17-02 was applied as a template to D-17-08 sportarr (its first worked example); that satisfies "load-bearing, not shelfware" | Criterion intent was to prevent template-shelfware; D-17-08's use proves it's load-bearing within the phase |
| Q5 | KI categorization sign-off: KI-010, KI-011, KI-012 as accept-as-permanent-debt (LAN-gated upgrade paths)? | **APPROVE** | All three have documented triggers + upgrade paths; LAN access via Headscale unblocks KI-010/011 simultaneously; KI-012 is decade-horizon |
| Q6 | KI-003 (obot dev-mode frontend) status: confirm OPEN vs RESOLVED? | **OPERATOR READS THE KI FILE** to confirm — I cannot determine without parsing the body | KI-003 inline status was UNKNOWN in my parse; needs manual confirmation |
| Q7 | KI-004 (mcp-docs-remote startup) MITIGATED disposition: close as resolved or accept as debt? | **CLOSE AS RESOLVED** if mitigation is operationally sufficient; otherwise accept-as-debt | Per KI-004's MITIGATED frontmatter, the mitigation is applied; operator decides whether further work is warranted |
| Q8 | Phase tag cut timing: cut phase-17-final after Brief C this session, or wait for Brief D (LAN session)? | **WAIT FOR BRIEF D** | Criteria 2 and 4 cannot close off-LAN; cutting the tag prematurely makes the "all criteria satisfied" claim untrue |

---

## §7 Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Branch-merge sequencing assumption (this audit assumes feat/orchestration-layer-build + feat/d-17-115-caddy-ca-trust + feat/system-prompts-consolidation-audit all merge to main before closeout WPs execute) is wrong | MEDIUM | Several WPs reference artifacts that don't exist on main yet; if merge order shifts, the WP scope shifts | Operator orchestrates merge sequence before any closeout brief drafts |
| Criterion 3 (D-17-02 citation) intent is more strict than my Q4 recommendation interprets | LOW | Closure path slips by one Phase 18 deliverable using the template | Operator's Q4 decision binds; if YES, criterion GREEN; if NO, defer to Phase 18 first citation |
| KI status-field normalization (WP-5.2) introduces a parser-compat issue if any tooling reads inline `**Status:**` headers | LOW | Tooling break; unlikely since no parser currently reads KI files | Pre-flight grep for KI-file parsers before WP-5.2 lands |
| Subagent MEMORY.md curation (WP-7.2) finds no learnings to promote (placeholders unchanged since authoring) | HIGH | None; WP is a no-op | Document the "no learnings to promote" finding in the closeout doc as evidence that subagent invocation didn't happen this Phase 17 cycle |
| .secrets.baseline stale entries (WP-7.3) include hashes for paths retired during the System Prompt Library consolidation merge | HIGH (if consolidation merged before this audit) | Pre-commit `detect-secrets` won't FAIL on missing whitelisted paths; baseline stays stable | No mitigation needed — stale entries are harmless; just record them for follow-up |
| Phase-17-final tag cut (WP-8.1) happens before D-17-115 Phase 2 lands; operator subsequently expects to find "phase-17 closed" referencing complete D-17-115 | MEDIUM | Closeout doc needs to be unambiguous about what was DEFERRED at tag-cut time | Operator approves Q3 + reads closeout doc's Deferral section before tag-cut |
| The 8 refined closeout criteria themselves are unmerged to main; an unmerged-criteria assumption could let phase-17-final tag-cut before the criteria are visible on main | LOW | Confusing for future archaeologists | Cut tag at a commit that has both the criteria AND the satisfied state visible; that means the orchestration-layer-build merge must precede tag-cut |
| D-17-43/45 authority decision (Q1) may surface deeper architectural questions (e.g., NetBox itself unreliable, registry-yaml not actually deprecated) that re-open work | MEDIUM | Brief D scope expands; phase-17-final tag-cut slips | Operator's Q1 decision binds the scope; if NetBox-as-authority is unworkable, escalate to Phase 18 via CR-17-007 (new CR) |
| F7 false-positive completion pattern (Brief C surfaced one in §9 D-17-54: openproject-admin-recovery.md claimed landed, never authored) may be present in other §9 DONE rows that were not exercised during Brief A/B/C investigation | MEDIUM-HIGH | Audit trail integrity for past closeouts is weaker than the §9 status column implies; future archaeologists may inherit silent gaps | Brief D scope addition: spot-check §9 DONE rows authored across the §18.O Goose pipeline (cell C1/C1a) — those are the highest-prior-risk surface for F7 recurrence. Outside the pipeline, F7 risk drops sharply (operator-authored rows verified at commit time). |

---

## End of audit

No closeout work executed. Execution briefs draft per §5 sequence after operator review of §6 decisions. Brief A (KI triage + meta-tooling hygiene) is the natural first execution brief — fully OFF-LAN-EXECUTABLE, no decision dependencies, lowest risk.

---

## §8 Brief A landing note (2026-05-11)

**Brief A landed** on branch `feat/phase-17-brief-a` (single commit pending push). WPs completed:

- **WP-1 (KI frontmatter migration):** KI-001, KI-002, KI-005, KI-009 gained YAML frontmatter (ki / title / severity / status / discovered / phase) matching the KI-010/011/012 convention. Body content preserved unchanged (importantly: KI-009's `**Status:**` body line preserved because `scripts/check-repo-coherence.py caddy-dns-parity` reads it at runtime per the hook's data-driven gate).
- **WP-2 (disposition annotations):** KI-010 + KI-011 gained `disposition: accept-as-deferred-pending-on-LAN-session`; KI-012 gained `disposition: accept-as-permanent-debt-decade-horizon`. Each got a `## Disposition (2026-05-11)` body section recording the audit §6 Q5 operator approval. Status field preserved as OPEN on all three.
- **WP-3 (KI-003 + KI-004 deferred to operator decision):** content surfaced to operator in Brief A report-back. Both files NOT modified per brief constraint.
- **WP-4 (CLAUDE.md staleness):** L239 stale HEAD reference (`81db99ea` from the orchestration-layer-build authoring) refreshed to current main `fabe20a7` with timestamp. No other staleness markers required substantive correction (the other grep matches were doctrine references using the word "stale" in conceptual contexts, not staleness markers themselves).
- **WP-5 (Subagent MEMORY.md scaffolding):** all 4 placeholders (state-verifier / brief-author / doctrine-author / provenance-runner) replaced with structured stub schemas (Operator preferences / Recurring patterns / Cross-references / Change log). No accumulated session content to promote — the agents have not been invocation-active during Phase 17.
- **WP-6 (.secrets.baseline stale-entry removal):** SKIPPED — pre-flight `comm -23` on baselined vs tracked file lists returned empty (4 file pointers in baseline, all live). Baseline is clean.

WP-3 deferred items (operator decision required before next execution brief):

- **Q6 — KI-003 disposition.** KI-003 inline status reads "RESOLVED — root cause was OBOT_DEV_MODE: 'true' in obot-stack.yml. Setting it to 'false' makes obot serve the API on /api/ (returns 403 = auth required, valid) and return clean 404 on UI paths. ... obot.internal validates verify=0 http=404 (in the 2xx-4xx pass range)." **Recommend close-as-resolved** — inline status is unambiguous.
- **Q7 — KI-004 disposition.** KI-004 YAML frontmatter is `status: MITIGATED`. Mitigation applied (`--ignore-scripts` flag in npm install); recommended fix (custom Docker image pre-installing dependencies) is deferred. **Recommend accept-as-permanent-debt** unless operator wants to schedule the custom-image work as a Phase 18 deliverable.

Remaining Phase 17 closeout sequence:

- **Brief B** (doctrine + framework hygiene): WP-6.1 PROJECT_FRAMEWORK §3 ↔ identifier-conventions.md cross-reference; CLAUDE.md staleness sweep (already partly addressed in Brief A's WP-4); subagent MEMORY.md curation (placeholders are now scaffolded; promotion of stable patterns happens during subagent invocation, not on schedule).
- **Brief C** (Phase-17-in-spirit deliverable closeout): D-17-54 closure verification; D-17-62 runbooks index; D-17-115 close-as-DEFERRED in closeout doc.
- **Brief D** (LAN session): D-17-01 v2 stack audit re-run; NetBox-vs-container reconciliation. Phase-17-final tag cut after Brief D lands.

---

## §9 Brief B landing note (2026-05-11)

**Brief B landed** on branch `feat/phase-17-brief-b` (single commit pending push). WPs completed:

- **Q6 KI-003 closure (audit §6 Q6 operator approval):** YAML frontmatter migration applied. New frontmatter fields: `status: RESOLVED`, `disposition: closed-as-resolved-per-audit-Q6`, plus `severity / discovered / phase` matching the Brief A pattern. Body `## Status` section preserved unchanged (parser-compat-safe; consistent with Brief A's `**Status:**` body-line preservation for KI-009). Added `## Disposition (2026-05-11)` body section referencing the evidence chain (root cause identified — `OBOT_DEV_MODE: "true"`; fix applied — flipped to `"false"`; verification — `obot.internal` returns http=404 in pass range).
- **Q7 KI-004 disposition (audit §6 Q7 operator approval):** existing YAML frontmatter gained `disposition: accept-as-permanent-debt-mitigated-workaround` field. Status preserved as `MITIGATED`. Added `## Disposition (2026-05-11)` body section recording: mitigation operationally functional; custom-image permanent fix deferred indefinitely; reopens if mitigation fails or if operator schedules the custom-image build as a Phase 18 deliverable.
- **Criterion 6 cross-reference cleanup:** the asymmetric PROJECT_FRAMEWORK.md §3 ↔ identifier-conventions.md cross-reference is now bidirectional. PROJECT_FRAMEWORK.md §3 gained a "Doctrine cross-reference" paragraph pointing at identifier-conventions.md as the canonical detailed taxonomy doc. identifier-conventions.md L4 was updated to cite both `§1 (lifecycle vocabulary)` AND `§3 (label format conventions)` for accuracy (previously cited only §1; the actual label-format table is at §3); "Last verified" date updated to 2026-05-11 with audit reference. The doctrine pair is now structurally symmetric per criterion 6's worked-example pattern (Path A / Path B from model-provenance).

Remaining Phase 17 closeout sequence (post-Brief B):

- **Brief C** (Phase-17-in-spirit deliverable closeout): D-17-54 closure verification (read both authored runbooks; flip §9 status to DONE if adequate); D-17-62 runbooks index (author `docs/runbooks/README.md`; legacy-reference scan); D-17-115 close-as-DEFERRED in Phase 17 closeout doc (Phase 1 DONE off-LAN; Phase 2 LAN-gated).
- **Brief D** (next on-LAN session): D-17-01 v2 stack audit re-run; NetBox-vs-container reconciliation (depends on Q1 CMDB authority decision). Phase-17-final tag cut after Brief D lands and all 8 criteria satisfy.

Criterion 5 (KI register triage) is now **COMPLETE** as of Brief B — every KI on main has a disposition recorded:

| KI | Status | Disposition |
|---|---|---|
| KI-001 | RESOLVED | closed-as-resolved (frontmatter migrated Brief A) |
| KI-002 | RESOLVED | closed-as-resolved (frontmatter migrated Brief A) |
| KI-003 | RESOLVED | closed-as-resolved-per-audit-Q6 (Brief B) |
| KI-004 | MITIGATED | accept-as-permanent-debt-mitigated-workaround (Brief B) |
| KI-005 | CLOSED | closed-as-resolved (frontmatter migrated Brief A) |
| KI-009 | RESOLVED | closed-as-resolved (frontmatter migrated Brief A) |
| KI-010 | OPEN | accept-as-deferred-pending-on-LAN-session (Brief A) |
| KI-011 | OPEN | accept-as-deferred-pending-on-LAN-session (Brief A) |
| KI-012 | OPEN | accept-as-permanent-debt-decade-horizon (Brief A) |
| KI-RETIRED-rclone-sftp | RETIRED (filename prefix) | n/a — historical artifact |

Criterion 7 (meta-tooling hygiene) is **partially complete** — CLAUDE.md staleness fixed in Brief A; MEMORY.md scaffolds in Brief A; .secrets.baseline review in Brief A surfaced zero stale entries. Subagent MEMORY.md curation is a continuous activity (population happens during subagent invocations, not on a schedule); not blocking for tag-cut.

Criterion 6 (doctrine consolidation) is now **COMPLETE** — both worked examples (Path A/B model-provenance from feat/orchestration-layer-build merge; PROJECT_FRAMEWORK ↔ identifier-conventions from Brief B) have bidirectional cross-references; no remaining orphan-terminology pairs identified.

---

## §10 Brief C landing note (2026-05-11)

**Brief C landed** on branch `feat/phase-17-brief-c` (single commit pending push). WPs completed:

- **WP-1 (D-17-54 closure investigation):** authored runbook claims verified against repo state. `docs/runbooks/opnsense-dhcp-dns-push.md` confirmed present (canonical, Brief C-indexed). `docs/runbooks/openproject-admin-recovery.md` confirmed **never authored** — investigation across worktrees, `git log --all --diff-filter=A '*openproject*'`, `git fsck --unreachable`, `git stash list`, `git reflog`, and worktree grep for "OpenProject admin recovery" all returned the same answer: only meta-doc references exist (the §9 claim itself, plus `goose-capability-boundary.md`, `promotion-criteria.md`, and this audit doc — each citing the runbook by name). No draft file at any path on any branch or reflog entry. Disposition: **Path C scope-split** confirmed.
- **WP-2 (§9 D-17-54 scope-correction + new D-17-137 row):** D-17-54 row title scope-trimmed to OPNsense DHCP DNS-push runbook only; status flipped IN PROGRESS → DONE with explicit revision note citing F7 pattern (`integration-audit-doctrine.md` Finding 2). New D-17-137 row appended to §9 with NOT STARTED status, descope provenance, and Phase 18 off-LAN-executable scope (operator verification of `rails runner` password-reset command syntax remains a destructive-surface gate before runbook commit).
- **WP-3 (D-17-62 runbooks index closure):** `docs/runbooks/README.md` extended additively. 12 missing runbook entries added to existing category tables (Platform Operations: foundation-install-status-track-2 / home-transition-mac-studio / mac-studio-day-1; Drift/Governance: regression-probe-failure; DNS/Network/Access: caddy-internal-ca-trust; Arr/Media/NAS: buildarr-excluded-services / download-pipeline-troubleshooting; AI/Local Models/Tooling: aider-default-workflow / serena-mcp-integration / track-1a-litellm-status; Legacy Monitoring: zabbix-templates / zabbix-trapper-pattern). All 12 files verified present pre-commit. New **Legacy-reference scan** section catalogues three classes of intentional historical references (`docs/_retired/` pointers, sportarr restoration-context references, CR-17-NNN-escalated D-NN-MM IDs cited in runbooks). New **Maintenance posture** section codifies append-on-author rule + quarterly drift-sweep cadence + status legend stability. No runbook content edits; no status promotions/demotions; closes the index gap.
- **WP-4 (§9 carry-forward annotations):** D-17-43, D-17-45, D-17-115 rows gained Brief D handoff annotations. D-17-43/45 stay IN PROGRESS pending Brief D Q1 (CMDB authority — recommend NetBox per ADR-A-014); D-17-115 stays IN PROGRESS pending Brief D LAN-session Phase 2 (cert extraction + on-device trust verification). Status fields unchanged.
- **WP-5 (§9 D-17-62 close-as-DONE):** executed inline with WP-3; status IN PROGRESS → DONE; row body cites the substrate landed in `docs/runbooks/README.md`.
- **WP-6 (this audit doc):** §10 landing note (this section); §10.1 self-correction subsection appended; §7 risk register gained one new row (F7-recurrence risk across other §9 DONE rows with Brief D mitigation handoff).

Phase 17 closeout sequence post-Brief C:

- **Brief D** (next on-LAN session): D-17-01 v2 stack audit re-run; NetBox-vs-container reconciliation gated on Q1 CMDB authority decision; D-17-115 Phase 2 (cert extraction + device-side trust verification); F7-spot-check sweep of §18.O Goose-pipeline-authored §9 DONE rows (new — per §7 risk register row added Brief C). Phase-17-final tag cut after Brief D lands and all 8 criteria satisfy.

### §10.1 Self-correction: F7 false-positive completion pattern recurrence

The §9 D-17-54 row asserted two runbooks landed; only one did. The chronicle artifact (the §9 row text itself) is the load-bearing audit surface for Phase 17 closeout, and it carried a false claim from 2026-05-03 through 2026-05-11 — eight days — without surfacing the gap. Brief C surfaced it only because the closure WP required reading both authored artifacts; absent that read, the row would have closed as DONE at tag-cut.

This is structurally the same pattern documented as F7 in `integration-audit-doctrine.md` Finding 2 (originally surfaced via D-17-39 WP-04 / D-17-35 placeholder validation: "closing on a placeholder file would have been false-positive completion"). The recurrence is doctrinally significant for two reasons:

1. **Doctrine coverage existed but did not prevent recurrence.** F7 was already a named pattern in 2026-05-03. The §9 D-17-54 row was authored 2026-05-03 — same day. The Goose session pipeline did not consult the F7 doctrine pre-commit; the operator review at WP-04 did not consult it; this audit's closeout-criteria pass did not consult it.
2. **The surface that surfaced the recurrence (a closure-time read of the named artifacts) is exactly the WP-04 "frontier authors corrected runbooks + close" step described in the original D-17-54 row.** WP-04 never executed for the openproject-admin-recovery half; the row sat in IN PROGRESS limbo for eight days while the chronicle implied both runbooks were authored. The doctrine reads as if the failure mode is rare; in practice, the §18.O Goose-pipeline cell already produced one instance in Phase 17 (rate: 1 / 1 deliverables of this shape in this cell, sample-of-one).

**Doctrine response carried to Brief D:** spot-check §9 DONE rows authored across the §18.O Goose pipeline for F7-shape claims (artifact names mentioned in the row body) against repo state. This is the new §7 risk register row authored as part of Brief C. The cell-level demotion already executed in D-17-53 (Posture 0; C1 split into C1a/C1b; C1a indefinitely SUSPENDED for Goose+qwen3-coder:30b) is the upstream-side mitigation; the Brief D F7 spot-check is the downstream-side audit catching anything that landed before the demotion.

No further self-correction artifacts authored in Brief C scope — the corrective close on D-17-54 + new D-17-137 row + this audit self-correction subsection are the full corrective payload. The original D-17-54 row's WP-04 (frontier-authors-corrected-runbooks) never fired for the missing runbook; descoping rather than authoring under closeout pressure is the right call (operator verification of destructive surface remains a pre-author gate).
