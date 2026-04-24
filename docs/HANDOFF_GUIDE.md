# Handoff Guide: Integrated AI Platform

This guide is for developers taking over the integrated-ai-platform project. It covers repository structure, current state, key components, and operational procedures.

## Current State

- **Roadmap Items:** 194 items created
- **Completed Items:** 54 items completed
- **Execution Mode:** Autonomous executor running via tmux
- **Primary Technology:** Python 3.9+, Ollama local models, Aider for code generation, GitHub for version control

## Repository Structure

### `/bin/` — Executable Scripts & Entry Points

- **`auto_execute_roadmap.py`** — Main autonomous executor. Runs continuously, parses roadmap items, decomposes them into subtasks, executes via aider, and updates status in git. This is the primary driver of progress.
  - Entry point: `python3 bin/auto_execute_roadmap.py [--filter PATTERN] [--target-completions N]`
  - Key features: Retry logic, timeout protection, status tracking, consecutive-failure stopping

- **`local_coding_task.py`** — Single task wrapper for ad-hoc execution. Executes a single coding task without requiring decomposition.
  - Entry point: `python3 bin/local_coding_task.py "task description"`

- **`roadmap_parser.py`** — Parses YAML roadmap items, extracts metadata, manages status updates, handles git integration.
  - Functions: `parse_roadmap_directory()`, `infer_dependencies()`, `detect_cycles()`, `update_frontmatter()`

- **`stage_rag*.py`** — Retrieval-augmented generation pipeline for context selection. Used by advanced planning.

- **`stage*_manager.py`** — Orchestration managers for multi-file modifications. Stages 3-7 handle increasing complexity.

- **`aider_*.py` & `aider_*.sh`** — Aider integration for local-first code execution.

### `/docs/roadmap/` — Roadmap Item Definitions

- **`ITEMS/RM-*.yaml`** — Individual roadmap item files. Each contains:
  - Metadata: ID, title, category, type, status, priority, queue rank
  - Description and why it matters
  - Key requirements and acceptance criteria
  - Affected systems and files
  - Dependencies and risks
  - Status transition notes

- **`ROADMAP_INDEX.md`** — Human-readable inventory of all items, grouped by category.

- **`ROADMAP_AUTHORITY.md`** — Source of truth for item status interpretation.

- **`ROADMAP_STATUS_SYNC.md`** — Status synchronization rules and canonical views.

### `/framework/` — Core Runtime Infrastructure

- **`worker_runtime.py`** — WorkerPool and job scheduling for parallel execution.
- **`code_executor.py`** — ExecutorFactory and executor abstraction (ClaudeCodeExecutor, AiderExecutor).
- **`job_schema.py`** — Job, JobLifecycle, and ValidationRequirement definitions.
- **`state_store.py`** — Artifact persistence and state tracking.
- **`permission_engine.py`** — Tool permission gates and safety checks.
- **`learning_hooks.py`** — Attribution and learning event recording.

### `/domains/` — Feature Domains

- **`coding.py`** — Aider integration and local-first code execution.
- Other domains handle specific features (workflows, analysis, etc.).

### `/tests/` — Test Suite

- **`test_autonomous_executor.py`** — Comprehensive test suite (19 tests) validating:
  - Priority sorting and dependency checking
  - Subtask decomposition
  - Timeout enforcement
  - Consecutive failure handling
  - Output flushing and crash reporting
  - Edge cases (no items, filtering, auto-fix)

### `/artifacts/` — Execution Output & Logs

- **`executions/`** — Timestamped execution records and stage outputs.
- **`execution_failures.jsonl`** — JSONL log of all failures with timestamps, item IDs, subtasks, and errors.
- **`escalations/`** — Items requiring manual intervention.
- **`stage_rag4/`** — Retrieval ranking decisions and selection reasons.

### `/config/` — Configuration Files

- **`security-policy.yaml`** — Security scanning configuration (Bandit, CVE checks).
- Model routing rules and local-first preferences.

## Checking Progress

### Quick Status View

```bash
# See current roadmap status in git log (last 20 commits)
git log --oneline | head -20

# Count completed items
git log --oneline | grep "status:.*Completed" | wc -l
```

