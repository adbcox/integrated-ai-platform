# System Prompt Library consolidation audit (2026-05-11)

**Trigger.** Claude Code pre-flight discipline on a proposed "System
Prompt Library scaffold" brief surfaced that the platform already has
TWO parallel system-prompt libraries on `main`, both claiming
authority, with substantial overlap on the 4 canonical prompt names
(voice-fast / deliberate-analysis / code-review / decomposition). The
scaffold brief was halted; this audit replaces it as the discovery
deliverable.

**Status:** AUDIT-ONLY. No consolidation work executed. Cleanup
brief follows after operator review.

**Recommendation (one line, full rationale in §8):** Library A
(`docs/system-prompts/`) and Library B (`config/prompts/library/`)
serve different layers — A is documentation/doctrine (D-17-11), B is
runtime presets (D-17-90/D-17-121, load-bearing on bin/aider_*,
scripts/aider-task.sh, multiple doctrine docs). Recommend **preserve
both libraries with explicit scope-boundary documentation** rather
than merge; the dual-library state is functional, not redundant. The
operator decision required is whether to formalize the layer split or
accept-as-is.

---

## Method

Per the `docs/_audit/phase-18-status-audit-2026-05-04.md` precedent:
inventory both libraries, classify content overlap and unique items,
surface cross-reference graph, propose corrections.

- Inventories via `find <library>/ -type f -exec wc -l -c {} \;`.
- Drift classification via `diff -u` per overlapping prompt pair.
- Cross-reference graph via `grep -rln '<library-path>'` across
  `*.md *.yml *.yaml *.sh *.py *.json`, excluding the library
  directories themselves and `_archive` / `node_modules` /
  `task-sets/` noise.
- Authority-claim verification by reading each library's README /
  CATALOG verbatim.
- Branch state: `feat/system-prompts-consolidation-audit` cut from
  `main` at `8c10ec43`. No working-tree changes other than this audit
  doc.

---

## Library A — `docs/system-prompts/` (D-17-11)

**Authority claim** (`docs/system-prompts/README.md` L3-7, verbatim):

> Status: Repo-managed library of system-prompt content for the
> platform's local LLM stack. D-17-11 deliverable. D#22 architecture
> reference: this directory is canonical; if a consumer service ships
> inline prompt text that differs from the content here, the content
> here wins and the consumer should be updated.

**Intended axes (L11-19):** Modes (what kind of work) + Tiers (which
model class). Composable: consumer concatenates `<mode> + <tier>` to
form the runtime system prompt.

**Inventory:**

| File | Lines | Bytes | Purpose |
|---|---|---|---|
| `README.md` | 233 | 10334 | Authority doctrine; mode/tier index; consumer integration contract; D-17-23 slot-binding contract |
| `modes/voice-fast.md` | 30 | 1219 | Low-latency conversational; voice front-end |
| `modes/deliberate-analysis.md` | 50 | 2249 | Multi-step reasoning; design discussion |
| `modes/code-review.md` | 62 | 2739 | Read-only critique posture |
| `modes/decomposition-planning.md` | 62 | 2934 | Splits task into independently-executable sub-specs |
| `modes/capability-permission.md` | 130 | 5830 | D-17-23 slot fill — pre-grants for Flavor C/D capabilities |
| `tiers/T1-general-purpose.md` | 43 | 1891 | Default-class chat models (qwen-coder-32b-class) |
| `tiers/T2-throughput.md` | 44 | 2009 | 7B–14B class; smaller context; fast |
| `tiers/T3-specialty.md` | 50 | 2388 | Code-fine-tune, domain-specific (D-17-12 evaluation) |
| `tiers/T4-distributed.md` | 62 | 3137 | Multi-node via exo cluster (D-17-14) |
| `consumers/litellm-routing.md` | 103 | 4392 | Descriptive: how litellm-gateway composes prompts |
| `consumers/open-webui-integration.md` | 119 | 4979 | Descriptive: how Open WebUI selects prompts |

**Totals:** 12 files, 988 lines, ~46 KB. Descriptive-only — README L131-134 explicitly states *"D-17-11 does NOT modify litellm_config.yaml or Open WebUI runtime config. That wiring is a follow-on operational task."*

