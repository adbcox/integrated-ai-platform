# Aider default workflow (D-17-94)

Single-surface operator guide for LOCAL_AIDER coding tasks. When you
have a coding task, run `scripts/aider-task.sh`. This runbook covers
the decision tree, invocation patterns, failure modes, and how to feed
learning back into the router.

**Related:**
- `config/prompts/library/v1.0.0/CATALOG.md` — persona routing guide (D-17-90)
- `docs/runbooks/goose-operations.md` — Goose invocation (non-coding agentic tasks)
- `docs/phase-17/d-17-93/AUDIT_2026-05-04.md` — telemetry audit that motivated this runbook

---

## 1. Decision tree — which surface?

```
Does the task involve modifying one or more code files?
│
├── YES → Are there ≤ 6 files and the intent is narrowly defined?
│          │
│          ├── YES → scripts/aider-task.sh  (LOCAL_AIDER)
│          │
│          └── NO (complex multi-service refactor, > 6 files,
│               unclear scope) → Claude Code  (claude-local)
│
└── NO → Does the task require MCP tools (file read across repos,
          service registry, platform-state queries)?
           │
           ├── YES → Goose  (doc drafting C1b, multi-step queries)
           │          (C1a/verbatim-quote work: Claude Code only — see §5)
           │
           └── NO (question, architecture review, judgment call)
                └── Claude Code  (claude-local / claude-pro)
```

**Rule of thumb:** Aider for file edits. Goose for MCP-driven agentic
workflows. Claude Code for everything else.

---

## 2. Invocation

### Basic usage

```bash
# Minimal — description only (router infers task type)
scripts/aider-task.sh "Add a one-line docstring to the health_check function" \
  services/health.py

# Multi-file task
scripts/aider-task.sh "Extract DB retry logic into a helper" \
  domains/coding.py domains/learning.py

# Tag with task class (enables class-level learning analytics)
scripts/aider-task.sh --class C0 "Fix typo in error message" services/api.py
scripts/aider-task.sh --class C1 "Refactor rate-limiter across 3 files" \
  services/api.py services/auth.py services/proxy.py

# Force a heavier model for a hard task
scripts/aider-task.sh --hard "Rewrite async scheduler to use asyncio.Queue" \
  services/scheduler.py

# Override model explicitly
scripts/aider-task.sh --model devstral:latest "Port to async" services/sync.py

# Dry-run — print routing decision without executing Aider
scripts/aider-task.sh --dry-run "Any task" services/foo.py
```

### Task class taxonomy (D-17-90)

| Class | Label | Description | Default model |
|-------|-------|-------------|---------------|
| C0 | voice-fast | ≤ 1 file, ≤ 50 chars description, quick fix | qwen2.5-coder:14b |
| C1 | deliberate-analysis | Multi-file synthesis, runbook authoring | qwen3-coder:30b |
| C2 | code-review | Diff/code critique, review pass | qwen2.5-coder:7b |
| C3 | decomposition | Planning + subtask breakdown | qwen3-coder:30b |

When `--class` is not passed, the router infers from description keywords
and file count. Supply `--class` to get accurate learning-layer analytics.

### Model cascade (Mac Mini Ollama)

Priority order when `--model` and `--hard` are not set:

1. `qwen2.5-coder:14b` — default fast
2. `qwen2.5-coder:32b` — `--hard` flag or explicit `--model`
3. `qwen2.5-coder:7b` — fallback
4. `devstral:latest` — via `--model devstral:latest`

---

## 3. What the router does

`scripts/aider-task.sh` calls `domains/router.py TaskRouter.classify()`:

1. **Learning path:** if `domains/learning.py` has ≥ 1 "coding" history
   entry and confidence ≥ 0.60, routes to LOCAL_AIDER using the
   learned model recommendation.
2. **Keyword fallback:** research/architecture keywords → CLAUDE_CODE or
   CLAUDE_CHAT escalation. File count heuristics → LOCAL_AIDER with
   model selected by file count.

If the router recommends CLAUDE_CODE or CLAUDE_CHAT, the script exits 1
with a specific escalation message and the equivalent Claude Code
invocation. This is expected behavior — not an error in the tooling.

Every invocation is logged to `artifacts/aider_runs/router_events.jsonl`
regardless of outcome.

---

## 4. Failure modes and remediation

### F1 — Router escalates to CLAUDE_CODE

**Symptom:** Script prints `[aider-task] ESCALATION RECOMMENDED` and exits 1.

**Cause:** Task description contains architecture/research keywords, or
file count exceeds the keyword-based heuristic (>5 files), and the
learning layer either has no history or confidence < 0.60.

**Remediation:**
- For a genuinely complex task, follow the escalation recommendation —
  open `claude-local` and describe the task interactively.
- If the escalation is wrong (you know Aider can handle it), use
  `--model qwen2.5-coder:32b` to override the model selection and
  re-run. The routing decision is logged; if the task succeeds, the
  learning layer will build confidence for future auto-routing.

### F2 — Aider exits 0 but makes no file changes

**Symptom:** Aider completes, but `git diff` shows no changes.

