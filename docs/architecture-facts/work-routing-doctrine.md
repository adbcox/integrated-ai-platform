# Work-routing doctrine (D-17-95)

Defines which execution surface handles which class of work. The goal
is to match task shape to surface strength: Aider for bounded file edits
(fast, local, zero quota), Claude Code for orchestration and judgment,
Goose for MCP-driven agentic tasks, frontier escalation for novel
architecture or security decisions.

**Sibling docs:**
- `docs/runbooks/aider-default-workflow.md` — operator invocation guide
- `docs/architecture-facts/goose-capability-boundary.md` — Goose posture
- `config/prompts/library/v1.0.0/CATALOG.md` — persona selection

---

## Tier definitions

### TIER 1 — Aider-eligible

Surface: `scripts/aider-task.sh`

A task is TIER 1 if ALL of the following hold:

| Criterion | Requirement |
|-----------|-------------|
| File scope | ≤ 5 files, all pre-existing |
| Intent | Single purpose: fix, annotate, or refactor one clearly defined thing |
| Runtime probes | None — no `docker exec`, no `curl`, no service health checks |
| API / network calls | None during edit |
| Vault interaction | None — no secret reads, writes, or rotations |
| Docker operations | None — no compose up/down/restart |
| Judgment calls | None — task output is fully deterministic from file content alone |
| Surface-back gates | None required — operator can accept the diff without session-level deliberation |

**TIER 1 examples:**

- Add a one-line docstring to a function
- Fix a wording drift in a doctrine doc (verbatim word swap, no policy change)
- Add a type hint to a function signature
- Rename a variable or constant consistently across ≤ 3 files
- Add a header comment or annotation block to an existing file
- Fix a broken markdown link (static path, no URL resolution needed)
- Refactor a function into two without changing external interface
- Add a missing `cap_drop` or security_opt to a compose service stanza
- Sync a comment block to match updated code it describes
- Add `--help` text to an existing CLI script

---

### TIER 2 — Claude Code / Codex required

Surface: Claude Code (`claude-local` or `claude-pro`), or Codex

A task is TIER 2 if ANY of the following hold:

| Criterion | Implication |
|-----------|-------------|
| Multi-deliverable orchestration | Coordinates > 1 framework row or phase gate |
| Runtime probes required | Needs live service state (health check, docker inspect, vault read) |
| API calls | Calls OpenProject, OPNsense, Vault, Zabbix, or any platform API |
| Vault writes | Credential rotation, AppRole provisioning, policy authoring |
| Docker operations | compose up/down, exec into containers, image pull |
| Doctrine + judgment | Policy wording where the right answer depends on context |
| Surface-back gates | Task spec includes "surface back at WP-NN" |
| Cross-file consistency | Changes must stay consistent across > 5 files or the whole repo |
| Commit + push | Git operations beyond local staging (hooks, force-push decisions) |
| New file creation (non-trivial) | Authoring a net-new runbook, ADR, or architecture doc from scratch |
| Multi-paragraph doc authoring | Chronicle authoring, doctrine extension, structured finding append to existing docs |

**TIER 2 examples:**

- Provision a new Vault AppRole for a new service
- Run a health-check cycle and remediate credential drift
- Author a new architecture decision record
- Promote a deliverable in PROJECT_FRAMEWORK.md after a gate pass
- Write a new compose service with Vault Agent sidecar
- Run `buildarr-run.sh` and verify the result
- Migrate a DNS record from Unbound to Dnsmasq via the migration script
- Orchestrate a phase gate (run regression probe, update status, commit)
- Append a new Finding section to `integration-audit-doctrine.md`

**Aider refusal note for doc-authoring:** when a task is multi-paragraph
doc-authoring or structured chronicle append, Aider should refuse and surface
back with: "Tier 2 required — route to Claude Code/Codex for source-fidelity."

---

### TIER 3 — Frontier escalation

Surface: Claude Code under `claude-pro`, or manual operator decision

A task is TIER 3 if ANY of the following hold:

| Criterion | Implication |
|-----------|-------------|
| Novel architecture decision | No prior precedent in `docs/architecture-facts/` |
| Security review | Credential posture, capability surface, AppRole scope |
| Multi-system reasoning | Spans > 2 independent platform subsystems |
| Incident triage | Root-cause unknown, system in degraded state |
| Gate promotion requiring judgment | "Should this be DONE?" decision |
| Legal / compliance | Property, contract, or regulatory content |

**TIER 3 examples:**

- "Should we move Vault to a dedicated network interface?"
- "Is the current cap_drop posture sufficient for this threat model?"
- "Design the MacBook parity rollout sequence"
- Incident: selfheal is silent and health check endpoint returns 200

