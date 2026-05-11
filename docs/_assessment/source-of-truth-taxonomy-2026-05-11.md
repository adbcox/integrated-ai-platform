# Source-of-Truth Taxonomy — markdown vs OpenProject vs NetBox

**Author:** Claude Code (Opus 4.7, 1M context)
**Date:** 2026-05-11
**Repo state:** main HEAD `27891bf4` (post-WP-4 ADR-A-020 ACCEPTED merge); branch `feat/source-of-truth-assessment` cut from this commit
**Frame:** Assessment, not implementation. No tool migrations executed; no markdown source-of-truth edits beyond authoring this doc.

**Anchors:**
- ADR-A-014 (NetBox as Authoritative CMDB; Accepted 2026-04-30)
- ADR-A-018 (Replace Plane CE with OpenProject CE as PM substrate; Accepted 2026-05-02; explicitly preserves D-16-02.A "repo-owned docs are canonical")
- ADR-A-020 (Track 2 Agent Role Codification; Accepted 2026-05-11)
- This session: Briefs A–D plan + Thread A WP-1 through WP-5 (10+ commits demonstrating the sync burden in practice)

---

## §1 Context

This session demonstrated a recurring **manual sync burden** that is structural, not procedural. Two concrete signals:

- **Four false-negative classifications** in the orchestration-rebuild audit (OpenCode, Continue, OpenHands, Cline — each corrected across Thread A WP-1/2/3) all traced back to probe-methodology defects compounded by *which source you read first* (Track 2 status doc + capability audit + filesystem evidence + `which`). The single-source assumption was wrong; the multi-source manual reconciliation surfaced the defect retroactively.
- **~6 distinct sync points** were required to propagate a single ADR-A-020 acceptance: the ADR file itself, `docs/adr/README.md` index, `docs/DECISION_REGISTER.md` sibling index, four doctrine docs (`work-routing-doctrine.md`, `capability-self-knowledge.md`, `goose-capability-boundary.md`, `integration-audit-doctrine.md`), three wrapper scripts, and five `§9` deliverable-table row annotations. Each of those is a separate edit operation that pre-commit hooks must reconcile (the ADR ↔ DECISION_REGISTER hook caught a missed sibling-index entry on the PROPOSED commit).

The pattern is structural because the platform's source-of-truth assignment is **per-document-type rather than per-data-type**. ADR-A-014 already flipped infrastructure inventory (NetBox); ADR-A-018 explicitly preserved the markdown-canonical doctrine for deliverables (D-16-02.A). The split is sound for some data classes and over-extended for others. This assessment reads the current state, classifies what fits where, and surfaces the migration paths that would reduce the sync burden without compromising the markdown-canonical narratives that genuinely belong in markdown.

---

## §2 Current-state inventory

Per-source state as of `main 27891bf4` (post-WP-4 ACCEPTED merge; Thread A WP-5 not yet merged).