### Detailed Progress Reports

```bash
# Run offline validation suite (deterministic, no API/NAS needed)
make test-offline 2>&1 | head -100

# Run autonomous executor in dry-run mode
python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run

# Check recent execution failures
tail -50 artifacts/execution_failures.jsonl | python3 -m json.tool
```

### Live Execution Monitoring

```bash
# Check if executor is running in tmux
tmux list-sessions
tmux attach -t ai-executor  # Re-attach if needed

# Monitor real-time output
tail -f execution.log
```

## Common Issues & Fixes

### Issue: Executor Crashes Silently

**Symptom:** execution.log shows only urllib warnings, then nothing.

**Cause:** Exception during startup (parse_roadmap_directory, git operations).

**Fix:**
```bash
# Check for syntax errors in YAML items
python3 -c "from bin.roadmap_parser import parse_roadmap_directory; parse_roadmap_directory('docs/roadmap/ITEMS')"

# Verify git state (no uncommitted changes blocking commits)
git status
git add -A && git commit -m "cleanup" || true
```

### Issue: Status Updates Not Appearing in Git

**Symptom:** Executor runs but `git log` doesn't show status changes.

**Cause:** Missing `flush=True` in status update prints, or git configuration issues.

**Fix:**
```bash
# Verify git user is configured
git config user.name && git config user.email

# Check if status update code has flush=True
grep -n "flush=True" bin/auto_execute_roadmap.py | head -10

# Force a test update
python3 bin/auto_execute_roadmap.py --target-completions 0 --dry-run
```

### Issue: Infinite Loop on Filter Mismatch

**Symptom:** Executor keeps reloading items, filter pattern doesn't match.

**Cause:** No forward progress when reload returns same unmatched items.

**Fix:**
```bash
# The fix adds a skipped_without_match counter that breaks after 10 attempts.
# Verify the fix is in place:
grep -A 5 "skipped_without_match" bin/auto_execute_roadmap.py

# Use filter that matches at least one item:
python3 bin/auto_execute_roadmap.py --filter "RM-DEV" --target-completions 1
```

### Issue: Process Hangs After Timeout

**Symptom:** Executor times out a process, but appears to hang indefinitely.

**Cause:** SIGKILL doesn't guarantee process termination; proc.wait() called without timeout.

**Fix:**
```bash
# Verify timeout protection on proc.wait() is in place:
grep -A 5 "proc.wait(timeout=5)" bin/auto_execute_roadmap.py

# If hanging, kill the executor tmux session and restart:
tmux kill-session -t ai-executor
# Then restart via SSH or direct execution
```

### Issue: File Corruption or Malformed YAML

**Symptom:** Parser fails on specific item file.

**Cause:** Manual edits or encoding issues in YAML files.

**Fix:**
```bash
# Validate all YAML files
for f in docs/roadmap/ITEMS/RM-*.yaml; do
  python3 -c "import yaml; yaml.safe_load(open('$f'))" || echo "BROKEN: $f"
done

# Revert broken file
git checkout docs/roadmap/ITEMS/RM-XXXXX.yaml

# Or re-create from the markdown version
# (all items have markdown equivalents in docs/roadmap/items/RM-*.md)
```

## Resuming Execution

### If Executor Is Not Running

```bash
# Connect to the machine via SSH
ssh admin@mac-mini

# Check if tmux session exists
tmux list-sessions

# If session exists, re-attach
tmux attach -t ai-executor

# If session doesn't exist, create new one
cd /Users/admin/repos/integrated-ai-platform
tmux new-session -d -s ai-executor -c /Users/admin/repos/integrated-ai-platform
tmux send-keys -t ai-executor "python3 bin/auto_execute_roadmap.py --target-completions 100" Enter

# Monitor output
tail -f execution.log
```

### If Executor Has Unfinished Items

```bash
# Check what was last executed
git log --oneline | head -5

# Count items still in "In progress" state
grep "In progress" docs/roadmap/ITEMS/RM-*.yaml | wc -l

# Resume from that point
python3 bin/auto_execute_roadmap.py --target-completions 50  # Continue from next executable item
```

