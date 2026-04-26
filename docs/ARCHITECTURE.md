# Architecture: Integrated AI Platform

> **Quick Start:** See [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md) for high-level system summary.

**System Version:** Post-convergence local-first execution  
**Last Updated:** 2026-04-24  
**Primary Goal:** Autonomous code generation and infrastructure task execution via local LLM

---

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     ROADMAP & ORCHESTRATION LAYER                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Roadmap Items (RM-*.md)  ──> Parse & Infer Dependencies           │
│  (253 total, 59 completed)       ↓                                  │
│                            Detect Cycles (0 remaining)             │
│                                 ↓                                   │
│                          Auto Executor Loop                         │
│                    (auto_execute_roadmap.py)                        │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      PLANNING & CONTEXT LAYER                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Stage RAG4 (Entity-Aware Reranking)                                │
│  ├─ Extract entities (CamelCase identifiers)                        │
│  ├─ BM25 token matching on codebase files                          │
│  └─ Entity definition scoring (boost "class X" definitions)        │
│                                                                       │
│  Stage RAG6 (Multi-Target Orchestration Planning)                  │
│  ├─ Select multiple target files for modification                  │
│  ├─ Order modifications by dependency and impact                   │
│  └─ Generate execution plan                                         │
│                                                                       │
│  Decomposition (task_decomposer.py)                                │
│  ├─ Break roadmap item into subtasks                               │
│  ├─ Use local LLM (qwen2.5-coder:14b)                             │
│  └─ Return list of concrete implementation steps                   │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     EXECUTION & CODE GENERATION                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Executor Abstraction (code_executor.py)                           │
│  ├─ ClaudeCodeExecutor (primary)                                   │
│  └─ AiderExecutor (fallback for complex edits)                     │
│                                                                       │
│  Aider Integration (local-first code generation)                   │
│  ├─ Local Ollama backend (http://127.0.0.1:11434)                 │
│  ├─ Model: qwen2.5-coder:14b (default, ~14B params)              │
│  ├─ Model: deepseek-coder-v2 (fallback, harder tasks)            │
│  └─ Subprocess isolation (clean git state between runs)           │
│                                                                       │
│  Inference Adapter (inference_adapter.py)                          │
│  ├─ Abstract backend (local vs remote)                             │
│  ├─ Token counting and rate limiting                               │
│  ├─ Retry logic with exponential backoff                           │
│  └─ Fallback to deterministic mode on timeout                      │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   VALIDATION & GIT INTEGRATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Verification (validate.py)                                         │
│  ├─ Python syntax check (ast.parse)                                │
│  ├─ Shell syntax check (shellcheck)                                │
│  ├─ Test suite execution (pytest)                                  │
│  └─ Git diff review (reject unsafe changes)                        │
│                                                                       │
│  Git Commit & Status Update                                         │
│  ├─ Mark roadmap item as "Completed"                               │
│  ├─ Commit code changes                                             │
│  ├─ Update roadmap markdown with status                            │
│  └─ Push to origin/main                                             │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────┐
│                   MONITORING & STATE PERSISTENCE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  State Store (state_store.py)                                       │
│  ├─ Artifact caching (retrieved context)                           │
│  ├─ Plan history (stage6 orchestration output)                     │
│  ├─ Execution logs (detailed task traces)                          │
│  └─ Escalation index (failures and errors)                         │
│                                                                       │
│  Metrics & Learning (learning_hooks.py)                            │
│  ├─ Attribution: Which components contributed to success           │
│  ├─ Outcome tracking: Semantic vs deterministic success            │
│  ├─ Signal generation: Identify weak points                        │
│  └─ Policy recommendations: Next improvements                      │
│                                                                       │
│  Artifacts Directory Structure                                      │
│  ├─ artifacts/stage_rag4/: Retrieval decisions & rankings          │
│  ├─ artifacts/stage6_manager/: Orchestration plans                │
│  ├─ artifacts/escalations/: Failures and issues                    │
│  └─ artifacts/aider_bench/: Local LLM performance metrics         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Flow: End-to-End Execution

```
Step 1: LOAD ROADMAP
  ├─ Read docs/roadmap/ITEMS/*.md (glob: RM-*.md only)
  ├─ Parse metadata: status, dependencies, priority
  ├─ Infer dependencies from description references
  ├─ Detect cycles (should be 0)
  └─ Load 253 items into memory

Step 2: SELECT NEXT ITEM
  ├─ Filter by status (Accepted items go into queue)
  ├─ Sort by priority, strategic value, queue rank
  ├─ Check dependencies (all must be Completed)
  └─ Select item with lowest queue rank

Step 3: RETRIEVE CONTEXT (Stage RAG4 + RAG6)
  ├─ Extract entities from item title/description
  │   └─ CamelCase: "ExecutorFactory" → boost files defining ExecutorFactory
  ├─ Search codebase for related files
  │   └─ BM25 token matching + entity definition scoring
  ├─ Select top 4-6 most relevant target files
  │   └─ Remove docs files for code-intent queries
  └─ Aggregate code context for LLM

Step 4: DECOMPOSE INTO SUBTASKS
  ├─ Call local LLM (qwen2.5-coder:14b via Ollama)
  ├─ Prompt: "Break this task into concrete implementation steps"
  ├─ Parse response into 3-5 subtasks
  │   ├─ "Create tests/api_contracts.py with contract definitions"
  │   ├─ "Update framework/http_client.py to include validation"
  │   └─ "Modify domains/service_a.py to adhere to contracts"
  └─ Store subtasks for execution

Step 5: EXECUTE SUBTASK (via Aider)
  ├─ For each subtask (dual-model workflow):
  │   ├─ Phase 1 (writer): aider + qwen2.5-coder:7b generates code (~217s)
  │   ├─ Phase 2 (reviewer): aider + qwen2.5-coder:32b reviews changes (~200s)
  │   ├─ Accept or auto-fix based on review severity
  │   └─ Retry up to 3 times on failure
  │
  └─ Subprocess isolation:
      ├─ Clean git state before execution
      ├─ start_new_session=True (process group isolation)
      └─ Timeout: 600 seconds per subtask

Step 6: VERIFY & VALIDATE
  ├─ Syntax checks:
  │   ├─ Python: ast.parse on all .py files
  │   └─ Shell: shellcheck on all .sh files
  ├─ Run test suite:
  │   ├─ pytest tests/test_autonomous_executor.py
  │   └─ make test-offline (7 offline scenarios)
  ├─ Review git diff:
  │   ├─ Reject if unsafe patterns detected
  │   └─ Accept if all validations pass
  └─ Return: Pass/Fail for this item

Step 7: UPDATE STATUS & COMMIT
  ├─ On success:
  │   ├─ Mark roadmap item status: "Completed"
  │   ├─ Record completion timestamp
  │   ├─ Git add + commit all changes
  │   ├─ Push to origin/main
  │   └─ Log metrics: time, subtask count, success/failure
  │
  └─ On failure (after retries):
      ├─ Log error details to escalations/index.jsonl
      ├─ Skip to next item (don't update status)
      ├─ Generate learning signal (what went wrong)
      └─ Continue loop

Step 8: REPEAT
  ├─ Loop back to Step 2
  ├─ Continue until:
  │   ├─ Target completions reached (--target-completions N)
  │   ├─ All items completed
  │   └─ Unrecoverable error occurs
  └─ Output summary metrics
```

---

## Technology Stack

### Infrastructure

- **Language:** Python 3.9
- **Runtime:** Subprocess isolation, tmux session management
- **VCS:** Git, GitHub
- **File Format:** Markdown (roadmap), JSON (artifacts, metrics)

### Local Code Generation

- **Backend:** Ollama (http://127.0.0.1:11434)
- **Decomposition Model:** qwen2.5-coder:14b — breaks roadmap item into subtasks (~140s/call)
- **Writer Model:** qwen2.5-coder:7b — generates code changes per subtask (~217s/call)
- **Reviewer Model:** qwen2.5-coder:32b — reviews writer output for bugs (~200s/call)
- **Available Models (measured):**
  - 7b: 4.7GB, ~217s per Ollama API call
  - 14b: 9.0GB, ~140s per Ollama API call
  - 32b: 19.9GB, ~200s per Ollama API call (estimated)
  - deepseek-coder-v2: 8.9GB (balanced pair reviewer)
- **Integration:** aider (CLI wrapper around Ollama)
  - Code-aware chat interface
  - Automatic file modification parsing
  - Syntax validation

### Testing & Validation

- **Python syntax:** ast.parse (built-in)
- **Shell syntax:** shellcheck (external tool)
- **Unit/Integration:** pytest
- **Regression:** 7 offline deterministic scenarios (no external APIs)

### Orchestration & Planning

- **RAG (Retrieval-Augmented Generation):**
  - Stage 4: Entity-aware reranking (BM25 + entity definition scoring)
  - Stage 6: Multi-target orchestration (select 4-6 files, order modifications)
- **Task Decomposition:** LLM planning (qwen2.5-coder:14b)
- **Dependency Resolution:** Topological sort + cycle detection

---

## Key Design Decisions

### 1. Why Markdown Roadmap?

**Decision:** Store roadmap as `RM-*.md` files in `docs/roadmap/ITEMS/`

**Why:**
- Human-readable source of truth
- Git history tracks changes to status, priorities, dependencies
- Easy to manually adjust without breaking parsing
- Portable: works offline, no database required
- Supports both explicit Dependencies sections and inferred references in descriptions

**Trade-offs:**
- Parsing is simple but requires careful regex
- No schema validation (must trust human input)
- File-per-item creates large directory (223 files)

### 2. Why Dual-Model Approach?

**Decision:** Default pair is 7b writer + 32b reviewer; decomposition uses 14b

**Why:**
- **Writer (7b):** Fast iteration — 217s per call, handles most code generation tasks
- **Reviewer (32b):** Catches bugs the 7b writer introduces; prevents bad commits
- **Decomposer (14b):** Balanced speed/quality for planning (~140s per decomposition)
- **Cost:** Local execution, zero API costs, no data leaves the machine

**Trade-offs:**
- Dual-model means 2× LLM calls per subtask (~420s vs ~217s for single-model)
- 32b reviewer requires 19.9GB RAM — may swap on machines with <32GB
- If reviewer is not available, falls back to single-model (writer only)

### 3. Why Subprocess Isolation?

**Decision:** Each aider invocation runs in a subprocess with `start_new_session=True`

**Why:**
- **Crash isolation:** LLM failure doesn't crash main executor
- **Git state:** Clean slate for each subtask (no accumulated git state)
- **Resource limits:** Can timeout without hanging parent process
- **Logging:** Separate stdout/stderr streams per subtask

**Trade-offs:**
- Process startup overhead (~1-2s per subtask)
- Can't share Python state between subtasks
- Requires git checkout between runs

### 4. Why Circular Dependency Breaking?

**Decision:** Remove weakest links in dependency cycles (heuristic: item with most other dependencies)

**Why:**
- Prevents topological sort failures
- Identifies which dependencies are actually critical
- Removes "nice-to-have" edges in the dependency graph
- Allows executor to make progress on cyclic families

**Trade-offs:**
- May remove some meaningful dependencies
- Strategy is heuristic (not optimal)
- Requires manual review of removed edges

### 5. Why Stage RAG4 Entity-Aware Reranking?

**Decision:** Boost files that *define* entities mentioned in the query, not just mention them

**Why:**
- BM25 alone ranks files that mention "ExecutorFactory" higher than files that define it
- Entity definition scoring (regex: "class ExecutorFactory") fixes retrieval accuracy
- Improves bounded task coverage by 28.5 percentage points
- Reduces context bloat by filtering to actual implementations

**Trade-offs:**
- Requires parsing entity names from queries (CamelCase extraction)
- Regex pattern matching can miss some definitions
- Needs periodic revalidation as codebase evolves

---

## Execution Modes

### Dry-Run Mode (`--dry-run`)

```bash
python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run
```

- **Still calls Ollama** for decomposition (~140s with 14b model)
- Skips aider execution (subtasks print `[DRY]` and return immediately)
- **Does NOT commit** changes to git
- **Does NOT update** roadmap status
- Requires Ollama running — not safe to run when Ollama is down
- Use `--max-items 0` to skip everything including decomposition

### Real Mode (no `--dry-run`)

```bash
python3 bin/auto_execute_roadmap.py --target-completions 5
```

- Full execution: decompose → execute → validate → commit
- Updates roadmap item status to "Completed"
- Commits changes to git
- Pushes to origin/main
- Updates execution metrics

### Resume Mode (`--resume`)

```bash
python3 bin/auto_execute_roadmap.py --resume --target-completions 10
```

- Reads state from last execution
- Continues from where it left off
- Skips already-completed items
- Useful for recovering from crashes

---

## Failure Handling

### Graceful Degradation

1. **Semantic Generation Fails:** Fall back to deterministic mode
   - Return safe, syntactically-valid boilerplate
   - Avoids crash, allows executor to continue

2. **Subtask Fails:** Retry up to 3 times
   - Different seed/temperature on each retry
   - Log to escalation index after 3 failures
   - Skip to next item

3. **Validation Fails:** Reject changes, mark escalation
   - Syntax error: Don't commit
   - Test failure: Don't commit
   - Unsafe patterns: Don't commit
   - Log for manual review

4. **LLM Timeout:** Use fallback strategy
   - Increase timeout
   - Switch to larger model
   - Return deterministic template on final timeout

### Failure Log (`artifacts/execution_failures.jsonl`)

```json
{
  "timestamp": "2026-04-24T15:09:10.335021",
  "item_id": "RM-DOCS-001",
  "subtask": "Create docs/sdk/guides/media_integration.md ...",
  "attempt": 1,
  "error": "timeout after 600s",
  "duration_seconds": 600.01
}
```

---

## Performance Characteristics

### Typical Execution Timeline (per item)

| Phase | Time | Notes |
|-------|------|-------|
| Load roadmap | 2-3s | Parse 223 items, infer dependencies |
| Select next | <1s | Check prerequisites, sort |
| Stage RAG4 | 5-10s | Search codebase, rank files |
| Decompose | 10-30s | LLM planning via Ollama |
| Execute (per subtask) | 420-420s | writer(~217s) + reviewer(~200s) per subtask |
| Validate | 10-30s | Syntax check, test suite |
| Commit & update | 5-10s | Git operations |
| **Total per item** | **15-45 min** | 1-3 subtasks × ~7min each |

### Throughput

- **Simple items (1 subtask):** ~14 min (decompose 140s + write 217s + review 200s)
- **Medium items (2-3 subtasks):** 25-45 min each
- **Complex items (3+ subtasks with retries):** 45-120+ min each
- **Average:** ~30-45 min per item
- **Daily throughput:** 8-15 items/day (24h execution)

### Resource Usage

- **CPU:** 2-4 cores (qwen2.5-coder:14b inference)
- **Memory:** 14-20 GB (model weight loading)
- **Disk:** 50-100 MB per execution (artifacts)
- **Network:** None (local Ollama)

---

## State Persistence & Artifacts

### Roadmap State

```
docs/roadmap/ITEMS/RM-*.md
├─ Status: Accepted | In progress | Completed | Blocked
├─ Dependencies: [RM-ID, RM-ID, ...]
├─ Metrics: Priority, queue_rank, strategic_value, LOE
└─ Expected files & implementation notes
```

### Execution Artifacts

```
artifacts/
├─ stage_rag4/usage.jsonl          # Retrieval decisions (entity reranking)
├─ stage_rag6/                     # Stage 6 orchestration plans
├─ stage3_manager/                 # Stage 3 execution plans
├─ aider_runs/                     # Per-run aider output and metrics
├─ execution_failures.jsonl        # Failed subtask log (timeouts, errors)
└─ execution.log (repo root)       # Live executor output
```

### Git History

```bash
git log --oneline | head -20
# Each commit:
# - Updates roadmap item status
# - Includes code changes
# - References RM-ID in message
# - Commit author: Adrian Cox <adbcox@gmail.com>
```

---

## Safety & Governance

### Permission Gates

- No destructive git operations without manual confirmation
- Shell commands sandboxed (no system-level changes)
- File writes limited to project directory
- API calls logged and rate-limited

### Validation Requirements

All commits require:
1. ✓ Python syntax (ast.parse)
2. ✓ Shell syntax (shellcheck)
3. ✓ Test suite pass (pytest)
4. ✓ Git diff review (reject unsafe patterns)
5. ✓ No uncommitted dependencies

### Bounded Execution

- `--target-completions N`: Stop after N items
- `--dry-run`: No git commits
- `--max-items 0`: Just validate, don't execute
- Outer timeout: 600s per subtask (`subtask_timeout` in execute_subtask)
- Inner timeout: 900s for the aider call inside local_coding_task.py (but never reached if outer fires first)
- Dual-model typical runtime: writer ~217s + reviewer ~224s = ~441s total — fits within 600s outer limit

---

## Integration Points

### Local Aider Entry

```bash
make aider-fast       # qwen2.5-coder:14b
make aider-hard       # deepseek-coder-v2
make aider-smart      # 32B model via OLLAMA_API_BASE_32B
```

### Remote Codex Integration

```bash
python3 bin/codex51_benchmark.py  # Benchmark against Claude
```

### Monitoring & Observability

```bash
# Real-time executor logs
tail -f execution.log

# Tmux session
tmux attach -t roadmap
tmux capture-pane -t roadmap -p

# Real-time web dashboard (standalone, no backend)
open web/monitor/dashboard.html  # polls execution.log every 10s

# Failed subtask log
tail -20 artifacts/execution_failures.jsonl | python3 -m json.tool
```

---

## Future Improvements (Planned)

- [ ] Multi-item orchestration (Stage 7): Break down items for concurrent execution
- [ ] Learning loop: Attribution + strategy updates based on success/failure patterns
- [x] Real-time monitoring dashboard: `web/monitor/dashboard.html` (polls execution.log every 10s)
- [ ] Automated code review: Claude review integration before commit
- [ ] Expanded model routing: Per-category model selection (easier tasks → faster model)
- [ ] Semantic caching: Retrieve and reuse previous successful solutions
