# Project Framework — labels, lifecycle, communication

**Status**: Living doctrine (this document is updated when conventions change)
**Adopted**: 2026-05-01 during Phase 15
**Context**: PMP-aligned project structure + ITIL-aligned operational classification

This document is the canonical reference for how work on the Integrated AI Platform is labeled, sequenced, and communicated. The operator's background is PMP + ITIL; control / execution windows align with these conventions to make rollup, status, and cross-window communication unambiguous.

For historical phase records, see `docs/PHASE_LOG.md`.
For upcoming roadmap, see `docs/PHASE_ROADMAP.md`.
For multi-window operating discipline, see `docs/runbooks/operating-model.md`.

---

## 1. Project structure (PMP-aligned)

| Term | Meaning here | Example |
|---|---|---|
| **Project** | The platform as a whole | Integrated AI Platform |
| **Phase** | Numbered milestone block with charter, deliverables, closeout | Phase 15 |
| **Deliverable** | Concrete tracked output of a phase | D-15-02 (information architecture hygiene) |
| **Work Package** | Smallest planned executable unit; one execution-window run | WP-15-02-T4 (ADR README index) |
| **Task** | A single named action inside a work package | T4 (read-then-add ADR rows) |

### Phase lifecycle

Each phase has four stages:

1. **Open** — phase opens with a written charter listing planned deliverables
2. **Execute** — work packages dispatched to execution window, one or more per deliverable
3. **Verify** — each work package surfaces with PASS / SKIP / FAIL status; each deliverable closes when its tasks resolve (PASS or explicitly deferred)
4. **Close** — phase closeout doc authored when all deliverables resolved; phase tagged in git as `phase-NN-final`

A phase does NOT close while deliverables are open without an explicit deferral decision recorded in the closeout doc. Drift between "scope said" and "actually closed" must be visible.

---

## 2. Operational classification (ITIL-aligned)

| Term | Meaning here | Example |
|---|---|---|
| **Service** | Deployed thing tracked in `config/service-registry.yaml` (or NetBox post ADR-A-014) | NetBox, Vault, AnythingLLM |
| **Change Record** | Tracked modification with pre-flight, execution, verification | CR-15-001 (audit + validation commit) |
| **Incident** | Unplanned outage, severity-classified, postmortem required | Sev-2 Vault cascade 2026-04-30 |
| **Problem** | Root cause behind one or more incidents | "No PreToolUse hooks for destructive Vault operations" |
| **Risk** | Identified but not-yet-realized issue with mitigation plan | R-01 backup chain broken |
| **Known Issue** | Documented limitation accepted as live | KI-001 plane-api OOM (resolved); KI-003 obot dev-mode (open) |

A change record is the unit of work-package execution; when a WP runs, it IS a change. The pre-flight + surface format ARE the change-control gate.

### Severity scale (incidents)

| Severity | Definition |
|---|---|
| Sev-1 | Platform unavailable; data loss imminent or in progress |
| Sev-2 | Major capability lost; recovery in progress with concrete fallback |
| Sev-3 | Service degraded; capability impaired but not lost |
| Sev-4 | Issue identified; no user-visible impact yet |

---

## 3. Label format conventions