---

## Library B — `config/prompts/library/` (D-17-90, D-17-121)

**Authority claim** (`config/prompts/library/v1.0.0/CATALOG.md` L1-5, verbatim):

> System Prompt Library — Catalog
> Version: 1.0.0
> Effective: 2026-05-04
> Derivation: D-17-90 (T1 system prompt library); D-17-53 session analysis (Sessions 1–13)

**Intended axes:** Personas (task-class C0/C1/C2/C3 mapping) + standard preamble + Aider-tier1 presets + verifier prompt. Versioned via semver directories (v1.0.0/, v1.1.0/).

**Inventory:**

| File | Lines | Bytes | Purpose |
|---|---|---|---|
| `v1.0.0/CATALOG.md` | 65 | 3163 | Library index; persona-selection guide; task-class mapping; versioning convention; cross-references |
| `v1.0.0/00-standard-preamble.md` | 84 | 4024 | Verbatim preamble for C1 tasks (mandatory); D-17-53 Session 9 validated content |
| `v1.0.0/01-voice-fast.md` | 55 | 2087 | C0 persona; ≤50 lines output target; ≤1 source |
| `v1.0.0/02-deliberate-analysis.md` | 105 | 4084 | C1 persona; 2+ source synthesis to runbook/doctrine output |
| `v1.0.0/03-code-review.md` | 71 | 2916 | C2 persona; structured critique on diff/file input |
| `v1.0.0/04-decomposition.md` | 71 | 3210 | C3 persona; splits complex deliverables into subtask specs |
| `v1.0.0/05-persona-routing.yaml` | 59 | 2429 | LiteLLM/Open WebUI routing config (YAML) |
| `v1.0.0/06-aider-tier1-presets.md` | 181 | 5430 | Tier 1 routing presets + Claude Code/Codex refusal preamble (D-17-95) |
| `v1.0.0/07-deepseek-verifier-prompt.md` | 107 | 3606 | DeepSeek dual-loop verifier prompt (D-17-110) |
| `v1.0.0/personas/INDEX.md` | 80 | 4088 | Persona Library v1.0.0 index — D-17-121; task class × model routing table |
| `v1.0.0/personas/voice-fast.md` | 38 | 1606 | Persona variant (D-17-121) |
| `v1.0.0/personas/deliberate-analysis.md` | 95 | 4079 | Persona variant (D-17-121) |
| `v1.0.0/personas/code-review.md` | 91 | 3882 | Persona variant (D-17-121) |
| `v1.0.0/personas/decomposition-planner.md` | 134 | 5853 | Persona variant (D-17-121) |
| `v1.1.0/07-deepseek-verifier-prompt.md` | 112 | 3682 | Version-incremented verifier prompt |

**Totals:** 15 files, 1391 lines, ~54 KB. Runtime-wired (see §6 cross-reference graph).

---

## Overlap analysis — 4-pair drift classification

| Pair | A path | B path | Classification | Evidence |
|---|---|---|---|---|
| voice-fast | `modes/voice-fast.md` (30 lines) | `v1.0.0/01-voice-fast.md` (55 lines) | **DIVERGENT** | A: "Mode: voice-fast" heading + posture/don't/do shape. B: "Persona: voice-fast" with task-class/derivation header, when-to-use/when-NOT-to-use/key-characteristics. ~25 line delta. Both name the same intent (low-latency conversational); shape and metadata differ substantially. |
| deliberate-analysis | `modes/deliberate-analysis.md` (50 lines) | `v1.0.0/02-deliberate-analysis.md` (105 lines) | **DIVERGENT — B is superset-ish** | A: posture / uncertainty-discipline / don't / do. B: when-to-use / when-NOT-to-use / characteristics / D-17-53 derivation. B has 2x A's content and cites empirical D-17-53 sessions (Session 9 clean outcome, Session 13 failure analysis). |
| code-review | `modes/code-review.md` (62 lines) | `v1.0.0/03-code-review.md` (71 lines) | **DIVERGENT** | A: severity-graded findings (bug/smell/style/nit/opinion) with findings shape. B: when-to-use, derivation note (no pure C2 D-17-53 sessions; persona derived from D-17-12 benchmarks + goose-capability-boundary). Similar size; substantively different structure. |
| decomposition | `modes/decomposition-planning.md` (62 lines) | `v1.0.0/04-decomposition.md` (71 lines) | **DIVERGENT** | A: spec-shape detail (ID / Subject / Scope / Inputs / Outputs / Acceptance / Dependencies). B: when-to-use + derivation from goose-capability-boundary + §18.O migration framework. Both target the same intent; structural shapes differ. |

