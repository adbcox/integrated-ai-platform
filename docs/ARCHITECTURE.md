# System Architecture: Integrated AI Platform

## High-Level System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    INTEGRATED AI PLATFORM                        │
│                                                                   │
│  ┌─────────────────┐         ┌──────────────────┐               │
│  │  Roadmap Items  │         │  Autonomous      │               │
│  │  (YAML + MD)    │────────→│  Executor        │               │
│  │  194 items      │         │  (auto_execute)  │               │
│  │  54 complete    │         │                  │               │
│  └─────────────────┘         └────────┬─────────┘               │
│                                       │                          │
│                                       ▼                          │
│                          ┌──────────────────────┐               │
│                          │ Task Decomposition   │               │
│                          │ (stage_rag pipeline) │               │
│                          └──────────┬───────────┘               │
│                                     │                           │
│                    ┌────────────────┼────────────────┐          │
│                    │                │                │          │
│                    ▼                ▼                ▼          │
│        ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐  │
│        │ Local Ollama    │ │ GitHub API   │ │ Git Commit   │  │
│        │ qwen2.5-coder   │ │ + Aider      │ │ Status Track │  │
│        │ (code gen)      │ │ (execution)  │ │ (versioning) │  │
│        └─────────────────┘ └──────────────┘ └──────────────┘  │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              Framework Runtime Layer                       │ │
│  │  • WorkerPool & Job Scheduling                            │ │
│  │  • Code Executor Abstraction (ClaudeCode, Aider)         │ │
│  │  • State Store & Artifact Management                      │ │
│  │  • Permission Engine & Safety Gates                       │ │
│  │  • Learning Hooks & Attribution                          │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Roadmap Management (`bin/roadmap_parser.py`)

**Purpose:** Parse, validate, and track roadmap items across their lifecycle.

**Key Functions:**
- `parse_roadmap_directory()` — Reads all YAML files, parses metadata, builds dependency graph
- `infer_dependencies()` — Extracts dependency relationships between items
- `detect_cycles()` — Identifies circular dependencies that block execution
- `update_frontmatter()` — Updates item status in version control (git commits)

**Data Structure:**
```python
RoadmapItem:
  - Metadata: id, title, category, type, status, priority
  - Governance: priority_class, queue_rank, target_horizon, LOE
  - Scoring: strategic_value, architecture_fit, execution_risk
  - Tracking: readiness, dependencies, execution status
  - Files: file_path, markdown_content, frontmatter
```

**Dependencies:** YAML parsing, git integration, markdown extraction

---

### Autonomous Executor (`bin/auto_execute_roadmap.py`)

**Purpose:** Run indefinitely, finding executable items, decomposing them, and executing subtasks.

**Execution Loop:**
```
1. Load all roadmap items from YAML
2. Detect and reject any cycles
3. Find executable items (status=Accepted/Planned, readiness=now/near, deps met)
4. Sort by priority (P0 → P4, then queue_rank)
5. For each item:
   a. Decompose into subtasks (using stage_rag pipeline or fallback)
   b. Execute each subtask (aider subprocess with timeout)
   c. Retry on failure (3 attempts, exponential backoff)
   d. Update status in git on completion/failure
6. Stop after target_completions or on consecutive failures
```

**Key Features:**
- **Priority Sorting:** P0 items always execute before P4
- **Dependency Enforcement:** Items with unmet dependencies are skipped
- **Retry Logic:** 3 attempts per subtask (5s, 5s, 10s delays)
- **Timeout Protection:** SIGKILL after 600s (configurable), proc.wait() timeout guards
- **Output Flushing:** All debug output includes `flush=True` to prevent buffering on hang
- **Failure Tracking:** JSONL log in `artifacts/execution_failures.jsonl`
- **Filter Support:** `--filter "RM-DEV"` executes only matching items
- **Dry-Run Mode:** `--dry-run` shows what would execute without git commits

**Exit Conditions:**
- Reached `target_completions` (success)
- 3 consecutive item failures (graceful stop)
- 10 consecutive filter mismatches without progress (prevent infinite loop)
- No more executable items (graceful exit)

---

### Task Decomposition (`bin/stage_rag*.py`)

**Purpose:** Convert a single high-level roadmap item into executable subtasks with file targets.

**Two-Stage Pipeline:**

1. **API-First (If Available):**
   - Send item description + requirements to local Ollama
   - Receive structured JSON list of subtasks
   - Filter subtasks to only those targeting .py files (no docs edits)

2. **Fallback (If API Unavailable):**
   - Use `expected_file_families` from item metadata
   - Generate subtasks directly from file paths
   - Example: "Add function to domains/coding.py" → subtask

