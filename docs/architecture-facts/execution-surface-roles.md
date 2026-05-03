# Execution surface roles — durable doctrine

Authoritative role boundary across the AI surfaces and automated
agents that touch this platform. Items here outlive any single
deliverable; revisions append to the bottom with date + originating
WP.

This chronicle exists to fix a single question in writing before
class-by-class migration deliverables (downstream of D-17-53)
start touching it: **what work runs on which surface, and what
never moves?** The §18.O migration framework is class-by-class,
not platform-wide; the role boundary is the rail that prevents
migration creep into roles that must remain frontier.

Sibling chronicles:
- `goose-capability-boundary.md` — what Goose, specifically,
  is allowed to do (extension surface posture)
- `promotion-criteria.md` — how a work-class moves from frontier
  to local-primary (gates, baselines, demotion triggers)
- `goose-session-pipeline.md` — operational pattern for Goose
  execution sessions (prompt structure, review gate, chronicle)
- `migration-telemetry.md` — cost / quality measurement
  framework that feeds promotion-gate decisions

---

## The three roles

The platform's AI/automation surface is partitioned into three
roles. The roles are defined by *responsibility*, not by *which
binary you're talking to* — the same physical surface can act in
different roles depending on the work. The doctrine names the
roles so a session can be classified without ambiguity.

### CONTROL — frontier surface, never migrates

**What:** the operator-facing PM / control window. Today this is
the frontier model accessed via claude.ai (the chat-UI window the
operator drives directly), with Anthropic-grade reasoning quality
and full-context multi-session synthesis.

**Responsibilities:**
- **Architectural decisions.** Cross-deliverable trade-offs,
  choosing between approaches, declaring scope.
- **Cross-session synthesis.** Reading state across multiple
  open deliverables, surfacing conflicts, integrating findings
  that span more than one execution surface's view.
- **Correctness review** of execution-surface output. During the
  validation phase of any class migration, CONTROL reviews
  EXECUTION's proposed mutations *before* commit.
- **Ambiguity resolution.** When an execution surface surfaces
  back with options, the CONTROL role makes the call.
- **Doctrine authoring.** Findings, chronicle entries, role
  boundaries, promotion criteria — the substrate that
  EXECUTION later operates against.
- **Operator directive interpretation.** Translating high-level
  operator intent ("we should harden the Vault path") into a
  decomposed set of work-classes that EXECUTION can run.

**Migration posture:** **never migrates to local AI.** This is a
hard rail in the §18.O framework, not a "until proven otherwise."
The CONTROL role's value comes from frontier-grade reasoning
applied to high-judgment work where the cost of being subtly
wrong dwarfs the cost of the inference. Migrating CONTROL would
trade the substrate that *enables* class-by-class migration
elsewhere for marginal token-cost savings on the lowest-volume
work — net-negative across every relevant axis.

The corollary: anything that needs to be reviewed before an
external observer (operator, future-self, compliance) trusts it
runs in CONTROL, regardless of whether EXECUTION could
plausibly produce a similar artifact. Trust authority is a
CONTROL property.

### EXECUTION — Claude Code + Codex CLI + Goose, progressively migrating

**What:** the surfaces that drive sessions which read files, call
tools, edit the repo, run commands, produce commits. Today three
surfaces are in use:

