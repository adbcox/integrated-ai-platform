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
| `RM-NN-X-NNN` | Roadmap scope item (Phase NN, sub-block X, ordinal). Sourced from `docs/PHASE_ROADMAP.md` §16/§18 sub-block scope bullets; mirrored to OpenProject by `scripts/openproject-sync-from-framework.py --include-roadmap`. Distinct from the older `RM-A11Y-*` / `RM-API-*` autonomous-coding micro-task corpus. |

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
`docs/_audit/stack-architecture-2026-05-01.md` as the template.
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

### D#25 — Service Registry consultation before port/dependency operations

Before any operation involving container ports, internal addresses,
service dependencies, or external (Caddy) routing, AI sessions MUST
consult the Service Registry at `~/.platform-registry/inventory.json`
(or `by-service/<service>.json` for a single record). The registry is
the canonical source of truth for: container_name ↔ service_id,
host_port ↔ container_port mapping, internal IPs per docker network,
depends_on/depended_on_by graph, attached Caddy routes, and credential
file metadata (paths + fingerprints, never values).

Convenience reader:
```python
import sys; sys.path.insert(0,'/Users/admin/repos/integrated-ai-platform/scripts/platform-registry/lib')
import registry_writer as rw
rw.query('seal-vault')  # → dict, or None if unknown
```

If `last-refresh.json` is older than 30 minutes, run
`scripts/platform-registry/refresh.sh` before consulting (full refresh
is ~1 second on this platform). Stale registry data is a doctrine
violation in itself.

**Failure mode prevented:** D-17-28 (2026-05-02) — seal-vault recovery
cost ~3 hours because AI guessed port 8200 (the Vault default) instead
of 8201 (the actual binding established earlier). The registry
mechanically eliminates this archaeology pattern. Spec:
`docs/architecture-patterns/service-registry-mvp.md`. Builder code:
`scripts/platform-registry/lib/`. Closed by D-17-29.

**Sub-doctrine (D-17-26 close, Finding DD): container env inspection.**
When inspecting container environment for credential or runtime-set
variables, query `/proc/1/environ` rather than spawning a fresh shell
via `docker exec env`. Image-baked `Config.Env` ≠ runtime PID 1
environ when entrypoint scripts source secret files. Correct check:

```
docker exec <container> sh -c 'tr "\0" "\n" < /proc/1/environ | grep ^VAR='
```