**Cause:** Model produced a response that didn't match the SEARCH/REPLACE
block format Aider expects, or the task description was too vague.

**Remediation:**
- Re-run with a more specific description that names the exact function
  or line range.
- Try `--hard` to escalate to qwen2.5-coder:32b.
- If the file is large (> 300 lines), decompose the task — target a
  specific function rather than the whole file. Aider on 14b truncates
  whole-file responses on 40+ line files under load.

### F3 — Timeout (exit 124)

**Symptom:** Aider exits with code 124.

**Cause:** qwen2.5-coder:14b cold-load on Mac Mini takes 20–40s; a
tight timeout leaves insufficient generation budget.

**Remediation:**
- Re-run immediately (model is warm on second attempt).
- For consistently large tasks, use `--hard` (32b has higher throughput
  for complex outputs once loaded).
- Default timeout in `bin/aider_local.sh` is 360s (raised D-17-94).
  If this is still firing, investigate Ollama resource contention
  (`ollama ps` on Mac Mini).

### F4 — aider not on PATH

**Symptom:** `command not found: aider` or exit 127.

**Cause:** `~/.local/bin` not in PATH for this shell session.

**Remediation:**

```bash
export PATH="$HOME/.local/bin:$PATH"
# Verify:
aider --version  # should show v0.82.3 or later
```

Add the export to `~/.zshrc` if this recurs.

### F5 — Learning layer overrides expected escalation

**Symptom:** A > 5-file task routes to LOCAL_AIDER instead of CLAUDE_CODE.

**Cause:** The learning layer has sufficient history (confidence ≥ 0.60)
and recommends LOCAL_AIDER regardless of file count. This is intentional
design — learning wins over keywords when it has evidence.

**Remediation:** This is not an error. If you believe the task is
genuinely too complex for Aider, use `--model qwen2.5-coder:32b --hard`
or invoke Claude Code directly. The learning layer will adjust based
on outcome.

---

## 5. Bypass — when to skip aider-task.sh

Skip the wrapper and invoke `bin/aider_local.sh` directly only when:

- You need to pass raw Aider flags not exposed by the wrapper.
- You are debugging the Aider invocation itself (use `--dry-run` first).
- The task is part of an automated pipeline that manages its own
  router-events logging.

Direct invocation:

```bash
bin/aider_local.sh --message "Fix the health check retry" services/health.py
bin/aider_local.sh --hard --message "Refactor scheduler" services/scheduler.py
```

---

## 6. Capturing learning back into the router

The learning layer (`domains/learning.py`) records outcomes from Aider
runs automatically when triggered via the orchestrated coding pipeline
(`domains/coding.py`). The `aider-task.sh` wrapper logs *routing decisions*
to `router_events.jsonl` but does not yet record execution outcomes
(exit code, diff delta, wall time) back into the learning store.

To help the router improve:

1. After a successful Aider run on a task that previously escalated,
   note the task description and file count — these are signal that
   the learning confidence threshold could be lowered.
2. Run the learning audit periodically:

   ```bash
   python3 -c "
   from domains.learning import LearningDomain
   from pathlib import Path
   l = LearningDomain(Path('.'))
   print('Task types:', l.get_all_task_types())
   rec = l.recommend_model('coding', 'LOCAL_AIDER')
   print(f'Coding confidence: {rec.confidence:.2f} model={rec.model}')
   "
   ```

3. File the result as a note in the session's WP — this feeds the
   long-horizon learning analytics backlog.

---

## 7. D-17-90 prompt library integration

Aider tasks can use the persona templates from `config/prompts/library/`
as Aider system prompts. Relevant personas:

| Persona file | Task class | Use with Aider |
|---|---|---|
| `01-voice-fast.md` | C0 | Low-friction, single-file edits — default path |
| `02-deliberate-analysis.md` | C1 | Multi-source synthesis; frontier review still required |
| `03-code-review.md` | C2 | Review pass on a diff before committing |
| `04-decomposition.md` | C3 | Break a task into subtasks before dispatching each |

To inject a persona as an Aider system prompt:

```bash
bin/aider_local.sh \
  --system "$(cat config/prompts/library/v1.0.0/02-deliberate-analysis.md)" \
  --message "Refactor the retry logic" services/retry.py
```

Note: `scripts/aider-task.sh` does not currently inject personas
automatically. Manual `--system` injection via `bin/aider_local.sh`
is the current pattern. Auto-injection is a follow-on deliverable.

---

## 8. Telemetry

Router decisions are logged to:

```
artifacts/aider_runs/router_events.jsonl
```

Each entry contains: `router_run_id`, `task_name`, `task_class`,
`executor`, `routed_model`, `confidence`, `reasoning`, `files`,
`timestamp`, `dry_run`.

To review recent routing decisions:

```bash
tail -5 artifacts/aider_runs/router_events.jsonl | python3 -m json.tool
```

To count routing by executor:

```bash
python3 -c "
import json
from pathlib import Path
lines = Path('artifacts/aider_runs/router_events.jsonl').read_text().strip().split('\n')
from collections import Counter
c = Counter(json.loads(l)['executor'] for l in lines if l)
for k,v in c.most_common(): print(f'{k}: {v}')
"
```
