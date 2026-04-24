# Autonomous Roadmap Execution System

Complete guide to the three-tier autonomous AI coding platform.

## Overview

The integrated AI platform now includes:

1. **Conversation State Management** — Persistent task history with keyword-based continuation
2. **Dual-Model Coding Workflow** — Writer model + reviewer model with intelligent auto-fix
3. **Autonomous Roadmap Execution** — Parse roadmap items, decompose to subtasks, execute autonomously

## 1. Conversation State Management

### Files
- `bin/quick_task.sh` — Main task runner with state persistence
- `/tmp/task_history.json` — Conversation history (last 3 tasks)

### Usage

```bash
# Simple task execution
./bin/quick_task.sh 'Add docstring to main function' file.py

# Resume previous context
./bin/quick_task.sh 'continue with error handling'

# Re-run on same files
./bin/quick_task.sh 'fix that'

# Extend context with previous files
./bin/quick_task.sh 'also add type hints'
```

### Keywords
- **continue** — Resume on previous files
- **fix that** — Re-run on same files with different task
- **also** — Extend context with previous files + new files

### How It Works
1. On each execution, stores: description, files, commit hashes
2. Keeps last 3 tasks in JSON format
3. Detects keywords and auto-includes previous files
4. Auto-commits dirty working tree before each task

---

## 2. Dual-Model Coding Workflow

### Files
- `config/model_pairs.yaml` — Model pair definitions
- `domains/coding.py` — CodingDomain with dual-model execution
- `bin/review_commit.py` — Standalone commit reviewer
- `bin/local_coding_task.py` — Updated with --dual-model flag

### Model Pairs

```yaml
fast_accurate:
  writer: qwen2.5-coder:7b       # Fast, 7B model
  reviewer: qwen2.5-coder:32b    # Thorough, 32B model
  use_for: [simple, medium]

balanced:
  writer: qwen2.5-coder:14b      # Balanced, 14B model
  reviewer: deepseek-coder-v2    # Cross-validator
  use_for: [medium, complex]

thorough:
  writer: qwen2.5-coder:32b      # Large, thorough writer
  reviewer: qwen2.5-coder:32b    # Large reviewer
  use_for: [complex, critical]
```

### Workflow

1. **Write Phase** — Writer model generates code
2. **Review Phase** — Reviewer model analyzes for issues
3. **Decide Phase** — Auto-fix based on severity:
   - **Low** → Auto-fix
   - **Medium** → Ask user
   - **High** → Escalate

### Usage

```bash
# Execute with dual-model (default)
./bin/quick_task.sh 'Add docstring to main function' file.py

# Single-model mode (no review)
./bin/quick_task.sh --single-model 'Fast execution'

# Local task with explicit flags
./bin/local_coding_task.py 'Add error handling' handler.py --dual-model --model qwen2.5-coder:32b

# Review a specific commit
./bin/review_commit.py abc123 --model qwen2.5-coder:32b
```

### Review Output

```json
{
  "issues": [
    {
      "severity": "medium",
      "category": "missing error handling",
      "description": "Handle database connection timeout"
    }
  ],
  "summary": "Good logic, missing edge case handling",
  "overall_quality": "good"
}
```

---

## 3. Autonomous Roadmap Execution

### Files
- `bin/roadmap_parser.py` — Parse markdown roadmap files
- `bin/auto_execute_roadmap.py` — Autonomous execution loop
- `bin/roadmap_status.py` — Progress dashboard
- `docs/roadmap/STATUS.yaml` — Execution state tracking

### Architecture

```
Roadmap File (*.md)
    ↓
roadmap_parser.py (Parse → RoadmapItem)
    ↓
auto_execute_roadmap.py (Find → Decompose → Execute)
    ↓
quick_task.sh (With dual-model flag)
    ↓
STATUS.yaml (Track status transitions)
    ↓
roadmap_status.py (Dashboard)
```

### Usage

#### View Dashboard

```bash
# Display progress overview
./bin/roadmap_status.py

# Export metrics to JSON
./bin/roadmap_status.py --export /tmp/metrics.json
```

Output:
```
================================================================================
📊 ROADMAP EXECUTION DASHBOARD
================================================================================

📈 Overall Progress
   Total Items: 35
   ✅ Completed:    2 (  5.7%)
   🔄 In Progress:   0
   ⏸️  Blocked:      0
   📋 Planned:     33

📋 Item Status
────────────────────────────────────────────────────────────────────────────
✅ COMPLETED (2)
   • RM-AUTO-001: Plain-English goal-to-agent system
   • RM-AUTO-002: Roadmap-to-execution compiler

📋 PLANNED (33)
   • RM-CORE-002: Installable edition-builder
   • RM-DEV-002: Dual-model inline QC coding loop
   ...
```

#### Parse Roadmap Files

```bash
# Parse all roadmap files
./bin/roadmap_parser.py --all

# Parse single file
./bin/roadmap_parser.py RM-CORE-004_EXECUTION_PACK.md
```