**All 4 pairs are DIVERGENT** — no IDENTICAL or SEMANTICALLY-EQUIVALENT pair. Library B consistently adds: explicit task-class label (C0/C1/C2/C3), derivation lineage (D-17-53 session or doctrine source), when-to-use vs when-NOT-to-use boundaries, model-class routing hints. Library A consistently adds: tighter posture/don't/do prescriptive shape, optional spec-shape micro-templates.

**Conclusion:** A merge would lose distinctive content from EITHER side. The two libraries authored against different requirements at different times — they're not duplicates of the same intent.

---

## Unique-content map — per-library files with no counterpart

| File | Library | Lines | Purpose | Consolidation disposition (proposed) |
|---|---|---|---|---|
| `modes/capability-permission.md` | A | 130 | D-17-23 slot fill — pre-grant Flavor C/D capabilities | **KEEP-IN-A** (D-17-23 slot-bind contract; no B counterpart) |
| `tiers/T1-general-purpose.md` | A | 43 | T1 tier framing | **KEEP-IN-A** (B has no tier axis) |
| `tiers/T2-throughput.md` | A | 44 | T2 tier framing | **KEEP-IN-A** |
| `tiers/T3-specialty.md` | A | 50 | T3 tier framing (D-17-12 eval) | **KEEP-IN-A** |
| `tiers/T4-distributed.md` | A | 62 | T4 tier framing (D-17-14 cluster) | **KEEP-IN-A** (referenced by `exo-cluster.md`) |
| `consumers/litellm-routing.md` | A | 103 | Descriptive: LiteLLM composes prompts | **NEEDS-OPERATOR-DECISION** (overlaps in intent with `v1.0.0/05-persona-routing.yaml` but Library A is descriptive prose, B is config) |
| `consumers/open-webui-integration.md` | A | 119 | Descriptive: Open WebUI selects prompts | **NEEDS-OPERATOR-DECISION** (same axis as `05-persona-routing.yaml`) |
| `v1.0.0/00-standard-preamble.md` | B | 84 | Mandatory C1 preamble (D-17-53 Session 9 validated) | **KEEP-IN-B** (runtime-load-bearing; no A counterpart) |
| `v1.0.0/05-persona-routing.yaml` | B | 59 | LiteLLM/Open WebUI routing config | **KEEP-IN-B** (runtime config; no A counterpart) |
| `v1.0.0/06-aider-tier1-presets.md` | B | 181 | Aider Tier 1 presets + Claude Code/Codex refusal preamble (D-17-95) | **KEEP-IN-B** (cited by `work-routing-doctrine.md` L165) |
| `v1.0.0/07-deepseek-verifier-prompt.md` | B | 107 | DeepSeek dual-loop verifier (D-17-110) | **KEEP-IN-B** (cited by `bin/aider_verifier.py`) |
| `v1.0.0/personas/INDEX.md` | B | 80 | D-17-121 persona library index | **KEEP-IN-B** (D-17-121 deliverable) |
| `v1.0.0/personas/voice-fast.md` | B | 38 | D-17-121 persona variant | **NEEDS-OPERATOR-DECISION** (relationship to `v1.0.0/01-voice-fast.md` unclear — Library B has internal duplication between numbered presets and personas/) |
| `v1.0.0/personas/deliberate-analysis.md` | B | 95 | D-17-121 persona variant | **NEEDS-OPERATOR-DECISION** (same internal-duplication concern) |
| `v1.0.0/personas/code-review.md` | B | 91 | D-17-121 persona variant | **NEEDS-OPERATOR-DECISION** (same) |
| `v1.0.0/personas/decomposition-planner.md` | B | 134 | D-17-121 persona variant | **NEEDS-OPERATOR-DECISION** (same; note name drift: `decomposition-planner` here vs `04-decomposition` in numbered) |
| `v1.1.0/07-deepseek-verifier-prompt.md` | B | 112 | Versioned variant of v1.0.0/07 (+5 lines) | **KEEP-IN-B** (D-17-110 v1.1 evolution) |

