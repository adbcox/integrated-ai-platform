# Goose capability boundary — durable doctrine

Chronicle of which Goose 1.x extensions are enabled, which are
disabled, and what the promotion gates look like for moving from
*capability-validation* to *Phase-A active* posture. Items here
outlive any single deliverable; revisions append to the bottom
with date + originating WP.

This chronicle exists because Goose ships a wide, opinionated
extension surface (file edit, shell exec, subagent delegation,
sandboxed apps, chat recall, top-of-mind injection, code-mode tool
elision, orchestration). Enabling it all on day-1 of a new model-
backend pairing is the wrong default — capability-validation needs
*observability of model behavior*, not full autonomy. The platform
treats capability adoption as a stepwise promotion: read-only
substrate first, write/exec extensions only after N clean reviewed
executions.

Sibling chronicles:
- `local-tool-calling.md` — what local model backends emit
  (substrate-side observability)
- `integration-audit-doctrine.md` — durable rules across deliverables
  (process-side observability)

---

## Posture 1 — Capability-validation phase (current, D-17-13 reopen)

**Date:** 2026-05-03
**Originating WP:** D-17-13 WP-05
**Backend pair:** Goose 1.33.1 + ollama provider + qwen3-coder:30b on
Mac Studio Ollama 0.22.1

### Operator-stated boundary

> "Filesystem read/write, git, bash sandboxed, curl" was the original
> recommendation; tightened during WP-05 to **read-only substrate +
> repo introspection** for capability-validation. No docker / ssh /
> Vault access initially.

The tightening rationale: capability-validation is about *observing
model behavior*, not getting work done. A model that misroutes a
shell command should fail at "no shell available" before it fails at
"shell ran but did the wrong thing." Read-only is the cheapest probe.

### Extension status

| Extension | Type | Enabled | Rationale |
|---|---|---|---|
| `filesystem-mcp` | stdio MCP | **YES** | Repo read access scoped to `/Users/admin/repos/integrated-ai-platform`. Cannot escape via path traversal (MCP server enforces root). |
| `xindex` | stdio MCP | **YES** | Service registry / catalog read. Read-only by design (xindex-mcp exposes no mutating tools). |
| `todo` | platform | **YES** | Internal task list — local model state, not platform state. |
| `analyze` | platform | **YES** | Tree-sitter directory/symbol overview. Read-only on the same paths `filesystem-mcp` already grants. |
| `skills` | platform | **YES** | Discovery of available skills from filesystem + builtins. Read-only. |
| `extensionmanager` | platform | **YES** | Lets Goose enable/disable *its own* extensions. Capability self-knowledge, no escape. |
| `developer` | platform | **NO** | **Shell exec + file write.** Out of scope for "no docker/ssh/Vault initially." Re-enable gate: §Promotion. |
| `summon` | platform | **NO** | Subagent delegation. We want to observe Goose's *own* behavior, not delegated chains. |
| `apps` | platform | **NO** | Sandboxed HTML/CSS/JS apps — out of scope for repo-execution work. |
| `chatrecall` | platform | **NO** | Past-conversation search — frontier-PM context, not execution-surface. |
| `summarize` | platform | **NO** | LLM summary calls outside tool-loop — capability-validation wants *observed* tool use, not bypass paths. |
| `tom` | platform | **NO** | Top-of-mind injection via env vars. Not used in this phase. |
| `code_execution` | platform | **NO** | "Code mode" elides tool calls into Python execution. Capability-validation needs the explicit tool-call surface, not the bypass. |
| `orchestrator` | platform | **NO** | Multi-agent session management. Same rationale as `summon`. |

### Where this is enforced

`config/goose/config.yaml` (repo) → `~/.config/goose/config.yaml`
(operator-local). Each disabled extension carries `enabled: false`
with an inline rationale comment. The enforcement is not sandboxed
— Goose reads its own config and respects it. A future capability-
isolation layer would be a subprocess wrapper or container, but
for capability-validation phase, config-respect is sufficient.

### Operator review obligation

While this posture holds, **operator review on all Goose output is
mandatory before any platform-state change is taken from it.** Goose
in capability-validation mode is allowed to *propose* changes (file
diffs in conversation, recommended commits, identified bugs); it is
not allowed to *enact* them. Anything Goose-authored that lands on
disk lands via operator copy-paste / operator git operations.

This is why commit identity (`Goose <bot@…>` style git author) was
deferred at D-17-13 WP-04 — pre-staging an identity for an enacting
capability that hasn't been promoted is premature.

---

## Promotion gate — Phase-A active

**Status:** Not yet entered. Recorded here so the gate criteria are
fixed before they get retroactively softened.

### Required to enter Phase-A active

1. **N ≥ 5 clean reviewed executions** in capability-validation
   posture, where "clean" means:
   - Tool calls were structurally valid (no malformed JSON, no
     hallucinated tool names, no out-of-scope path attempts).
   - Operator review found no doctrine violations in the proposed
     output (no credential exfil, no out-of-scope file reads, no
     misrouted recommendations).
   - The model recovered correctly from at least one tool error
     (file-not-found, permission-denied, network-fail) without
     requiring operator nudge.