| Pattern | Meaning |
|---|---|
| `Phase-NN` | Phase NN |
| `D-NN-MM` | Deliverable MM under Phase NN |
| `WP-NN-MM-XX` | Work Package XX under Deliverable D-NN-MM |
| `T-N` (or `Tn`) | Task N within a work package |
| `CR-NN-NNN` | Change Record (zero-padded) |
| `R-NN` | Risk |
| `S-NN` | Audit/finding signal (used inline in audits, e.g. S9-F1) |
| `D#NN` | Doctrine point captured during a phase (e.g. D#25) |
| `XF-N` | Cross-cutting finding (used in audits) |
| `KI-NNN` | Known Issue (Phase 7-era convention; preserved) |
| `Sev-N` | Incident severity |

Labels are stable once issued. If scope changes, the label is closed (`SUPERSEDED by`, `DEFERRED to`) and a new label is issued. Re-using a label for new scope creates traceability rot and is forbidden.

### 3.1 Local model stack prioritization (T1–T4)

When a deliverable consumes local LLM capacity, prefer models in
this priority order. The tier reflects fitness for routine
platform work, not absolute model quality.

| Tier | Examples | Use for |
|---|---|---|
| **T1** | Claude Code via local Ollama orchestrator (qwen2.5-coder:32b) | Default. Routine implementation, refactoring, doc work, exploration. Free; no quota. |
| **T2** | Subagent chain: decomposer (32b) → implementer (14b) → reviewer (7b) | Multi-step work that benefits from explicit decomposition. Runs entirely on Mac Mini Ollama under `claude-local`. |
| **T3** | Specialty models (Gemma 4 26B MoE, Qwen3-Coder-Next 80B) on Mac Studio | Workloads where T1/T2 are clearly under-powered (long context windows, code-heavy multi-file refactors). Gated on D-17-10 (Provenance Kit) and D-17-12 (benchmarks) before adoption. |
| **T4** | Anthropic Pro via `claude-pro` shell function | High-judgment tasks where T1–T3 demonstrably fall short. Pro quota is finite — treat as expensive. |

**Rules:**
- Platform services NEVER depend on Anthropic API access (see CLAUDE.md "LLM Access Doctrine").
- T3 model adoption requires D-17-10 Provenance Kit gate to pass first; D-17-12 benchmark evidence must demonstrate the workload-specific win over T1/T2 before any deliverable adopts a T3 model as default.
- T4 escalation is operator-discretion, not automated. Subagents do not call out to T4.
- The T1–T2 split is a runtime decision: the Claude Code orchestrator decides per-task whether to delegate; the user does not need to think about it.

This sequencing protects two things: cost (T4 quota stays for genuinely-hard work) and provenance (T3 model pulls go through Cisco Provenance Kit governance before landing on any compute node).

---

## 3.5 Doctrine register

Doctrine points are durable platform rules captured during phase work
under the `D#NN` label. Older D# entries (D#01 through D#14) are
recorded inline in CLAUDE.md, ADRs, or phase closeout docs at their
point of capture. New doctrine from Phase 16 forward is enumerated
here so it cannot be lost between conversations.

### D#15 — Pre-deliverable cleanliness gate (MANDATORY HARD STOP)

Every deliverable's first task is **preflight #0**: verify the working
tree, repo, and operational state are clean before any substantive
work begins. The operator and the executor (Claude Code or any other
agent) BOTH must observe this.

**Cleanliness checks:**

- `git status --short` returns empty
- `python3 scripts/check-repo-coherence.py all` → exit 0
- `python3 scripts/cross-index-validate.py` → exit 0
- `python3 scripts/phase-deliverable-count.py <N>` → no error
- `/Users/admin/.venv-block-4c/bin/python scripts/openproject-sync-from-framework.py --dry-run` → exit 0
- `xindex /healthz` → all sources `status=ok`
- No new known-issues created in the prior session that haven't been
  triaged into a deliverable

On any failure, the deliverable does **NOT** proceed to substantive
work. Two acceptable resolutions:

1. **Fix the failure as preflight #0** with explicit explanation in
   the resulting commit message; OR
2. **Operator explicitly waives** with a written reason, captured
   verbatim in the deliverable's commit message under a
   `Cleanliness gate waiver:` header.

Drift carried silently into substantive work is treated as a Sev-3
incident at minimum. This doctrine point commits the rule into the PM
system so it cannot be bypassed by accident.

See `docs/runbooks/drift-detection.md` §8 for the runbook this gate
invokes.

### D#16 — Per-deliverable compaction boundary

Agent runtimes with compactable context (Claude Code, others)
**compact at the close of every deliverable**, AFTER the final
commit + OpenProject sync + surface emit. Compaction never happens
mid-deliverable.

**Compaction summary preserves:**

- Deliverable IDs that closed in this session + their commit hashes
- Any KIs created or closed
- Any waivers granted under D#15 (with reasons)
- Outstanding state pointers (e.g., "vault-snapshot helper has known
  limitation X documented in KI-007")
- Any drift surfaced and not yet resolved

The compaction summary becomes the working context for the next
deliverable's preflight #0.

**Pairs with D#15:** D#15 verifies repo state is clean before new
work; D#16 verifies agent context state is clean before new work.
Same doctrine, two surfaces.

Operators using runtimes without `/compact`-equivalent functionality
follow the spirit of the rule: at deliverable close, summarize state,
discard exploratory threads, retain only the durable record captured
in commits + KIs + runbooks.

### D#17 — Memory recency window for transient findings

Memory captures findings during ongoing intake (article evaluation,
research, exploratory chats). Findings persist in memory only until
the next clean boundary (deliverable close + compaction). At the
boundary, findings either (a) graduate to repo as scope notes,
deliverables, or pattern docs, or (b) are explicitly deemed
not-actionable and discarded. Memory is not the long-term store.
The repo is. Memory entries older than ~30 days that don't match
a repo artifact are candidates for triage on principle — orphan
memory items represent debt.

### D#18 — Cross-index participation

Any new service proposal must answer: "does this participate in
xindex?" (i.e., is it ingestable into the cross-index, or does it
expose itself via MCP). If no, the proposal must justify why this
service is acceptable as an island. Defaults to rejection without
justification.

### D#19 — Stack-level audit at Phase boundaries

Every Phase opens with a stack-level architectural audit using
`docs/STACK_ARCHITECTURE_AUDIT_2026-05-01.md` as the template.
Catches "evaluated individually" damage before it accumulates
into a Phase's scope.

### D#20 — Capability evidence for retirement recommendations

Before recommending retirement of any service, exhaustively
enumerate its actual capabilities (probed from running state, not
inferred from documentation) and verify each is replaceable by
something else in the stack. Pattern-matched "this looks redundant"
recommendations get rejected at audit review. Reference:
Zabbix vs VictoriaMetrics analysis, 2026-05-01, where vibes-based
"retire Zabbix" recommendation was reversed after probing showed
4,593 SNMP items + 510 JMX items + 55 hosts that VictoriaMetrics
cannot natively monitor.

### D#21 — Three-plane architecture audits

Architecture audits cover three planes: physical (hardware nodes,
network topology, storage topology, capability ceilings), logical
(containers/services and nominal roles), capability (what each tool
actually does in this deployment, probed from running state).
Verdicts on any tool require evidence at all three planes.
Single-plane reasoning ("logical-only: two metrics tools = redundant")
is invalid. This rule is the codification of the Zabbix lesson.

### D#22 — Architecture facts in docs/architecture-facts/, not memory

Architectural facts that have been forgotten and re-learned across
sessions (operator-confirmed corrections, platform-specific service
choices that diverge from defaults, etc.) MUST be persisted as
artifacts under `docs/architecture-facts/`. Memory and chat-transcripts
are insufficient — they don't survive compaction reliably and are
not searched by future sessions before assuming. The
`opnsense-dns-authority.md` fact (Dnsmasq, not Unbound) is the
prototype: forgotten on 2026-04-26, refought on 2026-05-01,
chronicled as a permanent file thereafter. Failure mode prevented:
"Claude argues with operator about platform configuration that
operator has already corrected in a previous session."

### D#23 — Capability self-knowledge is suspect by default

AI capability self-knowledge is unreliable. False negatives
("I can't do that" when the AI in fact can) are common across at
least four distinct failure modes: training-data gap (Flavor A),
tool-surface gap (Flavor B), cautious framing (Flavor C),
over-constraint inference (Flavor D). Operators MUST verify before
accepting a declared blocker as real, working through the
six-step diagnostic in `docs/runbooks/capability-discovery.md`
(registry hit → tool-surface → training-data → cautious framing →
over-constraint → real limitation). Canonical reference:
`docs/architecture-facts/capability-self-knowledge.md`. Working
registry: `docs/architecture-facts/known-capabilities.md`. Failure
mode prevented: "operator accepts a phantom limitation as
canonical and rebuilds workflow around an AI false negative
that a five-minute unblock would have resolved."

### D#24 — Install the full set on developer toolchain decisions

When two install options exist for a developer-toolchain component
(CLT-only vs full Xcode, minimal Python vs full uv/pip stack,
single-package vs full-toolchain bundle, etc.), default to the
full set unless there is a specific reason to constrain. Toolchain
is permanent infrastructure; the platform has substantial capacity
(Mac Mini at 625 GB free at decision time, comparable on Mac
Studio). Disk space and download time are NOT the dominant cost —
mid-deliverable surface-back round-trips for "we constrained too
hard, now we need the missing piece" are. Codified from the
T1.0/T1.5/Xcode escalation rounds in D-17-14 (2026-05-02), each of
which cost a surface-back round-trip that a default-to-full
posture would have skipped. Failure mode prevented: "deliverable
under-installs the toolchain on first pass, then pays for the
missing component in escalation rounds that fragment the
operator's attention." Apply to: Xcode-vs-CLT decisions, Python
toolchain (uv full vs piecemeal pip), Rust (full toolchain vs
single-target), Node (LTS-with-tools vs minimal). Does NOT apply
to: runtime-image dependencies (where minimal-base-image discipline
remains correct), production-container packages (where principle
of least installed software still wins), data-store install
options (where each capability has runtime cost and operational
surface). The doctrine is specific to *developer-machine
toolchains*, where the cost of having an unused tool is dominated
by the cost of not having a tool you turn out to need.

---

## 4. Surface format template

When a work package runs, the execution-window surface format is mandatory:

```
STATUS: <WP-id> <PASS|PASS-PARTIAL|SKIP|FAIL>
<task-1-id>: <PASS commit-hash | SKIP reason | FAIL>
<task-2-id>: ...
DELIVERABLE <D-NN-MM> STATE: <N of M tasks complete>
PHASE <NN> STATE: <N of M deliverables complete>
COMMITS LANDED THIS RUN: <count + hashes>
ERRORS LOGGED: <count, one-line summary each>
WORKING TREE NOW: <git status --short output>
TIME ELAPSED: <minutes>
```

This makes phase rollup automatic. A status request ("where are we on Phase 15?") is answered with deliverable counts and concrete commit hashes, not narrative.

The surface format is part of the change-control gate. Skipping it converts a Change Record into an undocumented change — which is the precondition the platform is being hardened against.

---

## 5. Phase numbering — historical note

Phase numbering was **consolidated at commit `a6253c3` (2026-04-29)**.

Prior to consolidation, phases were micro-numbered (Phase 7 Caddy CA Trust, Phase 10 Strava OAuth, the old Phase 16 Vault Architecture Restoration — note that the old "Phase 16" predates and is unrelated to the future new Phase 16 work). After consolidation, phases are larger blocks with named tracks inside.

Mapping between numbering schemes is preserved in `docs/PHASE_LOG.md` with a renumbering note dividing the two regions of the file.

For any phase number referenced in code, docs, or commits, check the date — pre-2026-04-29 references use the old scheme. The current numbering line continues forward from Phase 13 / 14 / 15.

---

## 6. Multi-window operating model

The platform is operated across multiple Claude windows by design. Roles split as:

| Window | Role | What it does |
|---|---|---|
| **Master Project Manager** (control / planning) | Plans, verifies, sequences | Drafts WP prompts; cross-references with audits + chats; surfaces decisions |
| **Execution** (Claude Code on Mac Mini) | Executes bounded WPs | Runs pre-flight, applies changes, surfaces |
| **Sibling planning** (other chats) | May run in parallel | Subject to MPM verification before any output is forwarded to execution |

Detailed multi-window discipline lives in `docs/runbooks/operating-model.md`.

The MPM never bypasses the Execution window for repository changes. The Execution window never expands scope beyond the WP it received.

---

## 7. Phase 15 — CLOSED 2026-05-01

**Phase 15 — Vault Recovery + Information Architecture Hygiene** (opened 2026-04-30, closed 2026-05-01)

Tag: `phase-15-final`. Full closeout: `docs/phase-15/PHASE_15_CLOSEOUT_2026-05-01.md`.

| Deliverable | Status | Reference |
|---|---|---|
| D-15-01: Audit + validation committed | DONE | 3105f07 |
| D-15-02: Information architecture hygiene | DONE | 6a18e6c, 818ab3e, 2ce52d8, 3631b62, c2cc83d, a9d4129 |
| D-15-03: Backup chain repaired (R-01) | DONE | bb5d315 + Vault state + MinIO user + snapshot 784ff718 |
| D-15-04: Vault audit device re-enabled (R-02) | DONE | Vault config; audit log writing |
| D-15-05: PreToolUse hooks shipped (R-03) | DONE | 3cc764b |
| D-15-06: vault-test instance live (R-08) | DONE | a8f3abe |
| D-15-07: ADR-A-007 dirty edit resolved (Path B) | DONE | 9d50f84 |
| D-15-08: Loose-doc retirement pass | DEFERRED to Phase 16 | beyond-audit |
| D-15-09: Phase 15 closeout doc + tag | DONE | (this commit) |
| D-15-10: PROJECT_FRAMEWORK.md doctrine | DONE | e7d1c5b |

**Phase 16 charter draft** (per closeout doc Section "Phase 16 charter draft"):

- D-16-01 Block 4.D retroactive closeout (InvenTree)
- D-16-02 Block 4.E cross-index service — autonomous-coding structural enabler
- D-16-03 Mac Studio Day-1 execution (2 pre-actions remaining)
- D-16-04 Vault data volume in backup chain (raft snapshot integration)
- D-16-05 Loose-doc retirement (deferred from D-15-08)
- D-16-06 Documentation drift detection automation
- D-16-07 Recovery-handoff doctrine update (value-correctness verification)

---

## 8. Phase 16 — current state

Phase 16 — Autonomous Coding Enablement (opened 2026-05-01)

Original PHASE_ROADMAP.md framing was capability-centric (Mac Studio compute,
InvenTree real data, cross-index). Phase 15 closeout reframed priority: the
cross-index service is the structural enabler for autonomous coding (operator
meta-goal), so it leads. Mac Studio + InvenTree real-data work follow.

D-16-08 and D-16-09 were added 2026-05-01 to address the operator's
"real-time architecture visibility" requirement. Both depend on the
cross-index foundation (D-16-02 + 02.1 + 02.2) and could not be scoped
earlier — they consume xindex's normalized topology (NetBox devices /
services + OpenProject state) to project current architecture into Grafana
dashboards (D-16-08) and a Structurizr C4 model (D-16-09).