- **Claude Code** (Anthropic's CLI) — default for high-judgment
  execution work. Pairs with `claude-local` (Ollama via litellm)
  or `claude-pro` (Anthropic API).
- **Codex CLI** (OpenAI's CLI) — used in parallel for cross-check /
  second-opinion review on execution work.
- **Goose** (Block, Apache 2.0) — Ollama-native (qwen3-coder:30b on
  Mac Studio), currently in capability-validation phase per
  D-17-13 (`goose-capability-boundary.md`).

**Responsibilities:**
- **Repo modifications.** File edits, file creation, file moves,
  staged changes.
- **Commit authorship.** Both as primary author (during local-
  primary classes) and co-author (during dual-review windows).
- **Tool execution.** Reading files, running shell commands
  (where capability surface allows), MCP tool calls, deployment
  scripts.
- **Surface-back authoring.** When a class's WP gates require
  operator approval, EXECUTION authors the surface-back; CONTROL
  reads it and makes the call.

**Migration posture:** **PROGRESSIVELY migrates frontier →
local**, class by class, per the promotion-criteria framework
(`promotion-criteria.md`). The migration is not a flag-flip; it
is a per-class N=5-clean-execution gate followed by a dual-review
window followed by promotion to local-primary. Demotion paths
exist (`promotion-criteria.md` §"Demotion criteria").

The class-by-class shape is critical: a single EXECUTION surface
(say, Goose+T3-B) is simultaneously local-primary for some
classes, dual-review for others, and not-yet-evaluated for
others. The mental model is "promotion is per (surface ×
class)," not per surface.

### AUTONOMOUS — launchd agents, scripts, sweeps

**What:** the scheduled / triggered automation that runs without
human or LLM intervention. Today this includes:

- launchd agents in `docker/launchd-agents/` (e.g.
  `com.iap.arr-apikey-sweep.plist` hourly,
  `com.iap.buildarr-sync` daily 03:00,
  `com.iap.platform-registry-refresh` and siblings)
- shell-script sweeps in `scripts/` (e.g.
  `arr-apikey-sweep.sh`, `backup.sh`)
- scheduled chronicled sync runs (e.g.
  `openproject-sync-from-framework.py` when scheduled)

**Responsibilities:**
- **Scheduled remediation.** e.g. functional-probe → recreate
  → resync sweeps that close drift.
- **Periodic syncs.** e.g. framework → OpenProject mirroring,
  registry refreshes.
- **Backup and audit jobs.** e.g. nightly Restic backups,
  audit-log archival.

**Migration posture:** **not AI-driven, no migration concept.**
AUTONOMOUS work is deterministic logic shipped as code; it neither
calls LLMs nor benefits from frontier-grade reasoning. It exists
in a different layer entirely. EXECUTION authors AUTONOMOUS code
(and CONTROL reviews architectural choices in the authoring); but
once shipped, AUTONOMOUS runs without further AI involvement.

The interesting boundary case: an AUTONOMOUS sweep that *fails*
escalates to EXECUTION (or to CONTROL if the failure crosses
class boundaries). The failure→escalation path is the AI-driven
part; the running-the-sweep part is not.

---

## The boundary in practice

### Worked example — D-17-13 WP-06 (Goose drafts a runbook)

- **CONTROL** (operator + frontier PM) defined the work-class
  ("Goose drafts runbook from N source files; pure read+author"),
  picked the specific test deliverable (`goose-operations.md`
  draft), and reviewed Goose's output for defects pre-commit.
- **EXECUTION** (Goose with qwen3-coder:30b on Mac Studio Ollama)
  read the 3 source files via filesystem-mcp, ran
  `list_allowed_directories` autonomously to verify scope, and
  produced the draft runbook in 51 seconds.
- **Frontier EXECUTION** (Claude Code under claude-pro) authored
  the corrected runbook based on Goose's draft (75/25 split),
  wrote the chronicle observations, and ran the commit.
- **AUTONOMOUS** was not involved.

The work-class is now session 1 of 5 toward Phase-A promotion for
this class (per `goose-capability-boundary.md` Phase-A gate +
`promotion-criteria.md` framework).

### Worked example — D-17-50 (Prowlarr↔consumer apiKey sweep)

- **CONTROL** identified the doctrine pivot (per-implementation
  two-key model, not single-master), surfaced the trigger
  (functional HTTP 401 not hash mismatch), and made the
  judgment call.
- **EXECUTION** (Claude Code under claude-pro) authored the
  sweep script (`arr-apikey-sweep.sh`), executed the structural
  remediation (Prowlarr-side DELETE+recreate Application
  POST + ApplicationIndexerSync), and verified Sonarr/Radarr
  release-search end-to-end.
- **AUTONOMOUS** (launchd `com.iap.arr-apikey-sweep.plist` hourly)
  now runs the sweep on schedule. It calls no LLM; it executes
  deterministic remediation logic.

The judgment-heavy decision (doctrine pivot) lived in CONTROL;
the implementation work lived in EXECUTION; the operational
recurrence lives in AUTONOMOUS.

---

## Hard rails

These are the boundary properties that downstream migration
deliverables must not violate. They exist to keep migration from
being load-bearing on assumptions that haven't been validated.

1. **CONTROL never migrates.** No deliverable should propose
   running operator-facing PM / synthesis / correctness-review
   work on a local AI surface. The frontier surface's
   correctness-review function is the rail that *enables* the
   class-by-class migration approach; replacing the rail with
   the thing it's reviewing collapses the framework.

2. **EXECUTION migration is per (surface × class), not per
   surface.** A class can be local-primary on Goose+T3-B while
   another class is still frontier-only on Claude Code. The
   matrix is not "Goose has graduated"; it is "Goose has
   graduated for class C1 and C2, is in dual-review for C3, and
   has not been evaluated for C4–C8." Promotion criteria and
   demotion triggers operate at the cell level.

3. **AUTONOMOUS does not call LLMs.** Sweeps, syncs, and
   schedulers are deterministic code. If a future deliverable
   considers wiring an LLM into a launchd-driven path, that work
   *re-classifies* into EXECUTION (with appropriate role-boundary
   review) — it doesn't get smuggled in as "the cron job got
   smarter."

4. **Trust authority is CONTROL-side; drafting is EXECUTION-side.**
   Anything an external observer (operator, compliance, future-self)
   needs to trust without re-deriving is *approved* by CONTROL.
   EXECUTION can *draft* trust-bearing artifacts (ADRs, doctrine
   entries, chronicle revisions, runbooks); CONTROL reviews and
   ratifies them before they become authoritative.

   The split is the same pattern as D-17-13 WP-06's worked example:
   Goose drafted the runbook (EXECUTION), frontier corrected the
   draft (still EXECUTION, frontier-tier), operator approved before
   commit (CONTROL). Authority accrues at the approval step, not
   the drafting step. Drafting is structured authoring and is a
   **Phase-B promotion candidate** — once a class has cleared the
   N=5 gate for read-only authoring, structured-authoring of
   trust-bearing artifacts is the next class up. Approval never
   migrates: it is the CONTROL-side function that *makes the
   drafting-class promotable* in the first place.

   Corollary: a chronicle entry that an EXECUTION surface produced
   without CONTROL approval is a *draft*, regardless of how
   well-formed it looks. It does not become doctrine until the
   approval step lands.

5. **Force-multiplier, not replacement.** Local AI in EXECUTION
   role is a force multiplier on operator capacity (lower
   per-class cost, more parallel work, faster iteration on
   bounded tasks). It is **not** a replacement for the CONTROL
   role's correctness-review and architectural-judgment
   functions, which remain frontier indefinitely.

---

## Why this lives in `architecture-facts/`

Role boundary outlives D-17-53. Every downstream class-migration
deliverable will reference *this boundary*, not the phase-17 file
tree. Phase docs reference *events*; architecture-facts reference
*durable posture*.

This chronicle is the foundational pointer for `promotion-
criteria.md`, `goose-session-pipeline.md`, and
`migration-telemetry.md` — they assume this role boundary holds
and only define mechanisms within it.