**Library B internal duplication concern:** the 4 personas in `v1.0.0/personas/` mirror the 4 numbered presets `01-04` in the same v1.0.0/ directory. CATALOG.md L9-17 lists only the numbered presets, NOT the personas/ subdirectory. The INDEX.md at `personas/` cites D-17-121 (2026-05-05) — authored AFTER the CATALOG.md (D-17-90, 2026-05-04). Whether personas/ supersedes the numbered presets, augments them, or is parallel scaffolding is not documented in either library.

---

## Cross-reference graph

### Library A consumers (sparse — documentation-only)

| Path | Reference |
|---|---|
| `docs/PROJECT_FRAMEWORK.md` | D-17-11 row references `docs/system-prompts/` |
| `docs/architecture-facts/exo-cluster.md` | L109, L638 cite `tiers/T4-distributed.md` |
| `docs/architecture-facts/integration-audit-doctrine.md` | L680: "Cluster G: docs/system-prompts/ — canonical-as-is (operator decision; preserves D-17-11 self-contained library shape)" — surfaced via D-17-16 Loose-doc retirement |
| `docs/phase-17/d-17-12/INTAKE_2026-05-03.md` | L155 cites `tiers/T1.md`, `T2.md`, `T3-mac-studio.md` (note: paths are stale — current tier filenames are `T1-general-purpose.md` etc.) |
| `docs/_audit/loose-doc-inventory-2026-05-03.md` | D-17-16 inventory artifact |

**Library A is referenced descriptively in 5 docs. No runtime script loads files from `docs/system-prompts/`. Sparse blast radius.**

### Library B consumers (extensive — runtime-wired)

| Path | Type | Reference |
|---|---|---|
| `bin/aider_verifier.py` | Runtime script | Loads verifier prompt from `config/prompts/library/v1.X.0/07-deepseek-verifier-prompt.md` |
| `bin/persona_loader.py` | Runtime script | Persona loader — purpose-built for this library |
| `bin/aider_envelope_benchmark.py` | Runtime script | Loads personas for benchmark scenarios |
| `scripts/aider-task.sh` | Operator-facing wrapper | Loads `06-aider-tier1-presets.md` per work-routing-doctrine |
| `docs/architecture-facts/local-prompt-library-doctrine.md` | Doctrine | Canonical doctrine for this library |
| `docs/architecture-facts/work-routing-doctrine.md` | Doctrine | L12, L165 cite v1.0.0/CATALOG.md + v1.0.0/06-aider-tier1.md |
| `docs/architecture-facts/aider-intelligence-doctrine.md` | Doctrine | References library |
| `docs/architecture-facts/aider-verifier-doctrine.md` | Doctrine | References v1.0.0/07-deepseek-verifier-prompt.md and v1.1.0 |
| `docs/phase-17/d-17-90/WP02_PROMPT_PATTERN_AUDIT_2026-05-04.md` | Phase artifact | D-17-90 source-of-truth for B's authoring |
| `docs/runbooks/aider-default-workflow.md` | Runbook | Operator invocation guide |
| `docs/PROJECT_FRAMEWORK.md` | Framework | D-17-90 / D-17-121 rows reference library |

**Library B is runtime-wired across 4 scripts + 5 doctrine docs + 1 runbook + framework rows. Heavy blast radius — retiring B would break operator-facing Aider workflow + multiple doctrine cross-references.**

---

## Consumer risk surface