Deliverable table:

| Deliverable | Status | Reference |
|---|---|---|
| D-16-01: Block 4.D retroactive closeout (InvenTree) | DONE | cecb3ce |
| D-16-02: Cross-index service foundation | DONE | a3c198c |
| D-16-02.0.5: Caddy site block + NetBox registration | DONE | c642034 |
| D-16-02.A: Plane bootstrap from PROJECT_FRAMEWORK.md | DONE | 86020ff |
| D-16-02.1: NetBox source ingestion | DONE | 16971f0 |
| D-16-02.2: Plane source ingestion | DONE | 3262667 |
| D-16-02.3: MCP tool wrapper | DONE | 6792969 |
| D-16-03: Mac Studio Day-1 execution | DEFERRED to Phase 17 (D-17-15) | re-parented 2026-05-01 |
| D-16-04: Vault data in backup chain (warm-copy, ADR-A-017) | DONE | 88559fe |
| D-16-04.1: Silent cron failure remediation | DONE | d344869 |
| D-16-05: Loose-doc retirement | DEFERRED to Phase 17 (D-17-16) | re-parented 2026-05-01 |
| D-16-06: Documentation drift detection automation | DONE | c49432e |
| D-16-07: Recovery-handoff doctrine update | DONE | 2075c1c |
| D-16-08: Unified architecture + health dashboard | DEFERRED to Phase 17 (D-17-17) | re-parented 2026-05-01 |
| D-16-09: Structurizr population from xindex/NetBox | DEFERRED to Phase 17 (D-17-18) | re-parented 2026-05-01 |