**Entity-Aware Reranking (`stage_rag4.py`):**
- Extracts CamelCase entities from queries (ExecutorFactory, RoadmapItem)
- Boosts retrieval scores for files that *define* those entities
- Penalizes docs files for code-intent queries
- Result: 28.5 percentage point improvement in context selection

---

### Code Execution Layer (`framework/code_executor.py`, `domains/coding.py`)

**Purpose:** Execute a single subtask by invoking local Ollama or aider.

**ExecutorFactory Pattern:**
```python
executor = ExecutorFactory.get_executor(task)
success = executor.execute(task_description, file_paths)
```

**Two Executor Types:**

1. **ClaudeCodeExecutor** (Primary)
   - Routes through Claude API if available
   - Falls back to local Ollama via Aider

2. **AiderExecutor** (Fallback)
   - Direct invocation of aider CLI
   - Subprocess management with timeout
   - Real-time output capture

**Execution Flow:**
```
Input: "Add authentication to domains/auth.py"
  ↓
Aider subprocess: aider --auto --model qwen2.5-coder:14b domains/auth.py
  ↓
Local LLM generates code modifications
  ↓
Aider writes changes to file
  ↓
Git detects modified files
  ↓
Executor captures subprocess output (stdout, stderr, returncode)
  ↓
Success if returncode == 0
  ↓
On success: Stage next subtask
On failure: Retry or log failure
```

**Subprocess Safety:**
- Timeout: 600 seconds (default, configurable)
- Process group management: Kill entire group on timeout (os.killpg)
- Timeout protection: proc.wait(timeout=5) prevents indefinite blocking
- Retry backoff: 5s, 5s, 10s between attempts

---

### Job Scheduling & State Management (`framework/job_schema.py`, `framework/state_store.py`)

**Purpose:** Track execution state and lifecycle of items and subtasks.

**JobLifecycle:**
```
Proposed → Accepted → Planned → Execution-ready → In progress → Validating → Completed
                    ↓
                  Frozen (blocked)
                    ↓
                  Deferred (low priority)
```

**ValidationRequirement:**
- Custom tests per item (if any)
- Artifact preservation rules
- Escalation criteria

**State Store:**
- Persists execution records to `artifacts/`
- Tracks completion status per item
- Stores failure logs (JSONL format)
- Maintains git commit references

---

### Permission Engine & Safety (`framework/permission_engine.py`)

**Purpose:** Guard against unsafe operations.

**Safety Gates:**
- File modification whitelist (allow .py, .md, .yaml; reject .git, secrets)
- Subprocess timeout enforcement
- Git command validation (no force-push)
- Artifact access restrictions

---

### Learning & Attribution (`framework/learning_hooks.py`)

**Purpose:** Record what worked and what failed for continuous improvement.

**Attribution Data:**
- Which model generated successful code
- Which executor type worked best
- Which tasks took longest
- Which failure patterns emerge

**Learning Signals:**
- Semantic success rate (code compiles and runs)
- Actual test pass rate (if tests exist)
- Iteration count (how many retries needed)
- Execution time per task type

---

## Data Flow: From Roadmap to Git

### 1. Item Selection
```
parse_roadmap_directory()
  ↓
Load 194 items from YAML
  ↓
Filter by status (Accepted/Planned only)
  ↓
Filter by readiness (now/near only, skip "blocked")
  ↓
Check dependencies (skip if any dependency not Completed)
  ↓
Sort by priority_class, queue_rank, id
  ↓
Return top N candidates
```

### 2. Decomposition
```
Item: "RM-DEV-001: Add hot reload"
  ↓
stage_rag pipeline extracts requirements
  ↓
Local Ollama generates subtasks:
  - "Add file watcher to domains/dev.py"
  - "Create reload trigger in bin/hot_reload.py"
  - "Test reload with sample file"
  ↓
Filter to subtasks with .py file targets
  ↓
Return list of subtasks
```

### 3. Execution
```
Subtask: "Add file watcher to domains/dev.py"
  ↓
Execute via aider:
  subprocess.Popen([
    "python3", "bin/local_coding_task.py",
    "--force-local", "--batch-mode",
    "Add file watcher to domains/dev.py"
  ])
  ↓
Wait for completion (timeout=600s)
  ↓
On timeout: SIGKILL process, retry (up to 3 times)
  ↓
On success: Capture stdout/stderr, return True
  ↓
On failure: Log to execution_failures.jsonl, return False
```

