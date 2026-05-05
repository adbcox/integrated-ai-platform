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

## Architecture: Three Layers + 1.5

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
│  Inspects: per-file deletion rates, insertion-expansion     │
│  Exits script 4 on BLOCK; exits 2 (warn, logged, continue)  │
└─────────────────────────────────────────────────────────────┘
       │ PASS
       ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 1.5 — Dual-loop verifier (bin/aider_verifier.py)     │
│  D-17-110; runs AFTER Layer 1 passes                        │
│  LLM (qwen2.5-coder:14b) classifies: AGREE | DISAGREE       │
│  Exits script 5 on DISAGREE; non-blocking on ERROR/AMBIG    │
│  Catches: duplication, scope creep, logic rewrites          │
└─────────────────────────────────────────────────────────────┘
       │ AGREE or non-blocking error
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
| 0 | Success — Aider ran, all guards passed, files changed |
| 1 | Escalation or Aider error (non-zero exit from Aider) |
| 3 | Pre-flight BLOCK (Layer 2 refused the task shape) |
| 4 | Diff sanity BLOCK (Layer 1 refused the post-run diff) |
| 5 | Verifier BLOCK (Layer 1.5 DISAGREE — diff does not match task) |

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

## Findings 25-30 — D-17-111 hardening, envelope data, and verifier proof

### Finding 25 — System-context injection regressed into URL scraping / repo-map noise; default is now no-context

The D-17-109 wrapper path that prepended the full system-context block caused a repeatable regression on tonight's no-context-sensitive task: Aider attempted to scrape `http://127.0.0.1:11434`, pulled in unrelated repo-map suggestions, and emitted narration instead of SEARCH/REPLACE output. The same task succeeded cleanly when the wrapper ran with no injected context.

Doctrine change:
- `scripts/aider-task.sh` now defaults to **no context**
- `--with-context` injects the slim preamble only
- `--with-doctrine` injects the full block only when explicitly requested
- URL-like text in injected context is redacted before passing to Aider
- `--no-detect-urls` is passed to Aider to suppress URL scraping

### Finding 26 — Verifier env propagation must be layered, not shell-profile dependent

`AIDER_VERIFIER_API_BASE` and `AIDER_VERIFIER_MODEL` lived only in `~/.zshrc` on the Mac Mini, so non-interactive shells (`zsh -l -c`, SSH commands, cron) did not inherit them and the verifier fell back to the wrong endpoint.

Doctrine change:
- `bin/aider_verifier.py` now defaults to the Mac Studio endpoint and DeepSeek verifier model when env vars are absent
- `scripts/aider-task.sh` exports the same defaults before invoking the verifier
- the verifier prints whether each setting came from `env`, `arg`, or `default`
- optional `/etc/zshenv` persistence remains operator-controlled documentation only

### Finding 27 — Wrong-target ambiguity is a Layer 0 failure mode, not a Layer 1/1.5 afterthought

The `bin/test_stage3_executor.py` example has two `except` clauses. A prompt like "Replace bare except clauses with specific exception types" is ambiguous enough that the model can choose the wrong target unless the prompt is structurally disambiguated.

Doctrine change:
- `bin/aider_guard.py` now blocks ambiguous prompts before Aider runs when the description names a repeated pattern without structural context
- `--allow-ambiguous` exists only as an explicit bypass for tests
- the wrapper surfaces the block as a Layer 0 pre-flight failure

### Finding 28 — Line-number disambiguators are brittle and break SEARCH/REPLACE formatting

The line-number hint that seemed helpful in the moment (`at line 114`) is part of the failure mode. It pushes the model toward text matching and away from structural edits, and in this stack it degrades the quality of the Aider response.

Doctrine change:
- prompt conventions now prefer function/block/scope qualifiers over line numbers
- `--strip-line-refs` is available to remove `at line N` / `on line N` hints before dispatch
- prompt guidance is documented in `docs/aider-prompt-conventions.md`

### Finding 29 — Empirical envelope is narrower than the old "<=25KB green" assumption

The wrapper benchmark on 2026-05-04 sampled 9 Python files across 5KB → 114KB and produced only one clean success:
- `bin/aider_worker.py` (`7999` bytes, `13` def/class lines) succeeded in `51.51s` with `AGREE`
- `bin/aider_lib.py` (`5234` bytes) failed after `42.22s`
- `bin/aider_benchmark.py` (`15639` bytes) failed after `119.64s`
- `bin/stage5_manager.py` (`22844` bytes) exited `0` but produced no diff
- the remaining larger samples either hit guard/router exits immediately or produced no usable change

Conclusion: the old envelope claim is refuted by this sample. The current wrapper baseline is not reliably green across the 5KB–30KB band, and success is already fragile by ~8KB.

### Finding 30 — Live dual-loop verification currently has a false-negative blind spot on wrong-target diffs

The live Aider run on `bin/test_stage3_executor.py` earlier in this session selected the bare `except:` correctly. To prove the dual-loop path, a wrong-target diff was then replayed through the verifier: the diff changed the specific `except json.JSONDecodeError` clause instead of the bare `except:`. `bin/aider_guard.py` blocked the diff as ambiguous, but `bin/aider_verifier.py` still returned `AGREE`.

Conclusion: the current verifier prompt / model combination can miss a wrong-target edit if the diff is locally plausible. The verifier is useful, but not sufficient as a sole correctness gate on this class of edit. Proof artifact: `artifacts/aider_dual_loop_proof_2026-05-04.log`.

## Findings 31-37 — D-17-111 verifier v1.1.0, task routing, F25 standing instruction, and D-17-117 regression data