Sequencing: D-16-02 first (structural enabler), then D-16-01 (small),
then 02.1/02.2/02.3 expansions, then Mac Studio + remaining items.

---

## 9. Phase 17 — current state

Phase 17 — Three-plane architecture corrections + local AI stack (opened 2026-05-01)

Charter and full deliverable narrative: `docs/phase-17/PHASE_17_PLAN_2026-05-01.md`.

Tier 1 (foundation audits) → Tier 2 (architectural corrections) →
Tier 3 (local AI stack) → Tier 4 (Phase 16 carry-overs) → Tier 5
(doctrine + intake codification). Tier 5 lands in Bundle A.5 (this
opening); all other tiers are deliverable-scoped.

Deliverable table:

| Deliverable | Status | Reference |
|---|---|---|
| D-17-01 (historical: 17.A): Stack architecture audit promoted to repo | DONE | 8193014 |
| D-17-02 (historical: 17.B): Capability audit template | DONE | f1502f6 |
| D-17-03 (historical: 17.C): Physical architecture audit | DONE | c25c9ac |
| D-17-04 (historical: 17.D): Replace Plane with OpenProject | DONE | 8819861+a184202+3a30c6f+51b012e+f8e23ba+37f874c+d283fa1+abbbba8+cf0ff61+32b7ad0+2f6cc32 (ADR-A-018) |
| D-17-05 (historical: 17.E): Observability role-clarification | DONE | 9393785+9390c11 |
| D-17-06 (historical: 17.F): Agent surface audit + consolidation | DONE | 62b595d+57d7399 |
| D-17-07 (historical: 17.G): topology-api audit | DONE | 5698f30 |
| D-17-08 (historical: 17.H): Sportarr fix-or-retire | DONE | 4ae00a2 |
| D-17-09 (historical: 17.I): OPNsense API integration for DNS-parity | DONE | ecd7274 |
| D-17-10 (historical: 17.J): Cisco Provenance Kit | DONE | b6a78f1+29dfec1+bc9d77f |
| D-17-11 (historical: 17.K): Local LLM system prompt library | DONE | cc9df44 |
| D-17-12 (historical: 17.L): Gemma 4 + Qwen3-Coder-Next benchmarks | NOT STARTED | per Phase 17 plan |
| D-17-13 (historical: 17.M): Goose agent CLI integration | NOT STARTED | per Phase 17 plan |
| D-17-14 (historical: 17.N): exo distributed inference cluster | DONE (PARTIAL — distributed inference not operational; see `docs/architecture-facts/exo-cluster.md`) | 86600b8+0d6ebf3+a025827+1dc2f3b+ede9480+726725a+f90ce04 |
| D-17-15 (historical: 17.O): Mac Studio Day-1 execution | DONE | ccc02d1 |
| D-17-16 (historical: 17.P): Loose-doc retirement | NOT STARTED | re-parented from D-16-05 |
| D-17-17 (historical: 17.Q): Logical service architecture dashboard with live utilization (replaces original OpenProject framing) | NOT STARTED | re-parented from D-16-08 |
| D-17-18 (historical: 17.R): Physical architecture visualization (Structurizr + network/storage paths; original Structurizr-only framing now T1 of this deliverable) | NOT STARTED | re-parented from D-16-09 |
| D-17-19 (historical: 17.S): Article-intake findings consolidated to repo | DONE | 4ece268 |
| D-17-20 (historical: 17.T): D#17/D#18/D#19/D#20/D#21 codified | DONE | b86bc55 |
| D-17-21 (historical: 17.U): OPNsense DNS state audit + Unbound disable + retroactive Vault incident review (KI-009 follow-up; estimated 6-8h) | NOT STARTED | per Phase 17 plan |
| D-17-23: Capability self-knowledge + workaround surfacing | DONE | dcc2ca4 |