---

## Decision tree

```
New work request arrives
│
├─ Does it touch a file at all?
│   │
│   └── NO → TIER 2 or TIER 3 (judgment, research, orchestration)
│
├─ Does it touch ≤ 5 pre-existing files?
│   │
│   ├── NO → TIER 2 (too broad for Aider; needs planning surface)
│   │
│   └── YES ↓
│
├─ Does it require any of: runtime probe / API call / Vault read-write /
│   Docker operation / surface-back gate / policy judgment?
│   │
│   ├── YES → TIER 2
│   │
│   └── NO ↓
│
├─ Is the expected output fully deterministic from file content alone?
│   (i.e., could you write the diff on a whiteboard right now?)
│   │
│   ├── NO → TIER 2 (needs live context or judgment)
│   │
│   └── YES → TIER 1 — run scripts/aider-task.sh
│
└─ Is the task novel architecture, security posture, or multi-system?
    │
    └── YES → TIER 3
```

---

## Surface-routing preamble (for Claude Code / Codex dispatch)

Paste this at the top of any Claude Code or Codex task brief to enforce
Tier 1 routing compliance:

```
ROUTING PRE-CHECK (work-routing-doctrine.md D-17-95):
Before executing this task, classify it against the three-tier classifier:
- TIER 1 (Aider-eligible): ≤5 files, no runtime probes, no API/Vault/Docker,
  deterministic diff. If TIER 1: decline, surface back with the exact
  scripts/aider-task.sh invocation the operator should run instead.
- TIER 2 (Claude Code/Codex): proceed if orchestration, probes, Vault, or
  judgment are required.
- TIER 3 (frontier escalation): surface to operator for manual decision.
```

This preamble is canonicalized in
`config/prompts/library/v1.0.0/06-aider-tier1.md`.

---

## Rationale

Claude Code and Codex consume frontier quota. Aider on local Ollama is
free, fast (7–15s for a simple edit), and scoped to exactly the files
handed to it. The failure mode that motivated D-17-95: operators
habitually open Claude Code for a one-liner docstring fix, spending
quota tokens on a task that `qwen2.5-coder:14b` handles in 7 seconds.

The asymmetry is stark:

| Metric | Aider (TIER 1) | Claude Code (TIER 2) |
|--------|----------------|----------------------|
| Cost | Free (local Ollama) | Frontier quota |
| Latency | 7–30s | 30–120s |
| Context window | ≤ 5 files | Whole repo + tools |
| Failure mode | No-edit (recoverable) | Over-engineered fix |
| Appropriate scope | Bounded diff | Judgment + orchestration |

The doctrine does not restrict Claude Code from *performing* TIER 1
tasks — it instructs Claude Code to *recognize and redirect* them, so
the operator forms the habit of reaching for `aider-task.sh` first.

---

## Finding 19 (integration-audit-doctrine.md)

This doctrine establishes Finding 19: **Tier-classification is a
pre-dispatch obligation, not a post-hoc label.** Every AI session must
classify the task before emitting the first tool call. Skipping
classification and auto-routing to frontier is the F1 pattern from
D-17-93 (zero operator-initiated LOCAL_AIDER invocations despite 18
days of coding work — all of it routed to Claude Code by default).

Chronicle pointer: `docs/architecture-facts/integration-audit-doctrine.md`
Finding 19.

---

## Mechanical enforcement — three-layer intelligence system (D-17-103)

The tier boundaries above are enforced automatically by `aider-task.sh`
via three layers wired around every Aider invocation:

- **Layer 2 (pre-flight)** — `domains/router.py::preflight_validate()` — inspects
  task shape BEFORE Aider runs. BLOCKs doc-append, rewrite-large, C1-multi-file
  shapes (exit 3). Prevents the D-17-101 doc-authoring failure mode.
- **Layer 1 (diff sanity)** — `bin/aider_guard.py --inline` — inspects the diff
  AFTER Aider runs. BLOCKs excessive deletion rates (2% for append tasks, 30%
  for general). WARNs on truncation. Prevents silent no-op or destructive diff
  acceptance (exit 4).
- **Layer 3 (learning)** — `domains/learning.py::record_execution()` — records
  every outcome to `artifacts/execution_metrics.jsonl`. Router consults this
  log to tune future routing (confidence-weighted model selection, auto-escalation
  on low success rate).

Operator overrides: `--skip-preflight`, `--skip-validator` (or env vars).
Full doctrine: `docs/architecture-facts/aider-intelligence-doctrine.md`