#### Autonomous Execution

```bash
# Dry-run: show what would be executed
./bin/auto_execute_roadmap.py --max-items 2 --dry-run

# Execute 5 roadmap items
./bin/auto_execute_roadmap.py --max-items 5

# Decompose using specific model
./bin/auto_execute_roadmap.py --max-items 10 --model deepseek-coder-v2
```

### Item Status Transitions

```
planned
  ↓
in_progress (during execution)
  ├→ completed (all subtasks succeeded)
  └→ blocked (some subtasks failed)
```

### STATUS.yaml Structure

```yaml
items:
  RM-AUTO-001:
    status: completed
    last_updated: '2026-04-24T02:00:29'
    notes: "Executed 1 subtasks"
    commit_hash: "abc123"

execution_log:
  - timestamp: '2026-04-24T02:00:24'
    item_id: RM-AUTO-001
    status: in_progress
  - timestamp: '2026-04-24T02:00:29'
    item_id: RM-AUTO-001
    status: completed
    notes: "Executed 1 subtasks"
```

### Dependency Resolution

Items with unmet dependencies are automatically skipped:

```yaml
RM-DEV-003:  # Blocked by RM-DEV-005
  dependencies: [RM-DEV-005]
  status: planned
```

The executor will:
1. Check if RM-DEV-005 is `completed`
2. If not, skip RM-DEV-003 and move to next available item
3. When RM-DEV-005 completes, RM-DEV-003 becomes executable

---

## End-to-End Example

```bash
# 1. View current progress
./bin/roadmap_status.py

# 2. Start autonomous execution (dry-run first)
./bin/auto_execute_roadmap.py --max-items 2 --dry-run

# 3. Execute items
./bin/auto_execute_roadmap.py --max-items 5

# 4. Check progress after execution
./bin/roadmap_status.py

# 5. Export metrics
./bin/roadmap_status.py --export /tmp/roadmap_metrics.json
```

---

## Integration Points

### With Quick Task

```bash
# The autonomous system uses quick_task.sh to execute subtasks
./bin/quick_task.sh --dual-model "implement feature X" file.py
```

### With Dual-Model Workflow

Each subtask automatically uses:
- Dual-model flag enabled
- Default model pair (fast_accurate)
- Auto-fix for low-severity issues
- User confirmation for medium issues

### With Git

- Auto-commits after each successful item
- Stores commit hashes in STATUS.yaml
- Tracks diff for reviewability
- Provides rollback points

---

## Best Practices

### For Roadmap Items
1. Keep first milestone bounded and concrete
2. List 3-7 measurable outcomes
3. Specify required artifacts clearly
4. Include failure modes for context

### For Execution
1. Start with dry-run (`--dry-run`)
2. Execute in small batches (`--max-items 2-3`)
3. Monitor dashboard after each batch
4. Use `make check` between batches

### For Decomposition
- LLM generates 3-7 subtasks per item
- Each subtask runs with dual-model enabled
- Fallback to single model if needed
- All execution is logged in STATUS.yaml

---

## Troubleshooting

### Dashboard shows blocked items
Check STATUS.yaml for `notes` field explaining why:
```bash
grep -A2 "blocked:" docs/roadmap/STATUS.yaml
```

### Task decomposition fails
- Increase timeout: `--timeout 600`
- Use smaller model: specify with `--model` flag
- Check Ollama is running: `curl http://127.0.0.1:11434/api/tags`

### Execution stuck on in_progress
- Check git status: no uncommitted changes allowed
- Review logs: `/tmp/task_history.json`
- Manual reset: Edit STATUS.yaml, change status back to `planned`

---

## Performance Metrics

After testing with 35 roadmap items:
- Parser load time: <100ms
- Dashboard render: <200ms
- Decomposition: ~10-15s per item
- Execution: Variable (depends on task complexity)
- Status update: <10ms

## Testing

All components are validated with:
```bash
make check          # Syntax validation
make test-offline   # Integration scenarios
make quick          # Fast regression checks
```

---

## Files Reference

| File | Lines | Purpose |
|------|-------|---------|
| bin/roadmap_parser.py | 200 | Parse markdown → RoadmapItem objects |
| bin/auto_execute_roadmap.py | 350 | Autonomous execution loop |
| bin/roadmap_status.py | 280 | Dashboard + metrics |
| bin/quick_task.sh | 180 | Task runner + state management |
| bin/local_coding_task.py | 330 | Task executor with dual-model flag |
| bin/review_commit.py | 250 | Standalone commit reviewer |
| domains/coding.py | 800 | CodingDomain with workflows |
| config/model_pairs.yaml | 35 | Model configuration |
| docs/roadmap/STATUS.yaml | 30 | State tracking |

---

Total implementation: **~2,400 lines of code + infrastructure**

**System Status: Fully operational ✅**