### If Specific Item Failed

```bash
# View failure details
grep "RM-XXXXX" artifacts/execution_failures.jsonl | python3 -m json.tool

# Manually attempt the item
python3 bin/auto_execute_roadmap.py --filter "RM-XXXXX" --target-completions 1

# Or decompose and execute manually
python3 bin/local_coding_task.py "specific task description"
```

## SSH Connection Details

- **Host:** mac-mini
- **User:** admin
- **Repository Path:** /Users/admin/repos/integrated-ai-platform
- **Tmux Session:** ai-executor (primary executor running here)
- **Python:** /usr/bin/python3 (version 3.9.6)
- **Ollama:** Running locally on localhost:11434
- **Default Model:** qwen2.5-coder:14b

### Quick SSH Commands

```bash
# Connect
ssh admin@mac-mini

# Run executor in background
ssh admin@mac-mini "cd /Users/admin/repos/integrated-ai-platform && python3 bin/auto_execute_roadmap.py &"

# Check executor status
ssh admin@mac-mini "cd /Users/admin/repos/integrated-ai-platform && ps aux | grep auto_execute"

# Tail execution log remotely
ssh admin@mac-mini "tail -f /Users/admin/repos/integrated-ai-platform/execution.log"
```

## Key Files to Monitor

1. **`execution.log`** — Main execution transcript with [DEBUG] and [STARTUP] markers.
2. **`artifacts/execution_failures.jsonl`** — JSONL log of all failures.
3. **`git log`** — Source of truth for completed items (each completion is a commit).
4. **`.gitignore`** — Excludes artifacts/ and execution.log from version control.

## Validation Checklist Before Handoff

- [ ] Repository cloned and Python dependencies installed (`pip install -r requirements.txt`)
- [ ] Ollama running locally and accessible (`curl http://127.0.0.1:11434/api/tags`)
- [ ] Git user configured (`git config user.name` and `git config user.email`)
- [ ] Executor runs without immediate crash (`python3 bin/auto_execute_roadmap.py --dry-run`)
- [ ] Tests pass (`python3 -m pytest tests/test_autonomous_executor.py -v`)
- [ ] Recent roadmap items can be parsed (`python3 bin/roadmap_parser.py docs/roadmap/ITEMS`)
- [ ] Git history is clean and recent commits visible (`git log --oneline | head -10`)

## Support Resources

- **Autonomous Executor Architecture:** See `docs/ARCHITECTURE.md`
- **Roadmap Item Format:** See `docs/roadmap/ROADMAP_AUTHORITY.md` and any `RM-*.yaml` file
- **Code Executor Details:** See `framework/code_executor.py` docstrings and `domains/coding.py`
- **Test Coverage:** Run `make test-offline` for deterministic validation
- **Performance Benchmarks:** See `artifacts/stage_rag4/usage.jsonl` for retrieval performance

## Emergency Procedures

### Executor Won't Start

1. Check Python version: `python3 --version` (should be 3.9+)
2. Check git config: `git config --list`
3. Verify repository state: `git status`
4. Check Ollama: `curl http://127.0.0.1:11434/api/tags`
5. Run with verbose output: `python3 -u bin/auto_execute_roadmap.py 2>&1 | head -50`

### All Roadmap Items Stuck

1. Check for cycles: `python3 -c "from bin.roadmap_parser import detect_cycles, parse_roadmap_directory; cycles = detect_cycles(parse_roadmap_directory('docs/roadmap/ITEMS')); print(f'Cycles: {cycles}')"` 
2. Check for missing dependencies: Look for items with status not in ["Completed", "Accepted"]
3. Reset executor state: Delete artifacts directory if needed: `rm -rf artifacts/executions/*`

### Git Commits Failing

1. Verify git user: `git config user.name && git config user.email`
2. Check for pre-commit hooks: `ls -la .git/hooks/`
3. Check repository permissions: `ls -ld .git`
4. Manually retry: `git add -A && git commit -m "test commit"`

---

**Last Updated:** 2026-04-24
**Maintained By:** Development Team
**Version:** 1.0
