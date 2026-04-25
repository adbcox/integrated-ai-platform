# Reference Code System

Curated code patterns injected as read-only context into aider calls.
Improves code quality by showing the model idiomatic Python patterns *before*
it writes code for a task.

## Why This Exists (and Why Not Full Repos)

The local `qwen2.5-coder:7b` model has a **32k token context window**. Before
this system, the executor was injecting `repo_context.txt` (229k chars =
~57k tokens) into every aider call — blowing the limit on every single run.

This system fixes that in two ways:

| What changed | Before | After |
|---|---|---|
| Repo context | 229k chars (~57k tokens) | 5k chars (~1.3k tokens) |
| Reference patterns | none | up to 20k chars (~5k tokens) |
| Total context budget used | **>100%** (truncated) | **~25%** (safe) |

**Why not clone TheAlgorithms/Python?** It's 4+ GB. A single pattern file
(200 lines) is ~500 tokens. The algorithms repo has 800+ files we'd never use.
The snippet library approach gives targeted context without overflow.

## What's Included

### Curated Patterns (`artifacts/reference/patterns/`)

| File | Pattern | Best for |
|---|---|---|
| `adapter_pattern.py` | Adapter | Wrapping APIs, hardware, legacy code |
| `observer_pattern.py` | Observer | Event streams, metrics, notifications |
| `pipeline_pattern.py` | Pipeline | ETL, RAG stages, processing chains |
| `repository_pattern.py` | Repository | Decoupling storage from logic |
| `factory_pattern.py` | Factory | Config-driven object creation |
| `service_layer_pattern.py` | Service | Business logic API/CLI separation |

Each file is 50-80 lines with a docstring explaining when to use it, plus a
runnable concrete example.

### Category → Pattern Mapping

The executor infers category from the task description and selects patterns:

```
MEDIA  → observer, pipeline, adapter
API    → repository, service_layer
DATA   → pipeline, repository
OPS    → observer, adapter
LEARN  → observer, pipeline
TEST   → factory
CORE   → adapter, factory
```

## Setup

```bash
# Verify snippets + mini context (fast, no network needed)
python3 bin/setup_references.py

# Also clone reference repos to ~/ai-reference/ for human browsing
python3 bin/setup_references.py --clone

# Show detailed context budget breakdown
python3 bin/setup_references.py --report
```

## How It Works in the Executor

1. `auto_execute_roadmap.py` calls `local_coding_task.py --batch-mode "Create new file domains/foo.py"`
2. `local_coding_task.py` routes to `domains/coding.py`
3. `_build_aider_command()` injects context in order:
   - `--read=artifacts/repo_context_mini.txt` (~1.3k tokens, architecture summary)
   - `--read=artifacts/reference/patterns/observer_pattern.py` (~500 tokens, if budget allows)
   - `--read=artifacts/reference/patterns/pipeline_pattern.py` (~500 tokens, if budget allows)
   - The target file(s)
   - `--message "Create new file..."` as the task

Budget is enforced: if adding a snippet would exceed 20k chars, it's skipped.
The system never blocks aider — if anything fails, it falls through silently.

## Adding Your Own Patterns

1. Create a `.py` file in `artifacts/reference/patterns/`
2. Keep it under 250 lines (~3k tokens)
3. Start with a docstring: what pattern, when to use it, project-specific notes
4. Add a runnable `if __name__ == "__main__"` example
5. Wire it into `CATEGORY_SNIPPETS` in `framework/reference_manager.py`

## Reference Repos (for Human Browsing)

These are cloned for learning and browsing, NOT injected into aider:

| Repo | Why |
|---|---|
| `python-patterns` (faif) | 50+ patterns, idiomatic Python, small (~5MB) |
| `fastapi-realworld` | Production FastAPI structure, middleware, deps |

Clone with `python3 bin/setup_references.py --clone`.

Do **not** add TheAlgorithms/Python (4GB), bulletproof-react (needs npm),
or any repo that requires build steps or exceeds ~20MB.
