# Aider Intelligence Layer Doctrine (D-17-103)

**Status:** DONE — 2026-05-04
**Chronicle scope:** Three-layer guardrail system wired into `aider-task.sh` and supporting modules.

---

## Motivation

Two recurrent failure modes on 2026-05-04 motivated this layer:

1. **Finding 19 (D-17-101 close)** — Aider accepted a multi-paragraph doc-authoring task, produced a 3-line truncation stub, and exited 0. No diff sanity check caught it.
2. **qwen3-coder-next selective-rewrite failure** — On a large file, the model rewrote unrelated content near the target hunk. No pre-flight check refused the shape.

Both failures were silent: exit 0, no guard, downstream pipeline consumed corrupt output. The intelligence layer makes these failures loud before and after execution.

---

## Architecture: Three Layers

```
aider-task.sh invocation
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2 — Pre-flight validator (domains/router.py)         │
│  BEFORE Aider runs                                          │
│  Inspects: description, task_class, file list + sizes       │
│  Exits script 3 on BLOCK; logs WARN and continues           │
└─────────────────────────────────────────────────────────────┘
       │ (if ok/warn)
       ▼
  [Aider executes]
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1 — Diff sanity check (bin/aider_guard.py --inline)  │
│  AFTER Aider runs                                           │
│  Inspects: per-file deletion rates, truncation signals      │
│  Exits script 4 on BLOCK; exits 2 (warn, logged, continue)  │
└─────────────────────────────────────────────────────────────┘
       │ (if pass/warn)
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Learning feedback (domains/learning.py)          │
│  ALWAYS called (success, failure, block, no-change)         │
│  Writes to: artifacts/execution_metrics.jsonl               │
│  Powers: recommend_model(), should_escalate()               │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer 2 — Pre-flight Validator

**Implementation:** `domains/router.py::preflight_validate(description, task_class, files)`
**Called from:** `aider-task.sh` before dry-run check
**Override:** `--skip-preflight` flag or `AIDER_SKIP_PREFLIGHT=1` env var
**Exit code on block:** 3

### BLOCK Shapes

| Shape | Trigger | Reason |
|---|---|---|
| `doc-append` | append/extend keyword + `.md` file >50 lines | Multi-paragraph doc authoring is permanently Tier 2 per D-17-101. Aider truncates at >3 lines reliably. |
| `rewrite-large` | rewrite/restructure/rework/redesign keyword + any file >300 lines | qwen3-coder-next failure shape: selective-rewrite on large files touches unrelated content. |
| `c1-multi-file` | `task_class == "C1"` + >2 files | C1 is single-source deliberate analysis. >2 files violates Tier 1 doctrine. |

### WARN Shape

| Shape | Trigger | Action |
|---|---|---|
| `long-doc-task` | description >200 chars + large `.md` + no fix/update/correct/patch keywords | Logs warning, proceeds. Heuristic: likely authoring, not patching. |

### Append keywords (doc-append)

```
append, add section, add §, extend, insert, add finding,
add chronicle, add entry, add related, add step
```

### Relationship to D-17-101

D-17-101 established the boundary rule: multi-paragraph doc authoring is permanently Tier 2 (Claude Code), not Tier 1 (Aider). Layer 2 is the mechanical enforcement of that boundary — it does not require the operator to remember the doctrine. The `doc-append` shape is the primary enforcement point.

---

## Layer 1 — Diff Sanity Check

**Implementation:** `bin/aider_guard.py --inline`
**Called from:** `aider-task.sh` after Aider exits and CHANGED_FILES are detected
**Override:** `--skip-validator` flag or `AIDER_SKIP_VALIDATOR=1` env var
**Exit code on block:** 4

### Per-file Deletion Rate

Compares `git diff --numstat` deletions against `git show HEAD:<path>` line count:

| Task type | Threshold | Label |
|---|---|---|
| Append task (description has append/add/extend/insert/prepend/attach) | 2% | `2% (append task)` |
| General / refactor | 30% | `30%` |

Exceeding the threshold generates a **BLOCK** entry. The 2% threshold for append tasks captures the Finding 19 failure mode: append tasks should delete nothing; even 2% deletion is suspicious.

### Truncation Detection

Warns if:
- File is `.md`
- File had >50 lines at HEAD
- Task description is multi-paragraph (>150 chars or has chronicle/doctrine/runbook keywords)
- Aider added ≤3 lines

This is a **WARN**, not a block — Aider may legitimately add only a small correction to a large doc. The signal is for operator review, not automatic rejection.

### Artifacts

On BLOCK, writes `artifacts/aider_runs/guard-inline-<ts>.json` with:
- description, task_class, files checked
- block messages, warn messages
- timestamp

### Relationship to existing task-file mode

The `--inline` mode is additive to the original `--task-file` JSON mode (which does scope validation + diff-budget checking). Inline mode does not require a task JSON file and runs the deletion-rate + truncation checks only. Both modes are wired under the same binary.

### Relationship to D-17-93 (telemetry gap)

D-17-93 identified the gap: no structured execution outcome telemetry. Layer 1 artifacts + Layer 3 JSONL records are the first telemetry substrate. The inline guard artifact captures block/warn signals; the learning JSONL captures every outcome (including guards). Future dashboards (D-17-93 follow-on) can consume both.

---

## Layer 3 — Learning Feedback Loop

**Implementation:** `domains/learning.py::LearningDomain.record_execution()`
**Called from:** `aider-task.sh` in all terminal branches
**Output:** `artifacts/execution_metrics.jsonl` (append-only)
**Consumed by:** `TaskRouter.classify()` via `learning.recommend_model()` / `learning.should_escalate()`

### Outcome events recorded

| Branch | success | error_type |
|---|---|---|
| Aider succeeds, guard passes | `True` | — |
| Aider exits non-zero (error/timeout) | `False` | `"timeout"` / `"aider_error"` |
| No files changed after Aider | `False` | `"no_changes"` |
| Guard blocks (exit 4) | `False` | `"diff_sanity_block"` |

### Learning signal used by router

`recommend_model()` returns a confidence-weighted model recommendation from execution history. `should_escalate()` checks the recent success rate; if it drops below threshold, the router escalates future tasks to Tier 2 automatically (skips LOCAL_AIDER, routes to CLAUDE_CODE).

This closes the D-17-91 feedback gap: model fitness data from real task execution feeds back into routing decisions. Previously, routing was keyword-only with no empirical correction.

### Relationship to D-17-91 (model fitness)

D-17-91 established fitness benchmarks for qwen3-coder:30b and qwen3-coder-next:latest on synthetic tasks. Layer 3 collects fitness data on *real* production tasks, providing ongoing empirical grounding beyond the D-17-91 snapshot.

---

## Exit Code Table (aider-task.sh)

| Exit | Meaning |
|---|---|
| 0 | Success — Aider ran, guard passed, files changed |
| 1 | Escalation or Aider error (non-zero exit from Aider) |
| 3 | Pre-flight BLOCK (Layer 2 refused the task shape) |
| 4 | Diff sanity BLOCK (Layer 1 refused the post-run diff) |

Exit 2 is reserved (unused in current implementation).

---

## Override Ladder

For operator bypass in exceptional cases:

```bash
# Skip Layer 2 only (pre-flight):
aider-task.sh --skip-preflight ...