| Consumer | Library | Risk if library moves/retires | Mitigation requirement |
|---|---|---|---|
| `bin/aider_verifier.py` | B (v1.x.0/07) | HIGH — verifier breaks on path change | Path constant must be updated and committed simultaneously with any library move |
| `bin/persona_loader.py` | B (v1.0.0/personas/) | HIGH — persona loading breaks | Same as above; loader is purpose-built |
| `bin/aider_envelope_benchmark.py` | B | MEDIUM — benchmarks reference personas | Coordinated update |
| `scripts/aider-task.sh` | B (v1.0.0/06) | HIGH — operator-facing Aider workflow surface | Operator-visible breakage; coordinated update mandatory |
| `docs/architecture-facts/work-routing-doctrine.md` | B (citations L12, L165) | LOW — cross-reference rot only | Mechanical sed update |
| `docs/architecture-facts/exo-cluster.md` | A (T4 tier) | LOW — cross-reference rot only | Mechanical sed update |
| `docs/architecture-facts/integration-audit-doctrine.md` | A (Cluster G note) | LOW — narrative reference | Manual review (the "canonical-as-is" framing depends on Library A's identity) |
| `docs/runbooks/aider-default-workflow.md` | B | MEDIUM — runbook accuracy | Coordinated update |
| `docs/phase-17/d-17-12/INTAKE_2026-05-03.md` | A (stale tier filenames) | LOW — already-stale | Could fix opportunistically or leave as historical artifact |
| Future `bin/*` scripts | B (versioned) | The semver directory structure provides forward-compatibility — `v1.0.0` stays put as new versions land alongside | Documented in CATALOG.md §"Versioning convention" |

**Net assessment:** Library A is documentation-only and could be moved or restructured with mechanical cross-reference fixes (5 cite sites, low blast radius). Library B is runtime-load-bearing across operator-facing scripts and doctrine; any move requires coordinated updates across ~10 cite sites including 3 Python loaders and the operator-Aider wrapper.

---

## Consolidation proposal

### Recommended disposition: **PRESERVE BOTH; formalize scope split**

The two libraries serve different layers, both purposeful:

- **Library A (`docs/system-prompts/`, D-17-11)** is the **documentation library** — composable mode-+-tier framework, consumer integration contracts described prose-style, no runtime wiring. Canonical reference for "what kinds of system prompts the platform has and how to compose them." Surfaces the T1-T4 tier axis (referenced by exo-cluster.md and phase-17 INTAKE) which has NO counterpart in Library B.
- **Library B (`config/prompts/library/`, D-17-90 + D-17-121)** is the **runtime preset library** — versioned via semver, task-class-labeled (C0/C1/C2/C3), wired into bin/aider_* scripts and scripts/aider-task.sh. D-17-53-session-derived; provides operator-facing presets with empirical lineage.

The 4-prompt overlap is intentional duplication of the same intent at two layers (documentation vs runtime). The drift between A's "Mode: voice-fast" and B's "Persona: voice-fast" reflects the different layers' framing needs.

### Surface Library B's counter-argument

The README at `docs/system-prompts/README.md` L3-7 makes a D#22 "this directory is canonical" claim. If taken literally and against Library B's later-authored existence, A's claim would imply that B should be retired and its unique content (preamble, persona-routing.yaml, aider-tier1-presets, verifier-prompt, personas/INDEX) migrated into A.

Operator counter-argument candidates:
- The D#22 claim was authored at D-17-11 (2026-05-03 ish) before D-17-90 (2026-05-04) and D-17-121 (2026-05-05) created the runtime layer. A's claim is documentation-scope; it does not bind a runtime layer that didn't exist at A's authoring.
- The runtime-wiring count (4 scripts + 5 doctrine docs + 1 runbook citing B) is heavier than A's (5 documentation-only citation sites). Retiring B would touch more surface than retiring A.
- The semver directory convention in B (`v1.0.0/`, `v1.1.0/`) is a forward-compatibility scaffold that A doesn't have. Folding B's runtime presets into A's flat structure would lose versioning.

### Content migration map (under PRESERVE BOTH disposition)

| Action | File(s) | Target |
|---|---|---|
| No move | All Library A files | Stay at `docs/system-prompts/` |
| No move | All Library B files | Stay at `config/prompts/library/` |
| Update | `docs/system-prompts/README.md` | Add a "Relationship to Library B" section explaining the two-layer split: A = documentation/doctrine, B = runtime presets. Remove or soften the D#22 "this directory is canonical" claim — it's true within A's documentation scope but does not bind B's runtime layer. |
| Update | `config/prompts/library/v1.0.0/CATALOG.md` | Add a "Relationship to Library A" cross-reference pointing at A as the documentation library. |
| Update | `docs/architecture-facts/integration-audit-doctrine.md` | L680 "Cluster G" note is correct (A canonical-as-is) but should be augmented with the layer-split framing. |

### Retirements (under PRESERVE BOTH)

- None forced. Operator may choose to retire Library A's `consumers/litellm-routing.md` and `consumers/open-webui-integration.md` (which describe integration prose-style) in favor of B's `v1.0.0/05-persona-routing.yaml` (which IS the integration config). Both could co-exist if A's descriptions are clearly labeled "descriptive overview, see `config/prompts/library/v1.0.0/05-persona-routing.yaml` for the runtime config."

### Library B internal-duplication question (REQUIRES OPERATOR DECISION)

The 4 personas in `config/prompts/library/v1.0.0/personas/` overlap with the 4 numbered presets `01-04` in the same v1.0.0/ directory. CATALOG.md doesn't acknowledge the personas/ subdirectory. INDEX.md cites D-17-121 (newer than CATALOG.md's D-17-90).