### 4. Status Tracking
```
All subtasks succeeded:
  ↓
Update item status in YAML file
  ↓
Git add item file
  ↓
Git commit: "status: RM-DEV-001 → Completed"
  ↓
Push (if remote configured)
  ↓
Move to next item

Any subtask failed:
  ↓
Log to artifacts/execution_failures.jsonl
  ↓
Update item status to "In progress" (partially done)
  ↓
Git commit: "status: RM-DEV-001 → In progress"
  ↓
Retry same item next loop (max 3 consecutive failures)
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Code Generation** | Ollama + qwen2.5-coder:14b | Local-first LLM inference |
| **Code Execution** | Aider | Interactive code editing with LLM |
| **Orchestration** | Python 3.9+ subprocess | Job management, process control |
| **Version Control** | Git + GitHub | Item tracking, commit history, collaboration |
| **Configuration** | YAML + Markdown | Item definitions, human-readable format |
| **Logging** | JSONL + plain text | Structured failure logs, execution transcripts |
| **Testing** | pytest + unittest.mock | Unit & integration test validation |
| **State Management** | File-based artifacts | Persistent job state and learning data |

---

## Key Design Decisions & Rationale

### Decision 1: Local-First Execution (Ollama)

**Why:** Eliminates cloud dependency, enables offline work, reduces latency.

**Trade-off:** Smaller model size (14B) vs. larger remote models (but still effective for bounded tasks).

**Validation:** 88.9% semantic-primary success rate on 18-task benchmark.

---

### Decision 2: Aider for Code Modification

**Why:** Direct file interaction, error recovery, iterative improvement.

**Trade-off:** Requires local environment setup vs. cloud-only convenience.

**Validation:** 100% total success (primary + fallback) on 24-task benchmark.

---

### Decision 3: Autonomous Item Selection

**Why:** No manual queue management, continuous progress, respects dependencies.

**Trade-off:** Requires robust priority system and cycle detection.

**Validation:** 54 items completed autonomously, no deadlocks in 194-item set.

---

### Decision 4: Git-Based Status Tracking

**Why:** Immutable history, single source of truth, audit trail.

**Trade-off:** Overhead of git commits per item (acceptable for 194-item scale).

**Validation:** `git log` shows 54 status commits, 100% reliable tracking.

---

### Decision 5: YAML + Markdown Hybrid Format

**Why:** Structured metadata (YAML) + human-readable docs (Markdown).

**Trade-off:** Two formats to maintain (but clear separation).

**Validation:** Parser handles both, ~100% parse success rate.

---

## Failure Modes & Recovery

| Failure | Root Cause | Recovery |
|---------|-----------|----------|
| **Silent startup crash** | Exception in parse_roadmap_directory() before first print | Add [STARTUP] print with flush=True at entry point |
| **Buffered output on hang** | Missing flush=True in debug statements | Add flush=True to all prints before code that might hang |
| **Infinite loop on filter** | Reload returns same unmatched item repeatedly | Add skipped_without_match counter, break after 10 attempts |
| **proc.wait() hangs** | No timeout on wait() after SIGKILL | Add proc.wait(timeout=5) with exception handler |
| **Cycle in dependencies** | Item A depends on B, B depends on A | detect_cycles() in startup, reject cycles before execution |
| **Missing dependency** | Item tries to execute but dep not Completed | find_executable_items() checks _dependencies_met() |
| **Subtask without file** | Decomposition generates task with no target file | Filter subtasks, require .py file in task description |

---

## Performance Characteristics

- **Item Startup:** ~2s (parse + dependency check)
- **Decomposition:** ~5s (API call or fallback)
- **Subtask Execution:** ~30-60s (aider + LLM)
- **Retry Overhead:** 3 attempts × (5 + 5 + 10)s = 20s per failed subtask
- **Status Commit:** ~1s (git add + commit)
- **Overall Throughput:** ~1-2 items/hour (varies by complexity)

---

## Monitoring & Observability

### Real-Time Monitoring
- `execution.log` — [DEBUG] markers, [STARTUP] diagnostics, progress updates
- `tail -f execution.log` — Live execution transcript

### Post-Execution Analysis
- `git log --oneline | grep "status:"` — Completed items
- `artifacts/execution_failures.jsonl` — Failures with duration, attempt count
- `artifacts/stage_rag4/usage.jsonl` — Retrieval ranking decisions

### Health Checks
```bash
make test-offline          # Deterministic validation
make micro-lane-regression # Executor integrity checks
python3 -m pytest tests/test_autonomous_executor.py -v  # Unit tests (19 tests)
```

---

## Future Improvements (Roadmap)

- **RM-MON-001-010:** System health dashboard, real-time metrics, SLA tracking
- **RM-DEPLOY-001-010:** Blue/green deployment, canary releases, feature flags
- **RM-CI-001-010:** GitHub Actions optimization, multi-stage builds, security scanning
- **Semantic-to-Code Bridging:** Move from 88.9% semantic to 100% real code generation
- **Generalization:** Expand from 24-task benchmark to 100+ diverse real-world tasks

---

**Last Updated:** 2026-04-24
**Version:** 1.0