# Skip Layer 1 only (diff sanity):
aider-task.sh --skip-validator ...

# Skip both via env (useful for pipeline invocations):
AIDER_SKIP_PREFLIGHT=1 AIDER_SKIP_VALIDATOR=1 aider-task.sh ...
```

Both overrides log a visible message; neither is silent.

```bash
# Allow large insertions in Layer 1 (legitimate refactors):
aider-task.sh --allow-large-insertions ...
```

---

## Finding 23 — Insertion-expansion duplication failure (D-17-109, 2026-05-04)

**Gap:** Layer 1 deletion-rate guard caught destructive mutations but missed duplication failures. On a 27KB Python file, the model duplicated 607 lines of existing code into the output. The deletion check passed (net deletions were low) but the file grew from ~700 lines to ~1300 lines. The duplication was silent: exit 0, guard passed, corrupt output committed.

**Root cause:** The guard only checked `deletions / (insertions + deletions)` ratio. A pure duplication — many insertions, few deletions — produces a near-zero deletion ratio and passes cleanly.

**Fix (D-17-109 WP-05):** Added `check_insertion_expansion()` to `bin/aider_guard.py`:
- Counts `def ` and `class ` lines in the HEAD version of each changed Python file (definition density baseline)
- Blocks if `total_insertions > 3.0 × total_definitions` across all changed Python files
- New files are excluded (no HEAD baseline; insertion count is expected to be high)
- Bypass: `--allow-large-insertions` flag (for legitimate large refactors); also bypassed by `--skip-validator`

**Threshold rationale:** 3× definitions captures the case where a model copies an entire function/class section once. A file with 50 `def`/`class` lines legitimately accepting 150 new lines is plausible (doc additions, stub additions). Accepting 450+ new lines in one Aider pass on a single file is not.

**Performance data recorded (D-17-109):**
- Empirical failure: 607-line duplication on 27KB file, qwen3-coder-next:latest (default temp=1.0)
- Contributing factor: base model default temperature (1.0) is creative-writing profile, not coding
- Fix: `Modelfile-qwen3-coder-next-coding` sets `temp=0.15`; `Modelfile-qwen3-coder-30b-coding` sets `temp=0.1`
- Both derivations use `num_ctx=32768` (was default 4096 — context window mismatch explained 360s timeouts on 31KB files)

---

## Override Ladder (updated D-17-109)

| Override | Scope | Use when |
|---|---|---|
| `--skip-preflight` | Layer 2 only | Task shape check too conservative for known-safe task |
| `--skip-validator` | Layer 1 only (all checks) | Known-good diff, want to bypass entirely |
| `--allow-large-insertions` | Layer 1 insertion-expansion only | Legitimate large refactor adding many new functions |
| `AIDER_SKIP_PREFLIGHT=1` | Layer 2 (env) | Pipeline invocations |
| `AIDER_SKIP_VALIDATOR=1` | Layer 1 (env) | Pipeline invocations |

---

## Cross-references

- **D-17-101** — Multi-paragraph doc authoring boundary (Layer 2 enforcement target)
- **D-17-91** — Model fitness benchmark (Layer 3 extends empirically)
- **D-17-93** — Telemetry gap (Layer 1 artifacts + Layer 3 JSONL are the first substrate)
- **D-17-97** — Mac Studio compute redirect (provides the models Layer 3 evaluates)
- **Finding 19** — Truncation silent failure that motivated Layer 1 truncation detection
- **Finding 23** — Insertion-expansion duplication failure; motivated `check_insertion_expansion()` guard (D-17-109)
- **D-17-109** — Aider performance tuning: Modelfile derivations (temp, ctx), system context injection, Layer 1 expansion guard
- `docs/runbooks/aider-default-workflow.md` §13 — operator-facing procedure incorporating all three layers
- `docs/architecture-facts/work-routing-doctrine.md` — Tier boundary definitions that Layer 2 enforces
- `config/ollama/Modelfile-qwen3-coder-30b-coding` — temp=0.1, num_ctx=32768 derivation
- `config/ollama/Modelfile-qwen3-coder-next-coding` — temp=0.15, num_ctx=32768 derivation