ID-reservation note: D-17-22 (multi-session role + intake architecture)
is RESERVED but not yet framework-authored. Discussed in a prior
session; lives as a parking-lot item pending its own intake doc +
framework-add commit. Reserving the ID preserves the parking-lot
reference without forcing premature scope authoring. Sized similar
to D-17-23 (~2-3h doctrine-shaped) when it lands.

Identifier-convention note: Phase 17 was originally authored using
shorthand "17.X" deliverable IDs and "WP-17-D-NN" work-package IDs.
Migrated to canonical D-NN-MM and WP-NN-MM-XX form (per §1
vocabulary) on 2026-05-02 in WP-17-04-01.5, before WP-17-04-02 (Plane
data export) preserved old IDs as historical primary keys. Canonical
mapping in `docs/architecture-facts/identifier-conventions.md`. The
`(historical: 17.X)` annotations remain for one cycle to support
grep-by-old-form during the grace period.

Sequencing: D-17-01 → D-17-02 → D-17-03 (foundation) before Tier 2;
D-17-02 before D-17-05/06/07/08 (template consumed); D-17-06 before
D-17-17 (KEEP/RETIRE verdicts must settle before topology overlay
surfaces utilization on retired services); D-17-17 before D-17-18
(logical-layer overlay informs physical visualization); D-17-15 before
D-17-14; D-17-10 before D-17-12/13/14. D-17-23 before D-17-11
(capability-permission slot must be defined before the system prompt
library fills it). D-17-21 gates the .internal route in D-17-04's
WP-17-04-01 (IP+port deploy proceeds; Caddy site binding waits on
DNS authority resolution).

Phase 16 carry-overs (D-16-03/05/08/09) marked DEFERRED to Phase 17
in §8 — see Phase 17 IDs D-17-15/16/17/18 for new tracking.

**OpenProject mirror:** `http://192.168.10.145:8086/projects/roadmap/work_packages?query_props=...&filters=customField2:Phase-17`
(Phase-17 Version + 670 imported WPs; canonical PM substrate as of D-17-04 2026-05-01.
 Plane CE retired 2026-05-01 in WP-17-04-06 — historical mirror URL no longer reachable.)

---

## 10. References

- `docs/PHASE_LOG.md` — historical phase records (pre and post consolidation)
- `docs/PHASE_ROADMAP.md` — upcoming roadmap
- `docs/runbooks/operating-model.md` — multi-window operating discipline
- `docs/adr/` — architectural decisions (immutable once Accepted)
- `CLAUDE.md` — current operational truth (root)
- `docs/ARCHITECTURE.md` — current architecture (supersedes PLATFORM_OVERVIEW.md)
- `docs/phase-15/COMPREHENSIVE_AUDIT_2026-05-01.md` — current-phase audit (committed 3105f07)
- `docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` — current-phase audit validation (committed 3105f07)