2. **F1.B substrate stability:** Ollama 0.22.1 on Mac Studio
   continues to emit structured `tool_calls` in streaming mode for
   qwen3-coder:30b across at least N=5 sessions. Regression here
   forfeits Phase-A entry until substrate is patched.
3. **Operator decision recorded** in WP-08 chronicle of whichever
   D-NN-NN owns the promotion (likely a follow-on to D-17-13).

### What changes at Phase-A active

Re-enable, in order, with separate sub-gates:

1. **`developer` extension** — file write + shell exec scoped to
   the repo. Sub-gate: capability-bounded shell allowlist (initially
   `git status`, `git diff`, `git log`, `pytest`, `uv run` — not
   docker/ssh/sudo/curl-to-platform-internal). Commit identity
   question becomes live here.
2. **`summon`** — subagent delegation. Sub-gate: subagents inherit
   parent capability boundary by construction; review burden
   compounds, so only enabled once primary-Goose review pattern is
   established.
3. **`code_execution`** — tool-elision via Python. Sub-gate:
   tool-call observability tooling exists to recover the
   would-have-been calls from elided executions, otherwise this
   regresses the capability-validation observability win.

`apps`, `chatrecall`, `summarize`, `tom`, `orchestrator` are
explicitly **out of scope** for Phase-A. They serve UX polish
(`apps`, `chatrecall`) or context-injection (`tom`, `summarize`)
patterns that aren't on the platform's execution-surface roadmap.
Revisit per-extension only on operator request.

---

## Observed behavior — capability-validation phase, sessions 1–2

**Status:** First two measured sessions (D-17-13 WP-03 smoke test +
WP-06 first test deliverable). Track ongoing through Phase-A
promotion gate's N≥5 criterion.

### Session 1 — WP-03 smoke test (read /etc/hosts equivalent)

- 2 tool calls: `read_text_file` (CLAUDE.md head=50)
- All structurally valid; tool-loop closed cleanly
- Model autonomously ran no scope-check (first session, simple prompt)

### Session 2 — WP-06 first test deliverable (draft runbook from 3 sources)

- 6 tool calls: 4× `read_text_file`, 1× `list_allowed_directories`,
  1× `todo_write`
- All structurally valid; all paths within scope
- Model **autonomously** ran `list_allowed_directories` before
  reads — no instruction to do so
- Wall-clock: 51 seconds
- Output split: ~75% Goose draft / ~25% frontier correction

### Patterns to preserve at Phase-A re-enable

1. **Cautious-by-default scope check.** Two of two sessions where
   the model could verify scope before reading, it did. When
   `developer` re-enables (write/exec), the corresponding pattern
   is "verify path, run dry-run, then commit" — Phase-A re-enable
   design must not regress this.
2. **Tool-call structural validity.** 8/8 tool calls across two
   sessions emitted as structured `tool_calls` (F1.B substrate).
   Re-enabling write tools should not change this; the substrate
   is independent of capability surface.

### Patterns to correct via prompt engineering

1. **Padding tendency.** WP-06 draft included two padding sections
   (Security checklist, Backups) that didn't fit the runbook
   reference-style. Standard prompt preamble for Phase-A briefs:
   *"If uncertain about whether a section is necessary, omit
   rather than pad. Reference docs are concise; sections-because-
   docs-have-them is wrong."*
2. **Self-blind to encountered failure modes.** WP-06 draft
   omitted the `GOOSE_MODE=auto` headless invocation pattern even
   though that was the exact failure encountered while running
   the test. Standard prompt preamble: *"If a failure mode was
   encountered during the work itself, document it explicitly
   even if it feels like meta-information about the run."*

### Cost / economics observation

WP-06 work-class (read 3 files + draft a runbook) completed in 51s
on local Mac Studio compute vs the equivalent frontier-API
invocation. First measured data point validating the §18.O
execution-surface migration thesis: progressive migration of
work-classes to local T3-B with frontier doing correctness review.

Re-measure at N=5 sessions to confirm directionality (cost,
quality, defect rate).

### Headless invocation gotcha

`GOOSE_MODE=smart_approve` (the config default) blocks **any**
non-interactive run that triggers a tool-approval prompt — even
read-only tools like `todo_write` (which writes only to internal
session state). Headless invocation requires per-invocation
`GOOSE_MODE=auto` env override. Do NOT change the config default;
the approval gate is correct for interactive sessions.

```bash
# Headless / scripted run
GOOSE_MODE=auto goose run --no-session --instructions /path/to/prompt.txt
```

This is documented in `docs/runbooks/goose-operations.md` §1.

---

## Why this lives in `architecture-facts/` and not in a phase doc

Capability-boundary policy outlives D-17-13. Future deliverables that
adopt or migrate Goose configurations (re-pair with a different
local backend, add a new MCP extension, evaluate a Goose successor)
will reference *this posture*, not the phase-17 file tree. Phase
docs reference *events*; architecture-facts reference *durable
posture*.

Cross-references at next chronicle update (WP-08):
- `local-tool-calling.md` — F1.B append (qwen3-coder:30b streaming
  structured tool_calls — F1 refinement along
  (model-family × Ollama-version) axis)
- `integration-audit-doctrine.md` — F14 (mDNSResponder negative-
  cache sub-doctrine, sibling to D-17-21 authority doctrine)