D-17-14 WP-06 close ("`OPENAI_API_KEY` effectively empty") was a
diagnostic error caused by `docker exec env`-style inspection; D-17-26
was scoped on that wrong premise and closed in 25 min as
no-fix-needed once the correct check was applied. Apply this pattern
before reporting a credential as missing/empty.

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
| D-17-12 (historical: 17.L): Gemma 4 + Qwen3-Coder-Next benchmarks | DONE | 2026-05-04 — T3 adoption gate cleared via WP-07 decision matrix + WP-03 tier doctrine on objective benchmark data (operator hand-grade of 12 packets remains parked; matrix uses tps + auto-graded scores + structured-emission rate as decisional axes per agreement that hand-grade refines per-workload scores without re-shaping per-class recommendations). Per-class recommendations: C1a → T1 under explicit operator-side review (T2 fallback; T3-A excluded on no-tool-support; T3-B-via-Goose SUSPENDED per D-17-53 cell suspension, not a tier exclusion); C1b → T3-B default (T1 fallback); C2 → T3-B default (T1 fallback); C3 → T3-B default (T1 fallback); C4 → T1 default (T3-B fallback) — conservative until doctrine-drafting tested for failure-mode-attractor shape; C5/C6 Phase-C not yet migrated; C7/C8/C9 CONTROL never migrate; C10 → T2 mechanical / T3-B with-tool. Six tier-selection rules encoded (tool-call binary, lc-8K binary, capability-surface boundaries not tier-selectable, throughput tiebreaker only, cell suspensions don't propagate, auto-grade biases cannot flip ordering). Three falsified hypotheses chronicled (substrate-shape correlation FALSIFIED at N=2 D-17-53; single-clean-datapoint sampling-artifact STRENGTHENED; qwen2.5-coder structured-tool-call DISPROVEN as serving-stack issue per Finding 1.B). Tier inventory: T1=`qwen2.5-coder:32b` Mac Mini 32K-no-tools; T2=`qwen2.5-coder:14b` Mac Mini 32K-no-tools; T3-A=`gemma2:27b` Mac Studio 8K-no-tools (Ollama HTTP 400); T3-B=`qwen3-coder:30b` Mac Studio 256K-structured-tools (3B/30B MoE, 49–102 tps). Headline benchmark numbers (post-G1): T1 lc 0.86 / refactor 1.00 / tc 0.91 inline / agentic 0.62 (9–14 tps); T2 lc 0.87 / refactor 0.94 / tc 0.91 inline / agentic 0.71 (18–30 tps); T3-A lc 0.75 1/5 / refactor 0.94 / tc n/a / agentic 0.79 (24–35 tps); T3-B lc 0.84 / refactor 1.00 / tc 0.93 structured / agentic 0.83 (49–102 tps); T3-B 3.4× T2 throughput at 30B-class capability. Artifacts: `docs/phase-17/d-17-12/WP07_DECISION_MATRIX_2026-05-04.md` (per-class headline + per-workload appendix + hand-grade fold-in pattern); `docs/architecture-facts/local-model-tier-doctrine.md` (tier inventory, capability boundaries, six selection rules, falsified-hypothesis section, future-tier addition pattern). Cell-change branch (gemma2:27b on C1a, larger qwen variants on C1a) deferred as future deliverable per D-17-53 disposition. Hand-grade fold-in pattern documented: when 12 packets land, deltas apply to per-cell scores; predicted to flip zero per-cell verdicts (gaps exceed bias band) and zero per-class recommendations (rest on tier-vs-tier gaps not absolutes); hand-grade results would land at `WP06_HANDGRADE_RESULTS_<date>.md` and link from matrix appendix. Original-scope text retained: candidates substituted to verified upstream — `google/gemma-2-27b-it` (Gemma 4 26B MoE was aspirational; not yet released as of cutoff) + `Qwen/Qwen3-Coder-30B-A3B-Instruct` (verified MoE, fits Mac Studio's 96 GB unified pool cleanly). Serving substrate: Ollama-on-Mac-Studio (`brew install ollama` + `ollama serve` daemon at `192.168.10.142:11434`) for apples-to-apples fairness with Mac Mini Ollama T1/T2 baselines. T1/T2 baselines locked: T1=`qwen2.5-coder:32b` Ollama Mac Mini; T2=`qwen2.5-coder:14b` Ollama Mac Mini. Provenance gate runs against HF source per existing kit semantics with `PROVENANCE_OVERRIDE_REASON="D-17-12 benchmark; documented in deliverable per model-provenance.md doctrine line 220-235"` (catalog v1.0.0 has Gemma family absent + code-fine-tune coverage gap; override is the doctrine-pre-authorized path and the bypass-frequency data is itself evidence for upstream-contribution case). 4 workloads: long-context reasoning (16K+ tokens), multi-file code refactor (5+ files), tool-call adherence (`stream:false` direct-curl only — agent-integration deferred pending local-tool-calling Findings 1+2 unblock), autonomous agentic. Hard cap 6h Mac Studio compute. Surface backs at WP-06 (grading) + WP-07 (decision matrix). Workspace: `docs/phase-17/d-17-12/`. |
| D-17-13 (historical: 17.M): Goose agent CLI integration | DONE | 2026-05-03 close — Goose+T3-B execution-surface validated end-to-end. Reopened 2026-05-03 on F1 unblocker per D-17-12; closed same day after WP-03 substrate verification + WP-06 first-test deliverable. **F1.B (the actual unblocker):** qwen3-coder:30b emits structured `tool_calls` in *streaming* mode via Ollama 0.22.1 — refines the original F1 along (model-family × Ollama-version) axis. Goose's ollama provider hard-codes streaming on, so this is the cell that matters for adoption. Chronicled at `docs/architecture-facts/local-tool-calling.md` Finding 1.B (between F1 and F2). **WP-03 substrate:** native ollama provider + qwen3-coder:30b on Mac Studio (no litellm hop, no Vault credential surface). End-to-end smoke test verified 2 tool calls (filesystem-mcp `read_text_file` + `list_allowed_directories`); 6-call WP-06 session also clean. **WP-04 repo integration (commit `e1f884b`):** `config/goose/config.yaml` repo-mirrored; old `goose-platform.sh` renamed `goose-via-litellm-historical.sh` with obsolescence header; `scripts/goose/README.md` pointer doc. Commit identity (separate goose-bot author) deferred to Phase-A promotion per Q2=(a). **WP-05 capability boundary (commit `3c1d554`):** `docs/architecture-facts/goose-capability-boundary.md` chronicle. Read-only substrate only: `filesystem-mcp` + `xindex` enabled; `developer` (shell exec + file write), `summon`, `apps`, `chatrecall`, `summarize`, `tom`, `code_execution`, `orchestrator` disabled. Operator review mandatory on all output. Phase-A promotion gate fixed in writing (N≥5 clean reviewed executions, F1.B substrate stability, operator decision). **WP-06 first test deliverable (commit `f5ff90c`):** Goose drafts `docs/runbooks/goose-operations.md` from 3 source files. 51s wall-clock, 6 tool calls all valid + in-scope. Output split: ~75% Goose / ~25% frontier correction during review (padding sections dropped, `GOOSE_MODE=auto` headless pattern added, §3.3 hang causes deepened, redundant capability list dropped, provenance suffix added). First measured §18.O execution-surface migration economics datapoint. Cautious-by-default pattern (model autonomously runs `list_allowed_directories` before reads) preserved for Phase-A re-enable design. **WP-07 dual-review:** PM-side observations folded into capability-boundary chronicle "Observed behavior" section. Surface-back fidelity high; cost delta validates §18.O thesis. **WP-08 promotions:** F1.B → `local-tool-calling.md` Finding 1.B; F1.B.1 emission-noise sub-finding in same section; F14 (mDNSResponder negative-cache sub-doctrine, sibling to D-17-21 authority doctrine) → `integration-audit-doctrine.md` Finding 14 + `opnsense-dns-authority.md` "Consumer-side cache invalidation" section; CLAUDE.md "Execution surfaces" subsection added (Goose joins Claude Code + Codex; LLM-access mode is a different axis). **Backlog (not blockers):** framework script gap — `roadmap-create.sh --reopen` mode for DONE → IN PROGRESS reopens on unblocker resolution. **Prior eval (10bc41f):** install + config + MCP wiring all green; tool loop blocked-upstream by F1 (qwen2.5-coder × Ollama 0.20.7 streaming dropped tool_calls). Eval artifact: `docs/phase-17/d-17-13/EVALUATION_2026-05-03.md`. Reopen artifacts: `docs/phase-17/d-17-13/{WP02_INSTALL,WP08_CHRONICLE_NOTES}.md` + `wp06-evidence/`. |
| D-17-14 (historical: 17.N): exo distributed inference cluster | DONE | 86600b8+0d6ebf3+a025827+1dc2f3b+ede9480+726725a+f90ce04 |
| D-17-15 (historical: 17.O): Mac Studio Day-1 execution | DONE | ccc02d1 |
| D-17-16 (historical: 17.P): Loose-doc retirement | DONE | 2026-05-03 — 48 loose docs walked, 9 clusters processed, 0 outside canonical paths post-close. **WP-02 inventory** at `docs/_audit/loose-doc-inventory-2026-05-03.md` surfaced 48 files (under the >50 surface-back threshold by 2; operator gate on 3 directory-canonicalization decisions invoked anyway: (a) `docs/architecture/` → fold into `docs/architecture-facts/` with renames `mcp-server-architecture.md`→`mcp-servers.md` + `portability.md`→`host-portability.md` (+ Mac Mini M5→M4 Pro drift fix during the move, sibling to D-17-18 .146→.142), (b) `docs/system-prompts/` → canonical-as-is preserving D-17-11 self-contained library shape, (c) `docs/zabbix/` → consolidate to single `docs/runbooks/zabbix-operations.md` + Phase-12 retro fragments → `docs/_archive/phase-12/`). **WP-03 batch** ~48 `git mv` operations: Cluster A (top-level audits + 2 misplaced runbooks: `*_AUDIT_2026-05-01.md`→`_audit/`, `nextcloud-caldav.md`→`runbooks/`, `PLATFORM_OVERVIEW.md`→`_archive/`, `phase-9-completion.md`+`phase-10-validation-report.md`→`_archive/phase-NN/`); Cluster B (`docs/architecture/` 3 files folded into `architecture-facts/` with renames per WP-02); Cluster C (12 files `docs/audits/capability/`→`docs/_audit/capability/`); Cluster D (openproject-connector→`architecture-patterns/`; plane-connector→`_archive/` since Plane CE retired in WP-17-04-06); Cluster E (`performance/baseline-metrics.md`→`_archive/phase-10/`); Cluster F (2 `docs/phases/*` files→per-phase `_archive/phase-NN/`); Cluster G no-op; Cluster H (`templates/capability-audit-template.md`→`architecture-patterns/`); Cluster I (consolidated runbook authored ~150 lines covering SNMP add procedure with OPNsense+QNAP worked examples + Mac Mini native agent + Grafana integration + security checklist + backups + known trade-offs; 7 originals all archived to `_archive/phase-12/`). 9 empty-dir retirements. **WP-04 cross-reference verification** fixed 10 live-doc references: CLAUDE.md (PLATFORM_OVERVIEW path); ARCHITECTURE.md (PLATFORM_OVERVIEW + M5→M4 Pro drift fix + mcp-server-architecture rename); PHASE_ROADMAP.md (STACK audit path); PROJECT_FRAMEWORK.md (STACK audit + dependency-graph replace_all); observability-doctrine.md (4 path refs); ADR-A-006 (rewrote consequences for post-D-17-16 + post-D-17-04 OpenProject reality); ADR-A-014 (dependency-graph path); ADR-A-016 (D-17-16 supersession status note + Related update); ADR-A-001/A-008/A-010 (path-corrected source claim, plus A-010 OSS_REUSE_AND_ADOPTION_REGISTER deletion note); DECISION_REGISTER.md (canonical-patterns merged note on A-016 row); plus sed-batched fixes for 5 stale `docs/audits/capability/` refs in `docker/_retired/anythingllm/README.md` + `docker/_retired/homarr/README.md` + `docker/_retired/zabbix-exporter/README.md` + `docker/_rewire-log/2026-05-01-homarr-retirement.md` + `docs/architecture-patterns/capability-audit-template.md` + `docs/_audit/capability/victoriametrics-2026-05-01.md` + `docs/_retired/sportarr-2026-05-01.md` (templates+STACK paths). 2 `docker/_retired/*.parked.yml` audit-comment headers manually fixed. Frozen retros (`docs/phase-13/`, `docs/phase-14/`, `docs/phase-15/`, `docs/phase-17/d-17-34/`, `docs/_archive/phase-1[12]/`) left alone per frozen-retrospective doctrine. **Out-of-scope deferred** with explicit identification (not silent skips): Phase-8-era roadmap-executor pipeline (`bin/auto_execute_roadmap.py` + `config/systems.yaml` + `tests/regression/test_end_to_end.py` reference long-deleted `docs/roadmap/ITEMS/` — graceful-fallback in code; own retirement deliverable); CI workflow `.github/workflows/validate-infrastructure.yml` lines 230-232 reference `docs/architecture/{MASTER_SYSTEM_ARCHITECTURE,DECISION_REGISTER,AUTHORITY_SURFACES}.md` (Phase-8 deletions, broken-but-non-blocking for 8+ phases); AnythingLLM `bin/ingest-docs.py` `WORKSPACE_DOCS` preset references several Phase-8 deletions (graceful SKIP path at line 270-273; AnythingLLM has zero indexed docs per D#20 — own retirement deliverable). **WP-05 doctrine + chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 10 appended (~120 lines: observation + 5-WP doctrine surface + 6 subsidiary rules including frozen-retrospective doctrine + self-referential migration notes + drift-sibling-fixes-welcome + out-of-scope-discipline + worked example + refresh cadence + cross-references to D-17-21 / D-17-18 / ADR-A-016 / Finding 9). **Final canonical-paths state:** `docs/{ARCHITECTURE.md, PROJECT_FRAMEWORK.md, PHASE_ROADMAP.md, DECISION_REGISTER.md, _archive/, _audit/, _provenance/, _retired/, adr/, architecture-facts/, architecture-patterns/, dashboards/, known-issues/, phase-NN/, runbooks/, system-prompts/, troubleshooting/}` — closed set. Re-parented from D-16-05. Phase 17 progresses 31/31 → 32/31 (D-17-16 only; D-17-12 remains IN PROGRESS owned by separate session, D-17-35 remains IN PROGRESS pending real PDF). |
| D-17-17 (historical: 17.Q): Logical service architecture dashboard with live utilization (replaces original OpenProject framing) | DONE | demo-prep deliverable for Saturday 2026-05-09; static HTML rendered from `~/.platform-registry/inventory.json` (D-17-29 substrate) — 76 service cards grouped by stack swim lanes, 13 orphans surfaced, dependency arrows, health colour, hover detail with credentials_meta (path/mode/12-char fingerprint only — Finding ZZ compliant); live `docker stats` snapshot embedded at generation time. Generator: `scripts/dashboards/generate_logical_architecture.py`. Output: `docs/dashboards/logical-service-architecture.html` (93,754 bytes). Caddy route `architecture.internal` → `host.docker.internal:8765` (host-side python http.server). Smoke + deferral notes: `docs/phase-17/d-17-17/SMOKE.md`. Screenshot deferred — no GUI session on Mac Mini control window (Chrome headless / screencapture both blocked); HTML artifact is canonical. |
| D-17-18 (historical: 17.R): Physical architecture visualization (Structurizr + network/storage paths; original Structurizr-only framing now T1 of this deliverable) | DONE | sister deliverable to D-17-17 — static HTML at `docs/dashboards/physical-architecture.html` (13,483 bytes). 6 hardware nodes (Mac Mini .145 / Mac Studio .142 / Threadripper pending / QNAP .201 / HA .141 / OPNsense .1 26.1.6), 7 network links (LAN / TB5 bridge / VPN-overlay placeholder), 5 storage paths (Vault data / audit log / Docker volumes / media / HF cache). Reachability probed at render time (5/5 active reachable). Generator: `scripts/dashboards/generate_physical_architecture.py`. Caddy route `physical-architecture.internal` → `host.docker.internal:8765` (shared static server with D-17-17). Mac Mini node card cross-links to `architecture.internal` for sister-view navigation. Visual style matches D-17-17 for demo coherence. Hardware facts sourced from CLAUDE.md hardware block + `docs/architecture-facts/exo-cluster.md` (Mac Studio JACCL coordinator IP) + `docs/architecture-facts/opnsense-dns-authority.md`. Threadripper rendered as "pending hardware" placeholder, no invented state. Structurizr workspace retained at `docker/structurizr/workspace/workspace.dsl` for future structured-DSL work (related to D-16-09 spirit, deferred). Smoke + deferral notes + CLAUDE.md drift surface: `docs/phase-17/d-17-18/SMOKE.md`. Screenshot deferred (no GUI session, same as D-17-17). **Surfaced drift:** CLAUDE.md hardware block lists Mac Studio at `.146`, actual is `.142` (ping + ARP confirmed; D-17-24 reused stale value during rewrite — recommend follow-up correction). |
| D-17-19 (historical: 17.S): Article-intake findings consolidated to repo | DONE | 4ece268 |
| D-17-20 (historical: 17.T): D#17/D#18/D#19/D#20/D#21 codified | DONE | b86bc55 |
| D-17-21 (historical: 17.U): OPNsense DNS state audit + Unbound disable + retroactive Vault incident review (KI-009 follow-up; estimated 6-8h) | DONE | 2026-05-03 — DNS authority migrated programmatically from Unbound (residue) to Dnsmasq (operator-canonical). **WP-02 audit overturned the 2026-05-01 provisional doc:** Unbound was the de-facto authority on port 53 with **38 `.internal` host overrides** (visible only via `searchHostOverride`, not the `settings/get` `.unbound.hosts` field the provisional doc had probed); Dnsmasq held 6 bare-hostname records on port 53053. Operator pushback on WP-03 surface re-stated canonical posture: **Dnsmasq is sole authority; Unbound is unintended residue; disable completely; no GUI work**. **WP-04 executed end-to-end via OPNsense API** (`scripts/d-17-21-dns-migration.sh`): snapshot pre-state → addHost loop migrated 38 Unbound + 12 new (`architecture/docs/homeassistant/inventree/loki/mac-studio/mcp-xindex/netbox/openproject/physical-architecture/structurizr/xindex`.internal) → reconfigured Dnsmasq → validated all 50 records resolve on port 53053 → `unbound.general.enabled=0` + service stop → Dnsmasq port 53053→53 → reconfigured → final smoke 0 resolve failures on :53. **Post-migration corrections:** (1) `homeassistant.internal` re-pointed from .141 (HA hub direct) → .145 (Caddy front; Caddy proxies to .141:8123); (2) `dashboard.internal` removed (operator-noted candidate retirement, pruned from Caddy in 3db56c7); (3) `_dns_match` Shape priority bug fixed in `scripts/check-repo-coherence.py` — bare-hostname (Shape 3) was matching ahead of explicit-`.internal` (Shape 1) when iteration order favored bare row, causing false `wrong_target` on services with both DHCP-paired bare hostname and Caddy-front `.internal` record (worked example: homeassistant). Final parity check: `caddy-dns-parity` exit 0, `missing=0, wrong_target=0, extra_internal=16` (informational; non-Caddy direct-port services). **WP-05 KI-009 retroactive Vault incident review:** traced 2026-04-30 Sev-2 `api_addr` userland-proxy saturation incident — root cause was IP-literal `192.168.10.145:8200` forcing every redirect to U-turn through Docker Desktop's userland-proxy with 38 vault-agent sidecars saturating the queue; **DNS path never invoked** for the literal IP. Conclusion: no DNS contribution to Vault incident; KI-009 status flipped to RESOLVED (advisory-mode pre-commit gate auto-resumes strict-fail behavior on file's `**Status:**` line). **Doctrine:** new `CLAUDE.md` "DNS Authority Doctrine (D-17-21)" section (8 bullets — Dnsmasq as sole authority + Unbound as forbidden + record-add procedure + parity-check enforcement + Shape priority + audit-against-intent rule + migration-script-as-pattern + chronicle pointers); `docs/architecture-facts/integration-audit-doctrine.md` Finding 9 appended (~70 lines: configuration-audits-verify-against-operator-intent + residue-as-positive-failure-mode sub-doctrine + re-probe-an-audit's-premises sub-doctrine + migration-pattern-7-steps + parity-check-shape-priority sub-doctrine + KI-009 retroactive review). **Architecture-fact rewrite:** `docs/architecture-facts/opnsense-dns-authority.md` flipped from PROVISIONAL → VERIFIED with Dnsmasq-as-sole-authority rationale; KI-009 file flipped to RESOLVED with full close-out summary. Phase 17 progresses 30/31 → 31/31. |
| D-17-32: Autonomous coding stack integration audit (gap report + prioritized hardening backlog; no code changes; informs subsequent remediation deliverables) | DONE | 2026-05-03 — audit traced 6 target flows (Inference / InvenTree / Asset-firmware / Provenance / Documentation / PM) end-to-end; **17 gaps catalogued** with severity B/D/N + roadmap-item / queue / tagging mapping. **4 B-severity blockers in seams (not subsystems):** F1 `autonomous-coding` category missing in OpenProject (CLAUDE.md doctrine references nonexistent filter — D-17-31 close-loose-end); X1 service registry has no MCP/agent surface (D#25 doctrine has no clean execution path — D-17-29 close-extension); C1 no asset/firmware/OS register (the 2026-05-02 macOS-upgrade incident is the worked example — asset-mgmt family intake-doc'd but not framework-authored); F5 container health checks validate liveness not integration paths (the 2026-05-03 Sonarr/QNAP SMB mount break went undetected by all platform health signals — surfaced only by operator-observed import failure in separate troubleshooting session; Phase 6/7 close-extension, integration-health-check family proposed). 8 D-severity (Studio Ollama not in litellm, route enumeration multi-step, InvenTree empty + no axis, no provenance enumeration, architecture-facts not searchable in xindex, CLAUDE.md `--query-backlog` flag doesn't exist, RM-HW-* stranded in plane archive — F4 surfaced via parallel-session cross-check). 5 N-severity (mostly upstream-blocked or trivial doc fixes). Audit doc at `docs/_audit/integrated-stack-target-2026-05-03.md`; gap report at `docs/_audit/integrated-stack-gaps-2026-05-03.md`; prioritized backlog at `docs/_audit/integrated-stack-backlog-2026-05-03.md`. **New doctrine chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` — stack-integration audit becomes recurring deliverable at every phase boundary (Finding 1: subsystem closure ≠ integrated-system capability; B-severity gaps concentrate in seams *between* subsystems). Sub-doctrines: close-loose-end discipline (verify doctrine lines against actual surfaces at close time), operator-side actions count as gaps, negative datapoints reported honestly, **"container `(healthy)` is not `(integration working)`"** (deliverables asserting "monitoring complete" must state which layer — container liveness vs integration-path validation — is covered, and not the other). **No remediation deliverables auto-created** — operator queues B1/B2/B3/B4 + D-tier candidates in next planning pass per audit-only constraint. Parallel-session cross-check (operator concern about ESP32 artifact created via different chat window) found nothing was created by that session; surfaced pre-existing F4 (RM-HW-001/002 stranded in plane archive from D-17-04 close). F5 added late in T5 under operator instruction after empirical confirmation via separate Sonarr troubleshooting session. |
| D-17-34: Home Assistant architecture reconciliation — duplicate instance regression (Mac Mini container still running despite operator-recalled removal validation ~2 days ago; F7 false-positive completion pattern surfaced in D-17-32 audit context) | DONE | 2026-05-03 — investigation confirmed Mac Mini HA container was a stray (zero live consumers, REST sensors broken, canonical HA at 192.168.10.141 reached via Caddy `home.internal`). Phase-15 audit (`docs/phase-15/COMPREHENSIVE_AUDIT_VALIDATION_2026-05-01.md` §4.7) had reached the same retirement verdict + 4-step plan on 2026-05-01; operator confirmed in conversation; **none of the 4 steps were ever executed** — F7 worked example #2 (alongside D-17-32 Gap F5 Sonarr/QNAP mount break = #1). Executed deferred retirement: pre-flight log verify (REST sensor errors only, no surprise activity) → QNAP archive (`/share/CACHEDEV2_DATA/downloads/manual/D-17-34-ha-container-retirement/`, 3.9 MB tar.gz, SHA256 `4fe65026aa6d…b5f173`, 90-day retention to 2026-08-01) → container stop+remove → compose retirement marker → registry refresh (homeassistant.json gone from `~/.platform-registry/by-service/`) → Vault cleanup (AppRole + policy + on-disk role-id/secret-id + Vault Agent secret dir + repo policy file all revoked; `secret/homeassistant/api` data retained for potential .141 consumer per scope) → CMDB updates (`docs/architecture-facts/dependency-graph.md` dropped `homeassistant-container` + 2 dead Obot shim refs, updated `homeassistant-physical` label to `.141 (canonical)`; `docs/ARCHITECTURE.md` dropped integration-container row + updated dashboards stack row to retired-state; `CLAUDE.md` Hardware block added explicit `.141` HA hub entry). **3 new findings** authored into `docs/architecture-facts/integration-audit-doctrine.md`: Finding 2 (F7 false-positive completion regression — audit recommendations require executed validation, not conversation agreement; sub-doctrine "container `(healthy)` is not `(supposed to exist)`"); Finding 3 (stranded Vault AppRoles outlive their consumers — 5-artifact-class cleanup checklist; mirror failure mode to D#25 plane-web example); Finding 4 (CMDB authority unenforced — three substrates can disagree silently between NetBox / `service-registry.yaml` / `~/.platform-registry/inventory.json`). CMDB reconciliation deliverable + `retire-service.md` runbook **proposed but NOT auto-created** per operator instruction — operator decides scope in next planning pass. Closeout: `docs/phase-17/d-17-34/CLOSEOUT_2026-05-03.md`. Cross-references D-17-32 Gap F5 + Gap X1; unblocks D-17-33 Overwatch scoping. |
| D-17-23: Capability self-knowledge + workaround surfacing | DONE | dcc2ca4 |
| D-17-25: macOS alignment + RDMA hypothesis test (D-17-14 follow-on) | DONE | 7bdb537 — Outcome C: alignment necessary but not sufficient; Findings U+V surfaced. Reproducer evidence at `docs/phase-17/d-17-25-wp-05-multinode-evidence/`; chronicle in `docs/architecture-facts/exo-cluster.md` (Findings U, V + updated "Not operational" + revisit triggers); runbook in `docs/runbooks/exo-cluster-operations.md` updated. |
| D-17-29: Service Registry MVP — port-discovery archaeology unlock + autonomous-coding substrate | DONE | f47171f — spec at `docs/architecture-patterns/service-registry-mvp.md` (c34d48f); builder at `scripts/platform-registry/lib/` (compose_parser 655764a, docker_inspector 048a047, caddy_reader 8b2501a, credential_finder e8da839, registry_writer 342217b); refresh entrypoint + launchd at a63043f; doctrine D#25 + CLAUDE.md at f47171f. 40/40 integration tests; full refresh in 1.0s producing 76 services + 13 runtime orphans + 31 caddy routes + 125 credential files (metadata-only per Finding ZZ). Spec §10 success criteria all green: canonical seal-vault host_port=8201 query verified. Closes Finding CC. KNOWN: launchd plist installed but not registered (Finding Y; will load on next login). |
| D-17-26: Open WebUI exo surface via Vault Agent sidecar (existing-but-broken) | DONE | no-fix-needed-with-doctrine-finding. Plumbing was operational the whole time: Open WebUI PID 1 environ has `OPENAI_API_KEY` length=67, byte-identical fingerprint to litellm's `LITELLM_MASTER_KEY` (`439bcdb691d6` == `439bcdb691d6`); `GET http://litellm-gateway:4000/v1/models` from open-webui with bearer auth → HTTP 200 with `exo-qwen-coder-7b` listed. The broken-state premise was a diagnostic error (Finding DD: `docker exec env` reads image `Config.Env`, not PID 1 runtime environ). Closes Finding S; surfaces Finding DD; doctrine added to D#25 corpus. End-to-end demo path requires exo bring-up (separate provisional scope D-17-30). |
| D-17-30: Open WebUI → litellm → exo end-to-end demo verification (single-node) | DONE | exo single-node bring-up on Mac Mini (peer-id `12D3KooWAUqbiNsXfU2muNNN`, runner `RunnerReady`, MlxRing 1 shard 28 layers); Qwen2.5-Coder-7B-Instruct-4bit (4.28 GB) placed via `POST /instance` from `/instance/previews?model_id=…` (runbook said `POST /instance/preview` singular — corrected, see WP-05 note). Direct exo: TTFT 0.404 s, sustained 54.6 tok/s on 130-chunk stream. Through litellm-gateway: 0.64 s wall. Through `open-webui` container's network namespace into the same chain: 0.42 s wall, output "PARIS" — chain confirmed end-to-end. OWU `/v1/models` from inside the container lists `exo-qwen-coder-7b` + 5 ollama routes (6 total). UI splash captured at `docs/phase-17/d-17-30/open-webui-auth.png`; inside-app screenshot deferred (would require auth cookie; API-level evidence is stronger). Metrics doc: `docs/phase-17/d-17-30/latency-metrics.md`. exo route already wired into `litellm_config.yaml` from D-17-14 WP-06 (no config change needed). Demo-ready for Saturday 2026-05-09. |
| D-17-31: Roadmap → OpenProject sync (extend framework-only sync to ingest PHASE_ROADMAP.md scope sections) | DONE | d4ccfc4 — structural fix for "what's next" drift. New parser `scripts/lib/roadmap_parser.py` (250 lines, pure parser, no API) emits one `RoadmapItem` per scope bullet under Phase 16/18 sub-block headings; ID scheme `RM-<phase>-<sub>-<NNN>` (operator-approved 2026-05-03 — distinct from the legacy `RM-A11Y-*` autonomous-coding micro-task corpus). Extended `scripts/openproject-sync-from-framework.py` (+314 lines) with `--include-roadmap`, `--roadmap-only`, `--dedup-phase17` flags. WP-04 result: 53 RM WPs created across 7 sub-blocks (Phase-16 16.A/B/C 28 items, Phase-18 18.A/B/C/D 25 items), 20 auto-flagged with `autonomous-coding` category via positive/negative regex heuristic; Phase-18 OP version auto-created. Phase-17 dedup closed all 20 shorthand WPs (`17.A`–`17.T`) as superseded by `D-17-NN` canonicals — preserves migration history. Status drift on RM items is operator-owned (sync refreshes title/description only, never overwrites status). Two latent connector bugs fixed in `framework/openproject_connector.py`: `create_module()` was POSTing to project-nested `/projects/{id}/versions` (404) — corrected to root `/versions` with `_links.definingProject`; `ensure_label()` was attempting to POST a category (API v3 categories are read-only) — now raises typed `CategoryNotFoundError` with description-text fallback in sync. Root cause hypothesis (Plane → OpenProject endpoint pattern carry-over) chronicled in new `docs/architecture-facts/openproject-migration.md`. Doctrine added to CLAUDE.md: "what's next" answers consult OpenProject queue, not framework §9 alone; sync flag inventory documented. |
| D-17-24: CLAUDE.md staleness sweep — point to canonical sources not duplicate phase state | DONE | f76ac51 — structural fix for Finding L. Removed Phase-16-stale "Current Phase:" wall (was driving auto-prioritization of obsolete deliverables across ~3 sessions). Replaced with "Phase / deliverable state — DO NOT duplicate here" pointer block: §9 of THIS file is canonical, plus `docs/PHASE_ROADMAP.md`, `docs/phase-NN/PHASE_NN_PLAN_<date>.md`, `docs/phase-NN/PHASE_NN_*_CLOSEOUT_<date>.md`, `git log --oneline -20 docs/PROJECT_FRAMEWORK.md`, and `~/.platform-registry/inventory.json` (D#25 substrate). Auto-prioritization rule added: deliverables not in §9 of latest framework are treated closed-or-superseded until proven otherwise. Other refreshes: Hardware block restructured; Mac Studio updated from "future" to "compute node as of 2026-05-01"; Post-Block-2 Follow-up List retired (Phase 13 vocabulary, items 1+4 long-DONE); stale "601 roadmap items" line replaced with OpenProject sync paragraph. Doctrine D#1-D#25 (incl. D#25 sub-doctrine for Finding DD) and all operator standing rules preserved verbatim. File 197 → 230 lines, diff +52/-18 (~35% structural change, under 50% surface-back threshold). |
| D-17-37: Roadmap artifact storage substrate (QNAP-canonical filesystem layout + `qnap://` pointer scheme + sibling registry axis + ingest/resolve scripts + ACL classes; closes Gap F9 — binary inputs ingested to chat context but never persisted on filesystem) | DONE | 2026-05-03 — substrate end-to-end: storage layout `/Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts/<phase>/<deliverable>/{source,extracted,annotations}/` with `metadata.yaml` at deliverable root; pointer scheme `qnap://download/manual/roadmap-artifacts/...` (resolver `scripts/artifact-resolve.sh`); ingest entrypoint `scripts/artifact-ingest.sh <D-NN-NN> <local-path> [--class CLASS]` validates D-NN-NN ID, ACL class, QNAP mount, source file, then idempotent-moves into the tree, emits metadata stub, and triggers registry refresh; sibling registry axis at `~/.platform-registry/artifacts.json` + `~/.platform-registry/artifacts/<deliverable>.json` built by `scripts/platform-registry/lib/artifact_writer.py`, refreshed by `scripts/platform-registry/refresh-artifacts.sh` (chained from launchd-driven `refresh.sh` so both axes stay current). 4 ACL classes — `property` (700/600), `schematics` (750/640), `vendor-docs` (755/644), `source-files` (750/640); chmod is try-and-warn for smbfs (QNAP-side ACL governs). Backup posture: deliberate non-coverage in Restic — Restic targets MinIO **on QNAP** (`s3://192.168.10.201:9000/backups`), so adding artifact paths would be circular; QNAP RAID + native snapshots are the durability layer (off-host replication = future deliverable). Substrate-defining-deliverable exemption: D-17-37 itself does not retrofit through its own substrate; first validation = synthetic D-17-37 self-test via `scripts/artifact-ingest.sh D-17-37 /tmp/d-17-37-substrate-smoke.txt --class source-files` returned correct `qnap://...` pointer + indexed by registry. smbfs cleanup quirk noted (`.smbdelete*` placeholders emitted on rm; emitter filters dotfiles). **Doctrine + chronicle:** `docs/architecture-facts/integration-audit-doctrine.md` Finding 5 (full What/Why/Substrate/Backup/Exemption sections); CLAUDE.md "Artifact Substrate Doctrine (D-17-37)" block added (consultation rule + ingest mandate + ACL classes + backup posture). Closes Gap F9 in `docs/_audit/integrated-stack-gaps-2026-05-03.md` (severity B → CLOSED). **D-17-35 retrofit reduced to single operator command** once PDF lands on filesystem: `scripts/artifact-ingest.sh D-17-35 ~/Documents/property/ono-island/source/Cox_V3_-_CD_05__Permit_Set__All__signed___25-03-10__House.pdf --class property`. Backlog (deferred, not blocking): rename QNAP path to dedicated `/share/roadmap-artifacts/` share once Finding Y resolves. Phase 17 progresses 26/31 → 27/31 (D-17-37 only; D-17-35 stays IN PROGRESS pending operator PDF drop). |
| D-17-38: Arr-stack health check audit — F5 silence-mechanism breakthrough via Vault credential drift remediation + selfheal severity escalation + QNAP TLS workaround | DONE | 2026-05-03 — three-layer compounded failure diagnosed and remediated: (1) **Vault credential drift** — arr-stack records held stale URLs + stale API keys (services had been re-keyed since last Vault write); harvested live keys from running `sonarr/radarr/prowlarr` `config.xml` via `docker exec`, deferred-rotation policy applied (no service-side regeneration per operator standing decision), wrote to Vault using on-host root-token resolver `scripts/lib/vault-admin-token.sh` (zero operator credential action — fully autonomous via existing service identity on macmini); read-back hash fingerprints match harvest exactly (cde8de07c824 / cfd54d7fba5f / a3051e37707a). (2) **Selfheal severity downgrade silencing 401s** (Gap F5 silence mechanism empirically located): `framework/health_checker.py` was downgrading auth failures to warnings — added `_credential_issues()` classmethod + `_classify_http_exc()` with explicit 401/403 → critical mapping so credential drift can no longer hide as warnings. (3) **QNAP container-side TLS handshake failure**: `requests.get(https://192.168.10.201, verify=False)` from inside Debian-13 containers returns `tlsv1 alert internal error` (TLS alert 80) regardless of TLS version / SNI / cipher hint, while host macOS LibreSSL negotiates cleanly (root-cause Debian 13 OpenSSL 3.5.5 vs QNAP QTS TLS config — surfaced as **D-17-40 candidate** in `docs/PHASE_ROADMAP.md` §18.C); `connectors/qnap.py` workaround = HTTPS first with `verify=False` + urllib3 warning silence, TCP-connect fallback to `(host, 443)` via `socket.create_connection` proves "alive on network" without TLS handshake or auth (SSH fallback rejected — QNAP publickey-only, no key provisioned); `credentials.env.tmpl` flipped `QNAP_URL` `http://` → `https://`. **Vault Agent sidecar**: new `vault-agent-dashboard` container (`hashicorp/vault:2.0.0`, runs once with `agent -config`, exits clean) renders `arr/sonarr,radarr,prowlarr` + `qnap/admin` to `/Users/admin/.vault-agent-secrets/dashboard/credentials.env`; `ai-platform-dashboard` consumes via shell-sourced entrypoint `sh -c "set -a && . /vault/secrets/credentials.env && set +a && exec ..."` and `service_completed_successfully` dependency; new `config/vault-policies/dashboard-policy.hcl` (read-only on `secret/data/arr/*` + `secret/data/qnap/admin`); `docker/vault-agent-dashboard/agent.hcl` AppRole config wired against on-host `/Users/admin/.vault-approle/dashboard`. **Final cycle counts**: services 4/5 up (`sonarr/radarr/prowlarr/qnap` true, `seedbox` false — separate burned-credentials backlog); total 13, critical 2 (both real upstream — radarr/prowlarr "all indexers unavailable"), warnings 11 — F5 silence mechanism empirically broken-through (was reporting "0 fixes" indefinitely on healthy-container false-negatives). **Sev-3 incident under deferred-rotation**: AI twice ran `tr "\0" "\n" < /proc/1/environ | grep ^QNAP_` without redactor pipe during diagnosis, exposing `QNAP_PASS` value to conversation transcript; operator decision Q2(ii) — defer rotation, joins existing burned-credentials/stability-baseline list; new sub-doctrine added to CLAUDE.md "Integration Health-Check Doctrine (D-17-38)" requiring `\| sed 's/=.*/=<set>/'` (presence-only) or `\| grep -c ^VAR=` (count) on credential-bearing /proc/1/environ reads. **Doctrine + chronicle:** CLAUDE.md "Integration Health-Check Doctrine (D-17-38)" block added (6 bullets: container-healthy ≠ integration-healthy / credential-source authority is running service not Vault / URL values are part of credential not metadata / reachability vs storage-stats are different probes / hash-only verification with redactor / chronicle pointer); `docs/architecture-facts/integration-audit-doctrine.md` Finding 8 appended (~73 lines, layer taxonomy table L1 network / L2 transport / L3 application / L4 semantic + 3 simultaneous root causes + ordered remediation pattern + status). Phase 17 progresses 29/31 → 30/31 (D-17-38 only; D-17-12, D-17-16, D-17-21 remain NOT STARTED, D-17-35 remains IN PROGRESS pending real PDF). |
| D-17-39: Roadmap ingestion flow — artifact-aware deliverable creation (operator-facing surface that turns roadmap intake into a single self-contained transaction: title + status + optional artifact → framework row + OpenProject WP + canonical-storage placement + qnap:// pointer back, with operator never touching filesystem paths or running `scripts/artifact-ingest.sh` directly; closes Gap F9 at the **flow** layer that D-17-37 closed at the **storage** layer) | DONE | 2026-05-03 — `scripts/roadmap-create.sh` ships as the operator-facing surface, composing D-17-37 substrate (`artifact-ingest.sh`) + framework row insertion + OpenProject WP creation in one self-contained transaction. Validation: 5 input-validation paths exercised (ID format, status word, ACL class, missing artifact, pipe-in-title, duplicate row) all reject correctly; full-flow dry-run confirmed correct row composition + qnap:// embedding + OP sync invocation; D-17-35 retrofit via Path 1 (synthetic placeholder) exercised substrate write + registry index + qnap:// pointer + framework row + OP sync dry-run end-to-end. **Surface decision (WP-02):** option (a) CLI wrapper selected on cost/risk/doctrine grounds. Option (b) OpenProject attachment hook explicitly rejected on doctrine inversion grounds (would invert D-16-02.A "repo-owned docs are canonical"). Option (c) MCP tool deferred to future deliverable once chat-attachment-pickup primitive proves reliable. **Substrate-defining vs consumer retrofit asymmetry (Path 1 worked example, WP-04):** D-17-35 stays IN PROGRESS — closing it on a placeholder file would have been false-positive completion (Gap F7 territory); placeholder removed from canonical store post-validation. Close-out path for D-17-35 once real PDF lands: single command via `roadmap-create.sh --update-existing` (~30 min implementation when needed). **Doctrine + chronicle:** CLAUDE.md "Roadmap Ingestion Flow Doctrine (D-17-39)" block added (canonical entrypoint + four-question artifact checklist + asymmetry doctrine + backlog); `docs/architecture-facts/integration-audit-doctrine.md` Finding 5 extended with flow-layer-closure section. Closes Gap F9 in `docs/_audit/integrated-stack-gaps-2026-05-03.md` at the flow layer (D-17-37 closed it at the storage layer). Phase 17 progresses 27/31 → 28/31 (D-17-39 only; D-17-35 stays IN PROGRESS pending real PDF). |
| D-17-36: Sportarr unpark + F1 coverage + Sonarr F1 cleanup | DONE | 2026-05-03 — Sportarr unparked end-to-end. **WP-01 → WP-02:** framework intake + retirement-record gate answers (3 gates answered with empirical evidence; reversal record appended to `docs/_retired/sportarr-2026-05-01.md`). **WP-03:** indexer URL fix + container up (5 → 8 indexers post-fix; 1390 releases fetched from 8 RSS feeds vs 700 from 5 retirement-era; bind-mount canonical alignment to `/Users/admin/mnt/qnap-downloads:/downloads` plural + `/data` per Sonarr/Radarr sibling pattern). **WP-04:** indexer ApiKey sweep (live Prowlarr key 620626ef... applied across all 8 rows; channel mapping confirmed phantom — DVR Auto-Scheduler "No Channel" log line is live-record path, not import blocker). **WP-06:** Plex sports library γ workflow (DELETE library 3 + recreate as library 4 at `/share/CACHEDEV2_DATA/data/media/sports`); γ'.3 reconfiguration to align Sportarr storage with canonical `/data/media/sports/{Sport}/Season {Year}/` layout (RootFolder add `/data/media/sports`, RootFolder remove `/data`, container-mediated `mv` of both Miami 2026 files — Sportarr filesystem watcher auto-updated `Events.FilePath` + `EventFiles.FilePath`). **WP-07:** Miami Qualifying mis-import remediated — release-parser had linked the .mkv to Event 1572 = "Australian Grand Prix Qualifying" at 100% confidence despite filename containing `Miami` (F12 worked example); manual `UPDATE EventFiles SET EventId = 1597 WHERE Id = 1` + Events.HasFile/FilePath corrections on 1572 (cleared) and 1597 (set) remediated. **WP-08:** doctrine — `docs/architecture-facts/integration-audit-doctrine.md` Finding 6 (F10: retirement-records-as-restoration-playbook is structurally unsound; four-phase worked example covering URL column name, ApiKey staleness, bind-mount canonical pattern, storage-layout projection; sub-doctrine on container-mediated `mv` as canonical for in-arr-stack file relocation) + Finding 7 (F12: release-parser confidence is independent from event-correctness; 100% match score can still misclassify; sub-doctrine on filename-vs-event-title token mismatch probe as Phase 18 candidate). Audit gaps F10/F11/F12 added to `docs/_audit/integrated-stack-gaps-2026-05-03.md` (gap inventory 19 → 22). Retirement record patched in-place with column-name correction + ApiKey-refresh sub-step + execution record appendix. **Final post-unpark state:** Sportarr `(healthy)`; Plex Sports library 4 size=2 (Miami Sprint Race + Miami Qualifying both at canonical paths, both playable). Pre-fix DB snapshots preserved at `/Users/admin/sportarr-db-pre-{pathfix,apikey-fix,step4,wp07-relink}-2026-05-03.snapshot`. **Backlog (Phase 18 18.D added 2026-05-03):** sports-tracker expansion + release-parser tuning + filename-vs-event-title mismatch probe + FlareSolverr verification (4h research + 2h implementation hard cap). **WP-05 (Sonarr F1 cleanup) DONE 2026-05-03** — series id=185 deleted from Sonarr (`DELETE /api/v3/series/185?deleteFiles=true`); 5 episode files (12.18 GiB, Australia + China s2026) unlinked; Plex TV library ratingKey=35192 dropped on rescan (404 confirmed). Disposition: DELETE (operator-approved); rationale: zero watch state (viewedLeafCount=0 on all 5 episodes), zero overlap with Sportarr canonical path (Miami DARKSPORT releases, disjoint). Sportarr canonical path and Plex Sports library unaffected. SMB `.smbdelete*` artifacts under Season 2026/ dir remain — QNAP-side background cleanup, not platform-managed. Inventory: `docs/phase-17/d-17-36/wp-05/INVENTORY.md`. **Phase 17 close framing:** D-17-36 DONE advances Phase 17 28/31 → 29/31; WP-05 was post-close cleanup (no counter change). |
| D-17-35: Property plans ingestion — Ono Island (durable repo location + registry-discoverable + indexed for xindex consultation; prerequisite for D-17-33 Overwatch camera/sensor placement analysis and any future property-related deliverables) | IN PROGRESS | added 2026-05-03 — operator-provided plans (SURV-1, SURV-2, PP cover sheet, S-1 structural, permit set) currently live only in prior chat attachments; need durable AI-consultable home that survives session compaction. **D-17-39 WP-04 (2026-05-03):** ingestion-flow surface (`scripts/roadmap-create.sh`) validated end-to-end against this row using a placeholder file (substrate write + registry index + qnap:// pointer + framework row + OP sync dry-run all confirmed); placeholder removed from canonical store post-validation; awaiting real PDF for actual deliverable close. Close-out path once PDF lands: `scripts/roadmap-create.sh D-17-35 ... --update-existing --artifact <path>` (flag is the D-17-39 WP-05 backlog item). |
| D-17-43: CMDB reconciliation intake — three-substrate drift audit (NetBox / service-registry.yaml / inventory.json); audit-only, full deliverable scope authored at WP-05 gated on operator authority decision at WP-04; promoted from §18.K | IN PROGRESS | added 2026-05-03; intake/audit phase only — outputs at `docs/_audit/cmdb-substrate-inventory-2026-05-03.md` + `docs/_audit/cmdb-drift-2026-05-03.md`; full deliverable scope at `docs/phase-18/d-17-43/SCOPE_2026-05-03.md` (gated on WP-04 authority decision); cross-refs Finding 4 (CMDB authority unenforced), ADR-A-014 (NetBox declared authority), D-17-29 (runtime registry), §18.K scope source |
| D-17-44: Buildarr config-as-code substrate (Radarr + Prowlarr only) — first F11 worked example; Sonarr v4 + Sportarr documented out-of-scope until upstream plugin coverage | DONE | 2026-05-03 — Buildarr 0.7.1 deployed. `config/arr-stack/buildarr/buildarr.yml` (839 lines, dump-config-generated) captures full Radarr config + Prowlarr applications. Credential injection via ${VAR} placeholders + Python substitution from Vault-rendered credentials.env. Vault AppRole `buildarr` provisioned (reads secret/arr/{radarr,prowlarr,sonarr,sportarr}); `secret/arr/sportarr` created (D-17-38-style harvest from running container). Sidecar: `docker/vault-agent-buildarr/` (agent.hcl + credentials.env.tmpl). Compose: `docker/docker-compose-buildarr.yml`. Run wrapper: `scripts/buildarr-run.sh`. Launchd: `docker/launchd-agents/com.iap.buildarr-sync.plist` (daily 03:00). WP-05 live run confirmed: both instances `up to date` + `clean` (zero mutations — YAML extracted from live state is idempotent on first run). WP-04 test-config: PASSED 5/5. **Known limitations documented**: (1) Sonarr v4 blocked upstream (buildarr-sonarr v3-only), (2) Sportarr no plugin, (3) Prowlarr indexer definitions + download clients not in plugin schema. **F11 graduated from candidate to Finding 11** — chronicle at `docs/architecture-facts/integration-audit-doctrine.md` Finding 11. CLAUDE.md "Buildarr Config-as-Code Doctrine (D-17-44)" added. **Sev-3 incident**: two Radarr + Prowlarr API key values exposed to conversation transcript during `grep` output scan. Added to existing §18.L burned-credentials deferred-rotation queue (same disposition as D-17-38 Sev-3). |
| D-17-45: CMDB reconciliation — substrate audit + canonical authority decision (intake phase) | IN PROGRESS | added 2026-05-03 via roadmap-create.sh |
| D-17-46: arr-stack metrics observability (Scraparr/Exportarr) | DONE | 2026-05-03 — Scraparr selected at WP-02 gate (Exportarr in maintenance mode; Scraparr active + single-instance multi-service fit). Vault pattern mirrored from D-17-38/D-17-44: new policy `config/vault-policies/scraparr-policy.hcl`, sidecar templates under `docker/vault-agent-scraparr/`, provisioning script `scripts/provision-scraparr.sh` harvests live Sonarr/Radarr/Prowlarr API keys from running containers and verifies Vault parity via sha256[:12] only (`cde8de07c824` / `cfd54d7fba5f` / `a3051e37707a`). Deployment in `docker/docker-compose-arr-metrics.yml` (sidecar + Scraparr on `control-center-net` + `observability` networks). vmagent scrape job added to `docker/vmagent-config/scrape.yml`; final target status `up` at `http://host.docker.internal:7100/metrics`; VictoriaMetrics query returns `sonarr_last_scrape`/`radarr_last_scrape`/`prowlarr_last_scrape` series under `job=\"scraparr\"`. WP-05 minimal dashboard path operator-approved: provisioned `docker/grafana-provisioning/dashboards/arr-stack-overview-p18.json` (scrape age, scrape duration, exporter RSS). Community dashboard adaptation deferred to §18.G component-1 follow-on backlog due to non-trivial datasource templating mismatch (`DS_MIMIR`/`${datasource}`). WP-06 doctrine landed: `integration-audit-doctrine.md` Finding 12 + CLAUDE.md arr-stack metrics doctrine block; selfheal explicitly retained as sibling remediation layer, not replaced. |
| D-17-47: Bazarr subtitle automation deployment (arr-stack component 18.G.5) | DONE | 2026-05-03 — Bazarr deployed into canonical arr-stack compose at `/Users/admin/control-center-stack/stacks/arr-stack/docker-compose.yml` with sibling-pattern mounts (`/Users/admin/mnt/qnap-downloads:/downloads`, `/Users/admin/mnt/qnap-downloads/data:/data`), network `control-center-net`, and health check on `:6767`. Caddy route added: `bazarr.internal` → `host.docker.internal:6767`; operator-side DNS host-override runbook authored at `docs/runbooks/opnsense-add-host-overrides.md` (Unbound authority). Integration gate WP-04 applied via Vault Agent sidecar pattern (D-17-38/D-17-44 shape): policy `config/vault-policies/bazarr-policy.hcl`, sidecar templates `docker/vault-agent-bazarr/`, provisioner `scripts/provision-bazarr.sh`, AppRole `bazarr` rendering `/Users/admin/.vault-agent-secrets/bazarr/credentials.env`; hash-only verification fingerprints aligned Sonarr/Radarr API keys in Vault-rendered env and Bazarr runtime config (`cde8de07c824` / `cfd54d7fba5f`). Bazarr configured against canonical container DNS URLs (`http://sonarr:8989`, `http://radarr:7878`). WP-05 operator gate respected: account/API-key providers skipped; no-credential baseline providers enabled (`embeddedsubtitles`, `napiprojekt`, `podnapisi`, `subf2m`, `animetosho`); credential-bearing providers deferred into §18.L coordinated rotation companion queue. WP-06 test cycle: authenticated API call to `PATCH /api/episodes/subtitles` returned `204` for existing Sonarr episode (`seriesid=48`, `episodeid=2669`) confirming end-to-end Bazarr action path; selected sample episode already reported `missing_subtitles=[]`, so no new external subtitle artifact was created in that run. Known limitation: Bazarr->Plex refresh trigger/provider not configured in baseline; tracked as §18.G component-5 follow-on hardening with the provider-credential enrollment window. WP-07 coverage check: no `buildarr-bazarr` distribution/plugin available (verified via `pip index versions buildarr-bazarr` → no match), documented as F11-style partial-coverage continuation. |
| D-17-49: Cleanuparr deployment (Seeker-consolidated) — F10 family structural closure | IN PROGRESS | 2026-05-03 WP-07 state: **DEPLOYED (observable-but-inert), not closure-DONE**. Scope revised during execution after Huntarr image pull failure (`huntarr/huntarr` unreachable from runtime host): single-tool Cleanuparr deployment covers both roles via Queue/Download cleanup modules + Seeker missing/upgrade hunts. This mirrors D-17-46 Scraparr sibling posture pattern (signal plane/live service present; remediation path intentionally gated). Huntarr scaffolding preserved under `docker/_deferred/huntarr-upstream-unreachable-2026-05-03/` for future re-evaluation. Vault Agent sidecar pattern retained (D-17-38/D-17-44 shape, one-shot render-then-exit-0 — `vault-agent-cleanuparr` Exited(0) is the expected `service_completed_successfully` dependency-gate pattern, not a failure), with dry-run + rate-limit gates before destructive/high-volume operations. **2026-05-04 second hygiene pass — gate predicate corrected twice over (D-17-76 audit):** the prior narrative said Seeker enablement was gated on download-client credentials; that's wrong. Cleanuparr's *Seeker* module hunts for missing media via Sonarr/Radarr APIs (which it already has via existing `secret/arr/sonarr` + `secret/arr/radarr` rendered into the cleanuparr sidecar) and **does not talk to download clients directly**. Only Cleanuparr's *Queue Cleaner* + *Download Cleaner* modules need download-client API access. So: **Seeker can be enabled now** (operator UI flip from `search_enabled=0` to enabled, with conservative caps already staged per `docs/phase-18/d-17-49/SMOKE.md`); **Cleaner modules** remain gated on `secret/seedbox/qbittorrent` population (the actual integration target for the seedbox-resident qBittorrent WebUI — separate path from the existing `secret/seedbox/sftp` which is for rclone/rsync file transfer; P2 protocol-separation doctrine per D-17-76). §18.L companion deliverable **D-17-76** in flight (substrate-creation half landed at `c04c760`: `seedbox-policy.hcl` + `provision-seedbox-credentials.sh` + `vault-mapping.yaml` drift fix `secret/seedbox/account` → `secret/seedbox/sftp`); cleanuparr-side consumption (policy extension + sidecar template + provision-cleanuparr conditional readback test) staged to land in a sibling commit after operator runs the provision script (M3 ordering — avoids foot-gun where cleanuparr sidecar would refuse to render until the path exists). Closure-DONE blockers (revised): (1) operator authorizes Seeker first-pass enablement; (2) `secret/seedbox/qbittorrent` populated via `scripts/provision-seedbox-credentials.sh` (D-17-76); (3) D-17-76 commit-2 landed (cleanuparr policy/template edits); (4) Cleanuparr first-run UI setup wizard completed (currently `/api/v1/health` returns `{"error":"Setup required"}`); (5) operator authorizes Cleaner modules. Cleanuparr container remains UP (healthy) on `:11011`; Caddy front `cleanuparr.internal` returns 200; no remediation actions taken to date. |
| D-17-50: Prowlarr↔consumer apiKey freshness sweep + auto-resync | DONE | 2026-05-03 — WP-1 audit + WP-2 structural remediation completed with doctrine pivot to per-implementation two-key model. Sonarr-first and Radarr follow-up executed via Prowlarr-side `Application` DELETE+recreate + forced `ApplicationIndexerSync` (Radarr app id `3→5`, Sonarr app id `2→4` during recreate path). Functional verification: Sonarr `GET /api/v3/release?query=Inception` `HTTP 200` with 700 results; Radarr `GET /api/v3/release?query=test` moved from `HTTP 200 results=0` + indexer-unavailable health errors to `HTTP 200 results=291` with indexer health errors cleared. Hash audit confirmed mixed valid key paths post-fix: Sonarr/Radarr proxied rows `07ab59f4731b`, Sportarr proxied rows and Prowlarr master `a3051e37707a`; therefore single-master hash comparison was retracted as a universal drift rule. WP-3 automation landed: `scripts/arr-apikey-sweep.sh` + `docker/launchd-agents/com.iap.arr-apikey-sweep.plist` (hourly, functional-probe trigger; `HTTP 401` -> Prowlarr-side recreate -> sync -> re-probe; hash output retained as observability only). WP-4 chronicle/doctrine extension landed in `docs/architecture-facts/integration-audit-doctrine.md` Finding 6 sub-finding revision + worked example #6; D-17-38-era \"proxy-validation drift to master key\" statement annotated as wrong frame for Sonarr/Radarr-class apps. |
| D-17-51: Finding Y resolution — launchctl user-domain bootstrap blocker | DONE | 2026-05-04 — Operator-run LaunchDaemon migration executed; 11/12 effective OK (15 WRITE, 1 SKIP gui-dependent `com.iap.d-17-27-reminder`, 3 reclassified `DUPLICATE-PUBLISHER` and queued for retirement). All 6 critical unattended agents loaded (`buildarr-sync`, `arr-apikey-sweep`, `platform-registry`, `docker-events`, `strava-refresh`, `backup`). MCP outliers (`com.iap.mcp.{docker,docs,filesystem}`) diagnosed as stale pre-containerization plists: target ports 8091/8092/8093 already owned by healthy Docker containers `mcp-{filesystem,docker,docs}-remote` since 2026-05-03 02:54; daemon supergateway processes started cleanly per logs then SIGTERM'd in throttle loop because the canonical publisher is the container substrate, not launchd. Disposition: retire from launchd. Operator-run privileged retirement sequence queued (`bootout` × 3 + `rm /Library/LaunchDaemons/com.iap.mcp.*.plist`). Closeout chronicle: `docs/phase-18/d-17-51/CLOSEOUT_2026-05-04.md`. Doctrine produced: Finding 15 sub-finding 15.A (publisher-uniqueness check) added to `docs/architecture-facts/integration-audit-doctrine.md` — launchd analogue of D-17-29 service-registry consultation; specifies port-uniqueness probe + container-publisher probe + service-registry consult as pre-flight gates before authoring system-domain LaunchDaemons, plus a four-state classification (`OK` / `FAIL` / `DUPLICATE-PUBLISHER` / `SKIP`) for migration verifiers. |
| D-17-52: Remote-work readiness verification — 10-day Singapore travel window | IN PROGRESS | added 2026-05-03 via WP-01 intake for Phase 18 remote-work readiness; scope: Headscale tailnet access audit, `.internal` remote DNS strategy, MacBook operator runbooks, failure-mode recovery path, and pre-departure verification checklist with explicit Finding Y dependency. |
| D-17-53: Local AI execution-surface migration framework — operator-supervised progressive adoption | DONE | 2026-05-03 — Phase 18 §18.O meta-architectural foundation landed. Five chronicles authored under `docs/architecture-facts/`: `execution-surface-roles.md` (CONTROL / EXECUTION / AUTONOMOUS roles with 5 hard rails — CONTROL never migrates, EXECUTION migrates per (surface × class), AUTONOMOUS does not call LLMs, trust-authority CONTROL-side with EXECUTION-drafts-CONTROL-approves split for trust-bearing artifacts, force-multiplier-not-replacement); `promotion-criteria.md` (cell as migration unit, 4 postures Posture-0/1/2/3, N=5 gate criteria, M=10 dual-review window, automatic + operator-discretion demotion triggers, first measured cell empirical evidence); `class-taxonomy.md` (10 initial classes C1–C10 with Phase-A/B/C/Never tier assignments — C1/C2 Phase-A, C3/C4/C10 Phase-B, C5/C6 Phase-C, C7/C8/C9 Never per CONTROL-role rail; Vault/credential/SSH-cross-host explicitly excluded as capability-surface boundaries not work-classes); `goose-session-pipeline.md` (5-stage pipeline Brief→Prompt→Invoke→Review→Chronicle with role attribution, anti-pattern catalog, D-17-13 WP-06 retroactive worked-example mapping); `migration-telemetry.md` (per-session/per-cell-rolling/per-gate metric schema, 4-leg §18.O thesis falsification test, evidence path conventions). Surface backs at WP-02 (role-boundary Q3 → drafts-vs-approval split with ADR drafting reclassified as Phase-B candidate) + WP-04 (10-class taxonomy with C2 Phase-A, C10 Phase-B on consequence-surface, C6 Phase-C on reasoning-shape-not-output-shape) settled per operator. Pure repo authoring; no infrastructure mutation; no class promotion to local-primary in this deliverable — first cell (Goose+qwen3-coder:30b × C1) remains Posture 1 sessions 2/5. Builds on D-17-12 (T3-B benchmark basis) + D-17-13 (Goose substrate + first measured cell). All five chronicles cross-link as siblings; CLAUDE.md "Execution surfaces" subsection (landed at D-17-13 WP-08) references the role boundary. **2026-05-04 update — first measured cell DEMOTED Posture 2 → Posture 1.** Cell (Goose+qwen3-coder:30b × C1) cleared the N=5 gate 2026-05-03 and entered Posture 2 dual-review; after 6/10 entries, Session 11 (re-author of `launchd-jobs-canonical.md`) exhibited original severe-shape source-fidelity-loss recurrence under the strengthened standard preamble (verbatim-block + source-citation table + line-number verification). Hit-rate of severe-shape failure under strengthened preamble: **2 of 3 post-remediation sessions** (Session 9 clean, Session 10 shape-shifted, Session 11 severe). Operator demoted on Option D + E: cell back to Posture 1 (T1-A); Session 11 draft NOT committed (existing frontier-corrected runbook at 2a84076 remains canonical); watchlist correct-pattern #5 status REGRESSED to "PROMPT-ENGINEERING REMEDIATION INSUFFICIENT"; **N=5 gate re-required if future re-promotion attempted**. Standard preamble retained for Posture-1 work — does not hurt; just doesn't reliably suppress the failure-mode class. Two new findings logged: substrate-shape-correlation hypothesis (clean line-aligned blocks like argparse → clean output Session 9; structured-document XML plists / multi-script orchestration → severe-shape recurrence Session 11) and operator-side substrate trap sub-doctrine (pre-flight check existing-file conflicts before Goose dispatch). Session evidence preserved at `docs/phase-17/d-17-53/session{10,11}-evidence/`. Chronicle updates landed in `promotion-criteria.md` and `goose-capability-boundary.md`. **2026-05-04 update — first re-promotion attempt session 1/5 was a NULL attempt (severe-shape recurrence; does not count toward N=5).** Session 12 (re-author of existing `docs/runbooks/openproject-sync-and-enrich.md`) produced wholesale fabricated source-citation table line numbers across two Python scripts (sync flags cited 109-120 actual 771-781; enrich flags cited 158-163 actual 304-306). Verbatim quotes matched real content but line-number citations were fabricated end-to-end — the strengthened constraint B is **gameable by the model authoring the table**. Hit-rate of severe-shape failure under strengthened preamble now **3 of 4 post-remediation sessions** (Session 9 clean, Session 10 shape-shifted, Sessions 11 + 12 severe). Operator disposition Option A: reject Session 12; re-promotion counter stays 0/5; existing Session 9 frontier-corrected runbook remains canonical. Two follow-on chronicle changes: (a) **substrate-shape-correlation hypothesis FALSIFIED at N=2** — Session 9 (Python+argparse) clean / Session 12 (Python+argparse) fabricated; same substrate shape produced opposite outcomes; alternative correlation candidates logged (multi-script-CLI-flag-table sub-shape; target-already-exists shape; single-clean-datapoint sampling artifact); (b) **operator-side substrate trap promoted from chronicle sub-doctrine to HARD PRE-FLIGHT GATE** — brief-compose-time check that target file does not already exist; if it does, reject brief at compose-time. **Class-intrinsic-failure threshold:** one more severe-shape recurrence (Session 13 or later) triggers Option B — demote to Posture 0; class redefinition required before any new N=5 gate attempt. Session evidence preserved at `docs/phase-17/d-17-53/session12-evidence/`. **2026-05-04 update — Option B triggered; cell DEMOTED Posture 1 → Posture 0; C1 SPLIT.** Session 13 (fresh authoring of `goose-dispatch-preflight.md`, single primary source `promotion-criteria.md`, narrative-shape — deliberately matched Session 9's clean substrate shape to test alternative correlation hypothesis (c)) produced severe-shape failure with a **NEW DEFECT SHAPE: Sources-section fabrication-by-omission**. Goose ran 12 seconds with **zero tool calls**; the Sources section asserted reading `promotion-criteria.md` but no read occurred in the trace. Sessions 5/7/8/11/12 read source files and then fabricated *citations from* them; Session 13 fabricated the *reading itself*. Additional defects: counterfactual converted to factual (Session 11 "overwriting dispatch led to a loss of operational context" — no overwrite occurred at Session 11; the *prevented* counterfactual is what the chronicle records); wholesale invention of a Session 12 "recovery procedure to restore the correct dispatch state" that never existed. Hit-rate of severe-shape failure under strengthened preamble now **4 of 5 post-remediation sessions** (Session 9 clean, Session 10 shape-shifted, Sessions 11/12/13 severe). **Single-clean-datapoint sampling-artifact hypothesis (alternative correlation c) STRENGTHENED** — Session 13 substrate matched Session 9's clean shape on every identifiable axis (net-new target, single primary source, narrative content, no flag tables, no plists, no API endpoints) and still produced severe-shape failure; Session 9 was likely a lucky draw. **Operator disposition Option B confirmed:** cell DEMOTED Posture 1 → Posture 0; C1 SUSPENDED for this cell pending class redefinition; **C1 split** into C1a (verbatim-quote-bearing reference docs — SUSPENDED for Goose+qwen3-coder:30b indefinitely; returns to Claude Code under `claude-local`) + C1b (narrative chronicle/doctrine notes without quote citations — available for future Goose attempts; Posture 0 not yet evaluated for this cell at C1b sub-class; Posture-1 N=5 gate would re-establish capability evidence under the narrowed sub-class). **Cell-change branch deferred** (testing gemma2:27b or larger qwen variants on C1a parked as future deliverable; Singapore travel imminent). **Goose dispatch RETIRED for C1a work indefinitely.** Re-promotion attempts paused indefinitely until class redefinition is validated. Class taxonomy chronicle updated with C1a/C1b split (`class-taxonomy.md` C1 section). Session evidence preserved at `docs/phase-17/d-17-53/session13-evidence/`. |
| D-17-54: OPNsense DHCP DNS-push runbook + OpenProject admin recovery runbook — Goose session 2 deliverable, frontier-corrected | IN PROGRESS | added 2026-05-03 — D-17-53 framework follow-on. Two new runbooks authored via §18.O pipeline (Brief→Prompt→Invoke→Review→Chronicle): `docs/runbooks/opnsense-dhcp-dns-push.md` (closes the DHCP-doesn't-push-internal-DNS gap that breaks `.internal` resolution on MacBook + new clients) and `docs/runbooks/openproject-admin-recovery.md` (recover OpenProject admin access when operator credentials are unavailable). Goose session 2 produced both drafts in the same invocation; counts as session 3/5 toward N=5 promotion gate for cell (Goose+qwen3-coder:30b × C1). Output split ~32% Goose / ~68% frontier-correction — substrate-limited factual gaps (OPNsense Kea UI path, OpenProject `rails runner` syntax) require operator verification on destructive surfaces before commit. WP-01 intake; WP-02 chronicle entry to `goose-capability-boundary.md` "Observed behavior" extended with session 3 metrics; WP-03 awaiting operator verification of (a) OPNsense Kea UI path Services → Kea DHCPv4 → [Subnet] → DHCP options → "domain-name-servers" (option 6) and (b) OpenProject `rails runner` password-reset command syntax; WP-04 frontier authors corrected runbooks + close. Hard cap 2h once verifications return. Session evidence preserved at `docs/phase-17/d-17-53/session2-evidence/`. |
| D-17-55: OpenProject WP metadata enrichment — descriptions, % complete, custom fields, idempotent sync extension | IN PROGRESS | added 2026-05-03 via WP-01 intake for Phase 18 OpenProject metadata enrichment |
| D-17-56: opnsense-add-host-overrides runbook substitution — Unbound to Dnsmasq | IN PROGRESS | added 2026-05-03 via WP-01 intake for runbook authority substitution |
| D-17-57: retire-service runbook authoring — canonical decommission pattern | IN PROGRESS | added 2026-05-03 via WP-01 intake for retire-service runbook |
| D-17-58: Mac Studio Ollama LaunchDaemon persistence — system-domain UserName=admin | IN PROGRESS | added 2026-05-03 via WP-01 intake for Mac Studio Ollama persistence |
| D-17-59: ssh non-interactive sudo class — Finding 16 candidate + remote-sudo script pattern | IN PROGRESS | added 2026-05-04 via WP-01 intake for Finding 16 candidate |
| D-17-60: Phase 18 status audit + cross-reference verification | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-61: CLAUDE.md cross-reference audit | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-62: Runbooks index + legacy-reference scan | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-63: scripts directory inventory + dependency map | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-64: architecture-facts inventory + legacy-reference scan | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-65: Finding 1-16 cross-reference matrix | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-66: _audit and _archive inventory + index docs | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-67: D-17-63 follow-on: failed-branch annotation + service-registry normalization | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-68: provision-openproject.sh orphan disposition | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-69: xindex.md legacy DNS wording cleanup | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-70: Plane-era scripts retention decision | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-71: Stale-candidate runbook triage — disposition + minimal drift fixes | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-72: Orphan script disposition — cleanup_docker + troubleshoot + launchd installer | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-73: Runbooks second pass + runbooks README authoring | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-74: install-launchd.sh disposition decision | DONE | keep-annotated disposition accepted 2026-05-04; no move to scripts/_retired in this pass |
| D-17-75: D-17-44 Buildarr closeout audit | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-76: secret/downloads/seedbox bootstrap — §18.L companion to D-17-49 | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |
| D-17-77: Buildarr coverage audit — Sonarr v4 + Sportarr exclusion verification + reactive-management runbook | IN PROGRESS | added 2026-05-04 via roadmap-create.sh |

ID-reservation note: D-17-22 (multi-session role + intake architecture)
is RESERVED but not yet framework-authored. Discussed in a prior
session; lives as a parking-lot item pending its own intake doc +
framework-add commit. Reserving the ID preserves the parking-lot
reference without forcing premature scope authoring. Sized similar
to D-17-23 (~2-3h doctrine-shaped) when it lands.

ID-reservation note: D-17-40 / D-17-41 / D-17-42 are RESERVED as
deferred-candidate IDs. Each is logged as a §18.C scope bullet in
`docs/PHASE_ROADMAP.md` with its prerequisite/trigger captured;
none has a §9 framework row yet by design — they activate only when
the trigger fires (operator decision or surfaced incident).
- D-17-40 (logged 2026-05-03 from D-17-38 close): Container-side TLS
  handshake failure to QNAP appliance — root-cause + workaround.
- D-17-41 (logged 2026-05-03 by operator intake): HACS evaluation +
  supply-chain doctrine for HA plugins. Defer until concrete plugin
  need surfaces.
- D-17-42 (logged 2026-05-03 by operator intake): Tautulli playback
  analytics + alerting deployment. Defer until Plex usage analytics
  matter to operator workflow.

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
DNS authority resolution). D-17-14 before D-17-25 (test follows the
partial-close it interrogates).

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