| Source-of-truth | Path | Size | Edit freq (this session) | Downstream cross-refs | F7-class drift surface this session |
|---|---|---|---|---|---|
| `§9` deliverable table | `docs/PROJECT_FRAMEWORK.md` | 659 lines / **123 D-17-NN rows** | 4+ commits (Brief B/C + WP-5 prep) | OpenProject sync target; xindex `op_workpackages` mirror; audit docs cite row numbers; closeout doc § scorecard | D-17-54 false-positive completion (Brief C scope-correction); D-17-137 carry-forward row spawned |
| KI register | `docs/known-issues/*.md` (10 files) | ~100-200 lines each | 7 edits across Brief A/B/C (KI-001/002/005/009 frontmatter migration; KI-003/004/010/011/012 disposition) | ADR-A-020 §5 Q-5 reference; audit doc §3.5 criterion 5 KI table; framework §10 KI register block | None directly; but KI status drift between inline `**Status:**` body lines and YAML frontmatter was the Brief A migration trigger |
| ADR index | `docs/adr/README.md` | 54 lines | 2 edits (ADR-A-020 PROPOSED + ACCEPTED status flips) | ADR ↔ README pre-commit hook enforces parity; future ADRs must add row | Hook caught nothing this session — but only because operator landed both PROPOSED + ACCEPTED in same session |
| Decision register | `docs/DECISION_REGISTER.md` | 66 lines | 2 edits (ADR-A-020 PROPOSED + ACCEPTED) | ADR ↔ DECISION_REGISTER pre-commit hook; **caught a missed sibling-index entry on the ADR-A-020 PROPOSED first commit** | This session's primary sync-failure signal |
| ADR files | `docs/adr/ADR-A-*.md` (19 ADRs) | varies (60-300 lines each) | 1 new ADR + 2 edits to it (ADR-A-020 PROPOSED → ACCEPTED amendment) | Both index docs + DECISION_REGISTER; doctrine cross-references; §9 row annotations on Acceptance | ADR-A-019 reserved-but-unauthored slot (OrbStack) — example of a coordination drift class: foundation-install-status-track-2.md cites ADR-A-019 but the ADR doesn't exist yet |
| Audit docs | `docs/_audit/*.md` (16 files) | 100-635 lines each | `orchestration-layer-rebuild-audit-2026-05-11.md` edited **4+ times** (initial + WP-1/2/3 corrections); `phase-17-closeout-audit-2026-05-11.md` edited 2+ times (Brief B/C landings) | Cross-references to §9 rows + ADRs + doctrine; future audits cite this doc | Audit doc reclassifications 22/5/9/14 → 26/5/8/11 → 27/5/8/10 → 28/5/8/1/8 across WP-1/2/3 — each correction required editing the audit AND the doc the audit-row pointed at |
| Planning docs | `docs/_planning/phase-17-brief-d-plan-2026-05-11.md` | 267 lines | 2 edits (initial + WP-3 Cline carry-forward) | WP-D-07 row cites §9 rows + ADR-A-020 §5 Q-5 | None this session |
| Architecture-facts (doctrine) | `docs/architecture-facts/*.md` (38 files) | 100-1500 lines each | WP-5 prep touched 4 docs additively | ADR-A-020 §1 Sources Consulted cites 13 of these; cross-doc references abundant | Doctrine drift potential: ADR-A-020 §6 enumerates 5 doctrine docs needing cross-references; without ADR-acceptance trigger, drift surfaces later |
| Runbooks index | `docs/runbooks/README.md` | 126 lines | 1 edit (Brief C — 12 missing entries added) | Per-runbook page links; D-17-62 § row | Brief C surfaced 12-runbook index drift on a doc that was assumed canonical |
| Runbook files | `docs/runbooks/*.md` (62 files) | varies | 0 direct edits this session | Index links; CLAUDE.md occasional citation | Append-on-author rule was operator-confirmed (D-17-62 closeout) — but enforcement is procedural-only, not pre-commit-gated |
| CLAUDE.md | `CLAUDE.md` (repo root) | 376 lines | 1 edit (Brief A — HEAD SHA refresh) | "Current state" sections cite §9, NetBox, OpenProject, runtime stack | "Current state" prose drifts from real state between sessions; staleness probes are operator-manual |
| Service registry (DEPRECATED) | `config/service-registry.yaml.DEPRECATED` | (unchanged this session) | 0 | `scripts/cmdb_source.py` reads as fallback per ADR-A-014; canonical is NetBox | None this session; ADR-A-014 already retired this as write target |
| OpenProject runtime | `openproject.internal` (Docker) | n/a (DB) | unknown (sync runs operator-side; not directly editable from chat session off-LAN) | xindex `op_workpackages` mirror; PROJECT_FRAMEWORK.md is the WRITE source via sync script | D-17-31 sync flag drift (Phase 17 dedup edge case fixed via `--dedup-phase17`) |
| NetBox runtime | `netbox.internal` (Docker) | n/a (DB) | unknown (LAN-gated this session) | 13+ consumer scripts via `cmdb_source.py`; canonical for service/host/network inventory per ADR-A-014 | None this session (LAN-gated; off-LAN session can't read NetBox) |

**Manual sync points demonstrated this session (numerical count):**

| Operation | Files synced | Sync mechanism |
|---|---|---|
| ADR-A-020 PROPOSED commit | 3 files (ADR + 2 indexes) | Manual edit; ADR-A-020/README hook auto-validated; **DECISION_REGISTER hook caught missed update** |
| ADR-A-020 ACCEPTED amendment | 3 files (ADR + 2 indexes) | Manual edit; both hooks passed first attempt (lesson learned) |
| ADR-A-020 §6 propagation (Thread A WP-5, pending merge) | 8 files (4 doctrine + 3 wrappers + 1 framework annotation pass) | Manual edits; framework-table-sanity hook validated annotations are append-only |
| Orchestration-rebuild audit corrections (WP-1/2/3) | 4 audit edits + 1 planning doc edit | Manual edits; no automated parity check (audit-vs-§9 reclassification is operator-discretion) |
| Brief C §9 D-17-54 scope-correction | 3 files (§9 row + runbooks index + audit doc) | Manual edits; framework-table-sanity validated |
| Brief A KI frontmatter migrations | 4 KI files | Manual edits; no schema validation pre-commit (operator-checked) |

**Estimated manual sync burden:** ~25 file-edit-operations across this single off-LAN closeout session, spanning markdown reconciliation that would be near-zero if the underlying data lived in a query-able tool.

---

## §3 Tool-suitability taxonomy (4 buckets)

Per-data-type assignment to its right substrate. Bucket boundaries are evidence-based: ADRs already accepted (A-014, A-018) and doctrine doctrine-existing-on-main are the anchors.

### §3.a System-of-record fit (tool, not markdown)

These data classes have **structured-tool-shaped semantics** (records, queries, status transitions, relations). Markdown is a poor substrate for them because every state-change is a manual-sync event, and there's no query/aggregation path.

| Data class | Right tool | Current state | Migration status |
|---|---|---|---|
| **Service inventory** (name/host/port/protocol) | **NetBox** | NetBox canonical per ADR-A-014; YAML retained as fallback only | **DONE** — already migrated |
| **Physical node inventory** (devices, IPs, roles) | **NetBox** | NetBox canonical per ADR-A-014 | **DONE** |
| **Network topology** (vlans, prefixes, interfaces) | **NetBox** | NetBox canonical per ADR-A-014 | **DONE** |
| **Container roster** (running container list, image+tag, capability surface) | **NetBox** (planned) | Currently `docker ps` ad-hoc + audit-doc snapshots; ADR-A-014 implies but doesn't operationally enforce | **PARTIAL** — gated on Brief D LAN-session NetBox reconciliation |
| **Deliverable register** (D-17-NN rows: title, status, dependencies, work-package breakdown) | **OpenProject (work packages)** | OpenProject deployed; sync from PROJECT_FRAMEWORK.md is one-way (markdown canonical); xindex mirrors via `op_workpackages` | **PARTIAL** — direction inverted; markdown is authority, OpenProject is operational overlay |
| **Known issues** (KI-NNN register) | **OpenProject (work-package type "issue")** OR **GitHub Issues** | Currently 10 markdown files in `docs/known-issues/`; references scattered across §10 framework block + audit doc Criterion 5 table + ADR-A-020 §5 Q-5 reference | **NOT STARTED** — KI register is the next-easiest migration after §9 |
| **Phase rollups** (Phase-NN versions, completion status, criterion-by-criterion scorecard) | **OpenProject (versions)** | OpenProject versions provisioned per D-17-31; closeout-audit scorecards live in markdown | **PARTIAL** — versions exist but scorecard is markdown |
| **Change records** (CR-17-NNN entries) | **OpenProject (work-package type "change record")** | Currently 6 CR markdown files in `docs/change-records/`; ADR-A-018 explicitly cites change-record workflow as an OpenProject capability that Plane lacked | **NOT STARTED** — natural extension of §9 migration |

### §3.b Markdown-is-right (narrative documents)

These data classes have **prose-shaped semantics**: they describe reasoning, decisions, procedures, or temporal snapshots. Markdown's plain-text-grepable-durable nature is the actual asset, not a limitation.

| Data class | Examples | Why markdown fits |
|---|---|---|
| **ADRs** | `docs/adr/ADR-A-NNN-*.md` (19 files) | Decision narratives with Context/Decision/Alternatives/Consequences structure; immutable post-Acceptance; grep-able; tool-independent durable record |
| **Runbooks** | `docs/runbooks/*.md` (62 files) | Procedural prose; operator follows step-by-step; never-aggregated; per-domain narrative |
| **Doctrine docs** | `docs/architecture-facts/*.md` (38 files) | Narrative architecture; cross-references natural in markdown; long-form prose with embedded code blocks; not state-tracked |
| **Audit snapshots (point-in-time)** | `docs/_audit/*-2026-05-NN.md` (date-stamped) | Frozen-at-a-moment evidence records; immutable in spirit; cite tool state but ARE narrative records of that state |
| **Planning docs** | `docs/_planning/phase-17-brief-d-plan-2026-05-11.md` | Decision-precursor prose; per-session work product; cites but doesn't track state |
| **Assessment docs** | this file | Same as planning; operator-reading-material |
| **Capability audits** | `docs/_audit/capability/*.md` (13 files) | Decision narratives ("operator-decided KEEP" / "operator-decided RETIRE") — these are durable records of capability decisions, not tracked state |
| **CLAUDE.md doctrine prose** | repo-root `CLAUDE.md` (parts) | Behavioral rules, doctrine summaries — narrative |

### §3.c Ambiguous (needs operator decision)

These data classes have **mixed semantics** — partly tool-fit (state, query-able), partly narrative (decision, archival). The right answer depends on operator's priorities (sync-burden-minimization vs grep-stable-record-keeping).

| Data class | Q-NN candidate | Tradeoff |
|---|---|---|
| **§9 PROJECT_FRAMEWORK.md itself** | Q-A1 | Could be retired (OpenProject canonical, §9 generated snapshot) OR retained (markdown canonical, sync burden persists). D-16-02.A doctrine currently says retain. |
| **CLAUDE.md "Current state" sections** | Q-A2 | Could be generated from NetBox + OpenProject queries OR stay as operator-maintained prose with periodic staleness sweeps. Generation reduces drift; loses grep-ability of historical session-states. |
| **PROJECT_FRAMEWORK.md §3 lifecycle vocabulary + §10 KI register block** | Q-A3 | Lifecycle vocabulary is doctrine (markdown-right); KI register is state (tool-right). Currently bundled in one file. |
| **Closeout-audit scorecards** | Q-A4 | The 8-criterion table is state-tracked-progress (tool-right) but the audit doc IS a narrative record (markdown-right). Same shape as §9 — embedded state in a narrative doc. |
| **Change records (CR-17-NNN)** | Q-A5 | OpenProject explicitly has a change-record-workflow primitive per ADR-A-018; but the 6 existing CRs are markdown narratives with rich context. Migration cost vs ongoing-edit-cost. |

### §3.d Generated, not authored (query result, not source)

Some files are *currently authored* but *ideally generated* from the tool of record. Treating them as generated artifacts (not source) eliminates the manual sync burden by definition.

| Artifact | Generated from | Migration shape |
|---|---|---|
| **§9 PROJECT_FRAMEWORK.md deliverable table** | OpenProject work packages with external_id `D-NN-MM` | Replace manual table with `# Generated from OpenProject 2026-05-11T12:00:00Z` header + auto-rendered table via `scripts/openproject-render-§9.py` (new) |
| **CLAUDE.md "Current Inference Stack" + "Network Topology" sections** | NetBox query + LiteLLM config inspection | Replace prose with `# Generated 2026-05-11T...` header + auto-rendered prose via `scripts/claude-md-render.py` (new); operator edits doctrine portions only |
| **Container roster in audit docs** | NetBox container roster | Audit doc embeds `docker ps` snapshot today; could embed NetBox query result instead — same shape, durable source |
| **§10 KI register block in PROJECT_FRAMEWORK.md** | OpenProject (or GitHub Issues) issue list | Replace inline KI list with generated table |
| **Closeout-audit Criterion 5 KI status table** | OpenProject query | Same |
| **Phase-NN scorecard in closeout audit** | OpenProject version completion + per-version WP closure rate | Same |

The generated-not-authored bucket is the most leverage-rich migration path: each generation eliminates a recurring manual-sync class.

---

## §4 Migration paths for §3.a items

For each system-of-record-fit item, what does migration look like? What's off-LAN-doable prep vs LAN-gated execution?

### §4.A Deliverable register (§9 → OpenProject)

**Current direction:** markdown canonical (`PROJECT_FRAMEWORK.md` §9) → OpenProject mirror (via `scripts/openproject-sync-from-framework.py`).

**Inverted direction (proposed):** OpenProject canonical → markdown snapshot (via `scripts/openproject-render-§9.py`, new).

**Data shape mapping (already exists per D-17-04 / D-17-55 / D-17-31):**

| §9 markdown | OpenProject |
|---|---|
| `D-NN-MM` row identifier | Work Package external_id custom field |
| Row title | WP subject |
| Status enum (NOT STARTED / IN PROGRESS / DONE / DEFERRED) | WP status (New / In progress / Closed / On hold) |
| Body description | WP description |
| Carry-forward annotations | WP custom field OR comments |
| D#NN doctrine cross-refs | WP links |
| ESCALATED-TO-PHASE-18 markers | WP version association (Phase-18) |
| CR-17-NNN escalation refs | WP linked to CR work package |

**Migration steps:**

1. **Off-LAN prep:** verify `scripts/openproject-sync-from-framework.py` is current; author `scripts/openproject-render-§9.py` (read OpenProject WPs, emit §9-shaped markdown table). Test against current §9 — round-trip equivalence per ADR-A-012 doctrine.
2. **LAN execution (Brief D candidate):** populate OpenProject with all 123 §9 rows (sync script already does this); verify; flip authority direction by replacing §9 contents with "Generated from OpenProject" header + rendered table.
3. **Doctrine update:** amend D-16-02.A or author new ADR superseding the markdown-canonical assertion. Without this ADR amendment, the migration violates an Accepted ADR.

**Off-LAN-doable now:** render-script authoring + round-trip equivalence harness.
**LAN-gated:** OpenProject API populate + verify + flip.

### §4.B Known issues → OpenProject (or alternative)

**Same shape as §4.A** but smaller scope (10 KI files vs 123 deliverables).

**Decision branch:**

- Path A: KI register migrates into OpenProject as a separate work-package type (per ADR-A-018's "change-record workflow" capability). Single tool covers deliverables + KIs + CRs.
- Path B: KI register migrates to GitHub Issues. Separate from OpenProject (operator preference: minimize tool count); benefit: GitHub's mature notification/triage/labeling. Drawback: split between two tools (OpenProject for deliverables; GitHub for KIs).
- Path C: KI register stays markdown-canonical; sync burden accepted on the narrow surface (only ~10 files; only ~3-5 status flips per quarter per session-history).

Operator decision needed (Q-B1 in §8).

### §4.C Service registry → NetBox

**Already migrated per ADR-A-014.** Open items:

- Container roster (full `docker ps` snapshot per host) — partial; gated on Brief D LAN-session NetBox reconciliation (per Brief D plan WP-D-05).
- `config/service-registry.yaml.DEPRECATED` retirement — operator-discretion when audit cycle closes.

**Off-LAN-doable now:** nothing more; substrate is canonical.
**LAN-gated:** container roster reconciliation in Brief D.

### §4.D Phase rollups + closeout scorecards

**Phase versions** are already in OpenProject per D-17-31.

**Closeout-audit scorecards** are currently markdown (the 8-criterion phase-17-closeout-audit). They could be generated from OpenProject (version completion % + per-criterion WP status) — but the audit doc itself is a snapshot with narrative reasoning (per §3.b), so the scorecard is plausibly embedded-state-in-narrative, not standalone.

**Recommendation:** keep audit docs as markdown narratives; if scorecards drift, generate the *table* portion only via a render script; preserve the prose reasoning.

---

## §5 Cost-benefit per major migration

Sequenced by leverage (highest impact first).

### §5.A §9 deliverable register → OpenProject-canonical

| Dimension | Estimate |
|---|---|
| **Manual-sync burden reduced** | ~10-15 §9 row edits per closeout session; ~25 cross-reference annotation operations across audit/planning docs; ~5 framework-table-sanity hook validations |
| **Tooling lift required** | Author `openproject-render-§9.py` (~200-300 lines, mirror shape of existing sync script); update pre-commit framework-table-sanity hook to validate generated-vs-cached snapshot; one ADR superseding D-16-02.A markdown-canonical assertion |
| **Risk transfer** | Markdown is grep-able + git-versioned + survives tool outages. OpenProject dependency adds runtime requirement to read §9 state. Mitigation: render-script caches a markdown snapshot in repo; consumers can read either path |
| **Migration cost (one-time)** | All 123 §9 rows already in OpenProject per D-17-04 sync; flip is a single commit replacing §9 contents with generated snapshot + script + ADR |
| **Recommendation** | **Phase 18 candidate.** Highest-leverage migration. Off-LAN render-script authoring + round-trip equivalence test is doable now; flip itself is LAN-gated (needs OpenProject API access to verify pre-flip state). |

### §5.B Closeout-audit-doc-vs-§9 drift surface

Lower-leverage but immediately actionable:

| Dimension | Estimate |
|---|---|
| **Manual-sync burden reduced** | Audit-doc reclassifications track §9 status; each §9 row status change requires an audit-doc edit. Per this session: 4 audit-doc edits, all caused by §9 reclassifications |
| **Tooling lift required** | None if §5.A lands first (audit references generated §9 table directly). Standalone: pre-commit hook validating audit-cited §9 row IDs still exist in §9. |
| **Risk transfer** | Low |
| **Migration cost** | Zero if §5.A lands; otherwise add a `framework-table-coherence` cross-reference validator hook |
| **Recommendation** | **Tag along with §5.A.** Don't author independently. |

### §5.C KI register → OpenProject (or GitHub Issues)

| Dimension | Estimate |
|---|---|
| **Manual-sync burden reduced** | ~3-5 KI status flips per session-history quarter; cross-reference between §10 framework block + audit doc Criterion 5 + ADR-A-020 §5 Q-5 |
| **Tooling lift required** | KI-frontmatter-parser writing to OpenProject API (path A) OR GitHub Issues API (path B). Either is ~100-200 lines. |
| **Risk transfer** | Markdown is grep-able; KI files are individual documents that work well as standalone narratives. Risk: structured tool obscures the narrative. |
| **Migration cost** | 10 KIs × manual review + tool entry. Tractable but not zero. |
| **Recommendation** | **Phase 18 candidate, lower priority than §5.A.** Wait for §5.A to demonstrate the pattern works. |

### §5.D Container roster → NetBox

**Already partial.** Brief D WP-D-05 closes this via NetBox-vs-`docker ps` reconciliation. Cost is reconciliation effort, not migration design.

| Dimension | Estimate |
|---|---|
| **Manual-sync burden reduced** | Audit doc container-roster snapshots become NetBox query results; eliminates "snapshot is stale by the time it's committed" class |
| **Tooling lift required** | NetBox container-type custom field provisioning (if not already); script to populate from `docker ps` |
| **Migration cost** | Brief D WP-D-05 effort already scoped |
| **Recommendation** | **Land via Brief D as already planned.** |

---

## §6 Immediate Thread A WP-5 implications

Thread A WP-5 work (pending merge on `feat/thread-a-wp-5-adr-020-propagation`) was authored in the markdown-everywhere paradigm. Per this assessment:

| WP-5 edit | §3 bucket | Disposition |
|---|---|---|
| 4 doctrine docs cross-referencing ADR-A-020 (`work-routing-doctrine.md` Q-1 section, `capability-self-knowledge.md` cross-ref, `goose-capability-boundary.md` Q-7 section, `integration-audit-doctrine.md` Finding 23) | §3.b narrative documents | **EXECUTE — markdown is right here.** Doctrine docs are narrative; ADR-cross-references are part of the durable narrative record. |
| 2 wrapper script enforcement gates (`wrap-opencode.sh` Q-2 refuse + `wrap-goose.sh` Q-7 approval prompt) | §3.b code (operational substrate) | **EXECUTE — wrapper scripts are markdown-equivalent canonical code.** |
| 1 wrapper script header comment (`wrap-aider.sh` cross-reference) | §3.b code | **EXECUTE.** |
| 5 §9 row annotations (D-17-13/23/53/95/101 cross-refs) | §3.d generated-not-authored (eventually); §3.a system-of-record-fit (currently) | **DEFER / RESHAPE.** Under the proposed §5.A migration, these annotations become unnecessary (regenerated from OpenProject metadata each render). Under current markdown-canonical state, they're worth landing for short-term audit-trail integrity. |
| Q-4 LiteLLM config audit (no edit needed; SATISFIED) | §3.a system-of-record (LiteLLM config) | **NO CHANGE.** Config file is canonical; sync burden already minimal. |

**Recommendation:** WP-5 should land as-authored. The §9 annotations are short-term durable; if §5.A lands in Phase 18, those annotations become regeneration inputs (the OpenProject WP comment field captures the cross-reference).

This assessment does NOT block WP-5 merge. The migration paths it proposes are Phase 18 candidates, not Phase 17 closeout blockers.

---

## §7 Recommendations (sequenced)

| Horizon | Action | Substrate | Off-LAN? |
|---|---|---|---|
| **This session (immediate)** | Land WP-5 propagation as-authored | doctrine + wrappers + §9 annotations | Off-LAN-doable (already authored) |
| **Pre-Brief D (off-LAN, optional)** | Author `scripts/openproject-render-§9.py` + round-trip equivalence harness against current §9 | new script | Off-LAN-doable (script authoring is local; render against cached OpenProject snapshot from D-17-31 import) |
| **Brief D (LAN-gated)** | Per Brief D plan WP-D-05: NetBox-vs-container reconciliation; close `config/service-registry.yaml.DEPRECATED` retirement | NetBox | LAN-gated |
| **Phase 18 high-leverage** | §9 deliverable register → OpenProject-canonical (§5.A path); supersede D-16-02.A markdown-canonical doctrine via new ADR | OpenProject + new ADR | Mostly off-LAN; one LAN-session for flip-verification |
| **Phase 18 medium-leverage** | CLAUDE.md "Current state" sections → generated from NetBox + OpenProject queries (§3.d path) | new render script | Off-LAN-authoring; LAN-gated verification |
| **Phase 18 lower-leverage** | KI register → OpenProject OR GitHub Issues (§5.C path; operator chooses path A vs B) | OpenProject or GitHub | Mostly off-LAN |
| **Phase 18 lower-leverage** | Change records (CR-17-NNN) → OpenProject change-record-type work packages | OpenProject | Mostly off-LAN |
| **Phase 18 / structural** | Retire §9 as authored surface; OpenProject = deliverable system-of-record canonical | OpenProject + supersede ADR | Mostly off-LAN |

---

## §8 Operator decisions surfaced

Each item where this assessment surfaces a decision rather than a recommendation.

| Q# | Question | Recommendation | Affects |
|---|---|---|---|
| **Q-A1** | §9 PROJECT_FRAMEWORK.md authority direction — retain markdown-canonical (current D-16-02.A) or invert to OpenProject-canonical (proposed §5.A)? | **Invert** post-Phase-17 closeout. Phase-17 finishes on markdown; Phase-18 flips authority. Requires new ADR superseding D-16-02.A. | §9 + OpenProject; new ADR |
| **Q-A2** | CLAUDE.md "Current state" sections — generated (proposed §3.d) or operator-maintained prose? | **Generated** for state sections (Current Inference Stack, Network Topology); preserve operator-maintained for doctrine paragraphs | CLAUDE.md + new render script |
| **Q-A3** | PROJECT_FRAMEWORK.md §3 (lifecycle vocabulary) and §10 (KI register block) — same migration or split? | **Split**: §3 lifecycle vocabulary is doctrine (stays markdown); §10 KI register block is state (migrates with §5.C) | §3 + §10 (different fates) |
| **Q-A4** | Closeout-audit scorecards — generated or narrative? | **Embedded-narrative**: scorecards stay markdown, but if drift becomes painful, generate the *table* portion only via render-script (preserve prose) | audit docs |
| **Q-A5** | Change records (CR-17-NNN) — markdown narrative + OpenProject mirror, or OpenProject canonical? | **Phase 18 deferral**: 6 existing CRs are narrative-rich; migration cost > current sync burden | change-records/ |
| **Q-B1** | KI register migration path — OpenProject (single tool, path A) or GitHub Issues (split, path B)? | **Path A (OpenProject)**: minimize tool count; deliverables + KIs + CRs in one substrate; OpenProject's work-package-type primitive supports the distinction natively per ADR-A-018 | new tooling; operator preference |
| **Q-C1** | This assessment's recommendations — bundle into a single Phase-18 deliverable D-18-NN, or split per migration? | **Bundle as D-18-NN: "Source-of-truth migration"** with WP breakdown per §7 horizon; single deliverable preserves the cross-cutting nature | Phase-18 framework |
| **Q-C2** | Should this assessment land via a sibling ADR (ADR-A-021)? | **No — assessment first**: this doc is review material; if operator accepts the recommendations, the Q-A1 ADR supersession is the right ADR (not a meta-ADR about source-of-truth taxonomy itself) | next-ADR scope |

---

## End of assessment

Assessment doc only. No tool migrations executed; no markdown source-of-truth edits beyond authoring this file. Thread A WP-5 should still land per §6 disposition — markdown-narrative work is unaffected by the proposed migrations. Phase 18 candidates listed in §7 horizon table; operator decisions enumerated in §8 gate per-migration scope.

**Net assessment:** the markdown-everywhere paradigm has served Phase 17 well for narrative documents (ADRs, runbooks, doctrine, audits) but is over-extended for state-tracked data (deliverable register, KI register, container roster). The cost of structural migration is bounded — OpenProject is already deployed with the deliverable substrate populated; NetBox is already the canonical CMDB — and the manual sync burden eliminated would substantially reduce this-session-equivalent friction in future closeout work.