### Finding 31 — Verifier v1.0.0 was structurally blind to wrong-target edits; v1.1.0 adds full-file context and disambiguation rules

The `config/prompts/library/v1.0.0/07-deepseek-verifier-prompt.md` draft was sufficient for broad diff checks but still missed the D-17-111 wrong-target case. The v1.1.0 draft adds explicit full-file context, repeated-target comparison rules, and a wrong-occurrence DISAGREE rule so the verifier can reason about which repeated clause was actually edited.

### Finding 32 — Task type dominates file size in the empirical envelope

The D-17-117 benchmark shows that the old "file size alone" envelope is not stable, but the task-specific picture is even more mixed than the earlier one-dimensional claim:
- `docstring-add` had one real local success on `bin/aider_worker.py` (7,999 bytes / 13 defs / 48.63s / AGREE) and one trivial no-op success on `bin/aider_benchmark.py` where the file already satisfied the prompt
- `bare-except-narrow` did not succeed in the raw 36-run benchmark because the insertion-expansion guard was too tight for a narrow two-clause exception edit; after tuning the guard threshold, the same shape passes
- `type-hint-add` and `function-extract` remained zero-success in the sample

Conclusion: file size alone is not the routing axis. Mechanical edits remain Tier 1 candidates only when they are structurally narrow and the target file is small enough that the guard does not overreact; inference-heavy edits should route Tier 2 regardless of size.

### Finding 33 — The only tested model/prompt pair that caught the D-17-111 wrong-target diff was qwen3-coder:30b-coding + verifier v1.1.0

On the deliberately wrong-target replay, `qwen3-coder:30b-coding` with the v1.1.0 verifier prompt returned `DISAGREE`, while the same prompt against the clean correction returned `AGREE`. The other tested local verifier candidates (`deepseek-coder-v2:16b-lite-instruct-q4_K_M` and `qwen3-coder-next:coding`) still false-negatived the wrong-target case. The candidate matrix is captured in `docs/phase-18/d-17-111/WP-04C_MODEL_EVALUATION_MATRIX_2026-05-04.md`.

### Finding 34 — F25 output hygiene is now a standing instruction for agent prompts

Prompt hygiene is now a standing rule: keep prompts concise, structural, and URL-free unless the task explicitly needs the URL; prefer function/block scope over line numbers; and avoid narration-heavy context unless explicitly opted in. This is the rule the next session should assume by default when constructing agent prompts.

### Finding 36 — Multi-task envelope benchmarks must be read as task-type matrices, not single-size thresholds

The D-17-117 2D matrix (`artifacts/aider_envelope_2d_2026-05-05.csv`) captured 36 runs across four task types and nine files. The matrix is only meaningful when read by task type:
- `docstring-add`: the only real local success landed on the 7.9KB worker file; larger files either became no-ops or timed out/escaped routing
- `bare-except-narrow`: raw matrix runs were blocked by the insertion-expansion guard until the threshold was widened for narrow exception edits
- `type-hint-add` and `function-extract`: no successful local edits in this sample

Routing consequence: keep `docstring-add` and `bare-except-narrow` as Tier 1 only when the target is structurally narrow; route `type-hint-add` and `function-extract` to Tier 2 by default.

### Finding 37 — Wrapper E2E regression now covers the critical guardrails

The D-17-117 wrapper regression suite now exercises:
- default local flow on a bare-except edit
- `--with-context` opt-in for system context injection
- `--with-doctrine` opt-in for full doctrine injection
- Layer 0 ambiguity blocking plus `--allow-ambiguous` bypass
- `--strip-line-refs` prompt hygiene

Result: the regression path is now covered end-to-end, and the bare-except default flow passes after the insertion-expansion threshold tune.

### Finding 38 — Routing policy is now aligned with the empirical envelope

The D-17-118 routing update codifies the D-17-117 matrix:
- inference-heavy task patterns (`type hints`, `extract function`, `rewrite`, `rearchitect`) force Tier 2 regardless of file size
- mechanical patterns (`docstring-add`, `bare-except-narrow`, single-rename, typo/indentation fixes) remain eligible for Tier 1 when the file is structurally narrow
- `classify_task_complexity()` in `domains/router.py` is the gate that separates those two classes before the existing file-size and learning heuristics run

This makes the router explicit about the operator intent versus the file-size envelope instead of treating every file-bearing edit as the same coding shape.

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
- **D-17-110** — Layer 1.5 dual-loop verifier; see `docs/architecture-facts/aider-verifier-doctrine.md`
- **D-17-117** — Multi-task envelope benchmark + wrapper E2E regression
- `docs/runbooks/aider-default-workflow.md` §13 — operator-facing procedure incorporating all layers
- `docs/aider-prompt-conventions.md` — prompt-shape rules for structural disambiguation
- `docs/architecture-facts/work-routing-doctrine.md` — Tier boundary definitions that Layer 2 enforces
- `docs/architecture-facts/aider-verifier-doctrine.md` — Layer 1.5 model selection, bypass ladder, verdict semantics
- `bin/aider_envelope_benchmark.py` — envelope benchmark harness used for Finding 29
- `docs/phase-18/d-17-111/WP-04C_MODEL_EVALUATION_MATRIX_2026-05-04.md` — verifier model/prompt matrix used for Finding 33
- `config/ollama/Modelfile-qwen3-coder-30b-coding` — temp=0.1, num_ctx=32768 derivation
- `config/ollama/Modelfile-qwen3-coder-next-coding` — temp=0.15, num_ctx=32768 derivation