Three plausible interpretations:
- (a) personas/ supersedes the numbered presets (D-17-121 replaced D-17-90's structure mid-flight) — implies numbered presets should retire.
- (b) personas/ augments the numbered presets with model-routing hints (qwen2.5-coder:14b vs :32b per INDEX.md table) — both stay, INDEX.md becomes canonical for routing.
- (c) Accidental duplication; one of the two should retire.

Operator decision required before any cleanup. This audit cannot disambiguate without runtime evidence (which loader script actually reads which path).

### Versioning convention (for the survivor / both)

Library B already uses semver directories. CATALOG.md §"Versioning convention" specifies MAJOR.MINOR.PATCH semantics with version directory as source of truth and an optional `latest/` symlink. **Recommend preserving this in B.** Library A could optionally adopt the same pattern (flat → v1.0.0/) for future-proofing — but A is documentation-only and the versioning overhead may not be justified. **Recommend leaving A flat** unless documentation versioning becomes operationally useful.

### Filename convention

Library A: `modes/<name>.md`, `tiers/<name>.md`, `consumers/<name>.md`. Un-numbered.
Library B: `NN-<name>.md` for sequenced canonical presets; `personas/<name>.md` for D-17-121 persona variants. Numbered.

**Recommend preserving both conventions.** A's un-numbered convention reflects its mode-+-tier composition axis; B's numbered convention reflects sequenced loading order (00-preamble must load first, etc.). Cross-convention is acceptable across libraries.

### Open questions requiring operator decision

1. Accept the **PRESERVE BOTH** recommendation, or override with **MERGE INTO A** / **MERGE INTO B**?
2. Library B internal duplication: personas/ supersedes / augments / accidental? Which interpretation is correct, and what's the disposition for the loser?
3. Should Library A's `consumers/litellm-routing.md` + `consumers/open-webui-integration.md` retire (in favor of B's `v1.0.0/05-persona-routing.yaml`) or stay as descriptive prose siblings?
4. Should the D#22 "this directory is canonical" claim in A's README be softened to acknowledge B's runtime layer? Or operator wants to assert A's primacy over B?
5. Is the D-17-16 Loose-doc retirement decision (L680 of integration-audit-doctrine.md: "Cluster G: canonical-as-is") binding on this audit, OR is it open for revisit given that D-17-90 / D-17-121 authored Library B after that decision?

---

## Cleanup brief outline (for the follow-up authored by operator)

Under the **PRESERVE BOTH** recommendation, the cleanup work-packages are minimal:

| WP | Scope | Files | Commit shape |
|---|---|---|---|
| WP-1 | Add "Relationship to Library B" section to `docs/system-prompts/README.md` | 1 file modified | docs(system-prompts): document A/B layer split |
| WP-2 | Add "Relationship to Library A" cross-ref to `config/prompts/library/v1.0.0/CATALOG.md` | 1 file modified | docs(prompts-library): cross-ref to documentation library |
| WP-3 | Resolve Library B internal-duplication (personas/ vs numbered presets) per operator decision; possibly retire one set | 0-8 files | depends on operator decision |
| WP-4 | (Optional) Retire `consumers/litellm-routing.md` + `consumers/open-webui-integration.md` if operator decides B's `05-persona-routing.yaml` is the canonical runtime config and A's prose-descriptions are redundant | 2 files possibly retired | docs(system-prompts): retire descriptive consumer docs |
| WP-5 | Fix stale tier-filename references in `docs/phase-17/d-17-12/INTAKE_2026-05-03.md` (T1.md → T1-general-purpose.md etc.) | 1 file modified | docs(phase-17-intake): refresh tier path references |
| WP-6 | Update `docs/architecture-facts/integration-audit-doctrine.md` L680 Cluster G note to acknowledge the two-library split established by D-17-90 / D-17-121 | 1 file modified | docs(integration-audit-doctrine): augment Cluster G note for dual-library state |

Under a **MERGE** disposition, the cleanup would be substantially heavier:
- 7-12 files retired
- 10+ cross-reference sites updated mechanically
- Runtime scripts (bin/aider_verifier.py, bin/persona_loader.py, scripts/aider-task.sh) re-pathed and re-tested
- Multiple doctrine docs updated

The PRESERVE-BOTH path is lower-risk and respects the prior D-17-16 "canonical-as-is" disposition while acknowledging the post-D-17-16 evolution.

---

## Risk register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Audit misclassifies the personas/ vs numbered-presets relationship | MEDIUM | Could lead to a cleanup brief that retires the wrong half | Pre-flight surfaced this as NEEDS-OPERATOR-DECISION; cleanup waits for operator clarity |
| Audit underestimates Library B runtime blast radius | LOW | Cross-ref grep + bin/ inspection found 11 cite sites; may have missed scripts that load library files via dynamic-path construction | Cleanup brief should run a second-pass grep for `prompts/library` substring (not just full path) before retiring anything |
| Audit assumes consumer behavior without runtime evidence | MEDIUM | `bin/aider_verifier.py`, `bin/persona_loader.py`, `bin/aider_envelope_benchmark.py` are identified as loaders without actually inspecting their code paths | Cleanup brief should read each loader and confirm which library path it dereferences before re-pathing |
| D-17-16 Loose-doc retirement disposition ("canonical-as-is") may be operator-binding | HIGH | If the operator's earlier decision is binding, the audit's PRESERVE-BOTH recommendation matches; if NOT binding, the audit's MERGE-INTO-A or MERGE-INTO-B paths become live options | Operator review surfaces this explicitly as Open Question 5 |
| Library A's D#22 claim conflicts with Library B's existence | HIGH (already realized) | The claim is structurally false relative to current state; operator must decide whether to soften the claim or assert A's primacy | Operator decision in Open Question 4 |
| Future deliverables may add more prompt files to either library without acknowledging the dual-library state | MEDIUM | Drift continues; eventual audit redo | WP-1 / WP-2 in cleanup brief explicitly cross-references each library from the other's authority doc, making future-deliverable authors see both |

---

## Cross-reference summary (for the audit doc itself)

- This audit replaces a halted "System Prompt Library scaffold" brief that surfaced the dual-library state via Claude Code pre-flight discipline (2026-05-11).
- Authority docs: `docs/system-prompts/README.md` (Library A); `config/prompts/library/v1.0.0/CATALOG.md` (Library B); `config/prompts/library/v1.0.0/personas/INDEX.md` (Library B persona sub-layer).
- Cited doctrine: `docs/architecture-facts/local-prompt-library-doctrine.md`, `work-routing-doctrine.md`, `aider-intelligence-doctrine.md`, `aider-verifier-doctrine.md`, `integration-audit-doctrine.md` (L680 Cluster G note).
- Source-of-truth deliverables: D-17-11 (Library A); D-17-90 (Library B v1.0.0); D-17-121 (Library B personas/); D-17-110 (Library B verifier prompt); D-17-95 (Library B Aider tier-1 presets); D-17-16 ("canonical-as-is" disposition).
- Audit precedent: `docs/_audit/phase-18-status-audit-2026-05-04.md`.

---

## End of audit

No consolidation work executed. Cleanup brief drafts as a separate
follow-up message after operator review of this audit's
recommendations and the 5 open questions in §8.
