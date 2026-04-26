# Handoff Guide: Integrated AI Platform

> **See also:** [PLATFORM_OVERVIEW.md](PLATFORM_OVERVIEW.md) | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**Last Updated:** 2026-04-24  
**Current Status:** 253 roadmap items, 59 completed (23.3%), 0 circular dependencies  
**Execution Mode:** Autonomous executor on tmux (mac-mini)

---

## Quick Start (5 minutes)

### 1. Verify environment

```bash
# Check Python and dependencies
python3 --version  # Should be 3.9+
pip install -r requirements.txt

# Verify Ollama is running (local code generation)
curl http://127.0.0.1:11434/api/tags

# Check aider is installed
aider --version
```

### 2. Check current progress

```bash
# See status of last 10 items
git log --oneline | head -10

# Count completed items
python3 -c "
from bin.roadmap_parser import parse_roadmap_directory
from pathlib import Path
items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
completed = sum(1 for i in items if i.status == 'Completed')
total = len(items)
print(f'{completed}/{total} items completed ({100*completed/total:.1f}%)')
"

# Check for dependency cycles (should be 0)
python3 -c "
from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies, detect_cycles
from pathlib import Path
items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
infer_dependencies(items)
cycles = detect_cycles(items)
print(f'{len(cycles)} cycles detected')
"
```

### 3. Run the executor

```bash
# Dry-run mode (no git commits, but still calls Ollama for decomposition ~140s)
python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run

# True no-op (just roadmap load + cycle check, no Ollama call)
python3 bin/auto_execute_roadmap.py --dry-run --max-items 0

# Real mode (will commit status changes)
python3 bin/auto_execute_roadmap.py --target-completions 5

# Resume from where you left off
python3 bin/auto_execute_roadmap.py --resume --target-completions 10
```

### 4. Monitor execution

```bash
# Tail the execution log
tmux attach -t roadmap

# View recent failed subtasks
tail -10 artifacts/execution_failures.jsonl | python3 -m json.tool

# View retrieval decisions (stage RAG4)
tail -5 artifacts/stage_rag4/usage.jsonl | python3 -m json.tool

# Run validation suite
make test-offline
```

---

## Repository Structure

### bin/ — Execution and processing scripts

- `auto_execute_roadmap.py`: Main autonomous executor entry point
- `break_dependency_cycles.py`: Detect and break circular dependencies
- `roadmap_parser.py`: Parse roadmap items from markdown
- `stage_rag*_*.py`: Retrieval-augmented generation stages (context selection)
- `stage*_manager.py`: Execution managers (stages 3-7 of planning)
- `aider_*.py` / `aider_*.sh`: Local Ollama integration

### framework/ — Core runtime infrastructure

- `code_executor.py`: Executor abstraction (ClaudeCode / Aider)
- `worker_runtime.py`: Parallel job execution and scheduling
- `job_schema.py`: Job lifecycle and validation rules
- `inference_adapter.py`: Local/remote inference backend
- `state_store.py`: Artifact persistence and caching
- `codebase_repomap.py`: Symbol indexing and repomap generation
- `permission_engine.py`: Tool permissions and safety gates

### domains/ — Domain-specific autonomous functions

Application-layer workflows and bounded execution contexts.

### tests/ — Validation and regression tests

- `test_autonomous_executor.py`: Unit tests (mostly mocked), 3 real subprocess tests in `TestExecutorIntegration`
- `test_reality_check.py`: Zero-mock reality checks (Ollama generate, aider file edit, executor commit)
- `run_offline_scenarios.sh`: 7 deterministic offline behavior tests
- `scenarios/`: Environment fixture files

### docs/roadmap/ITEMS/ — Canonical roadmap truth (253 items)

Markdown files (RM-*.md) organized by category:
- RM-DEV-*, RM-OBS-*, RM-SEC-*, RM-DATA-*, RM-DEPLOY-*, etc.

---

## Checking Progress

### By git history
```bash
git log --oneline | head -20
git log --oneline --since="24 hours ago"
```

### By roadmap status
```bash
python3 << 'INNER'
from bin.roadmap_parser import parse_roadmap_directory
from pathlib import Path
from collections import defaultdict

items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
by_status = defaultdict(list)

for item in items:
    by_status[item.status].append(item.id)

for status in sorted(by_status.keys()):
    print(f"{status}: {len(by_status[status])} items")
INNER
```

### By category progress
```bash
python3 << 'INNER'
from bin.roadmap_parser import parse_roadmap_directory
from pathlib import Path
from collections import defaultdict

items = parse_roadmap_directory(Path('docs/roadmap/ITEMS'))
by_category = defaultdict(lambda: {"total": 0, "completed": 0})

for item in items:
    category = item.id.split('-')[1]
    by_category[category]["total"] += 1
    if item.status == "Completed":
        by_category[category]["completed"] += 1

for cat in sorted(by_category.keys()):
    data = by_category[cat]
    pct = 100 * data["completed"] / data["total"]
    print(f"{cat}: {data['completed']}/{data['total']} ({pct:.0f}%)")
INNER
```

---

## Common Issues and Solutions

### Issue 1: Circular dependencies detected

Solution:
```bash
python3 bin/break_dependency_cycles.py
git add docs/roadmap/ITEMS/
git commit -m 'fix: Break circular dependencies'
```

### Issue 2: Executor crashes on startup

Solution:
```bash
pip install -r requirements.txt
python3 -c "from bin.roadmap_parser import parse_roadmap_directory; from pathlib import Path; items = parse_roadmap_directory(Path('docs/roadmap/ITEMS')); print(f'Loaded {len(items)} items')"
```

### Issue 3: Decomposition times out

Solution:
```bash
curl -s http://127.0.0.1:11434/api/tags
ollama list
ollama pull qwen2.5-coder:14b
```

### Issue 4: File syntax error

Solution:
```bash
make check
python3 -m py_compile path/to/file.py
git checkout HEAD -- path/to/file
```

### Issue 5: No git commits from executor

Solution:
```bash
grep "Dry run: True" execution.log
python3 bin/auto_execute_roadmap.py --target-completions 1
git config user.name "Adrian Cox"
git config user.email "adbcox@gmail.com"
```

---

## Key Commands

### Status
```bash
python3 -c "from bin.roadmap_parser import parse_roadmap_directory; from pathlib import Path; items = parse_roadmap_directory(Path('docs/roadmap/ITEMS')); completed = sum(1 for i in items if i.status == 'Completed'); print(f'{completed}/{len(items)} completed ({100*completed/len(items):.1f}%)')"

git log --oneline | head -20

python3 -c "from bin.roadmap_parser import parse_roadmap_directory, infer_dependencies, detect_cycles; from pathlib import Path; items = parse_roadmap_directory(Path('docs/roadmap/ITEMS')); infer_dependencies(items); print(f'{len(detect_cycles(items))} cycles')"
```

### Execution
```bash
# Dry-run
python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run

# Real
python3 bin/auto_execute_roadmap.py --target-completions 5

# Resume
python3 bin/auto_execute_roadmap.py --resume --target-completions 10
```

### Validation
```bash
make check
make quick
make test-offline
python3 -m pytest tests/test_autonomous_executor.py -v
```

---

## Next Steps

1. Verify environment: `pip install -r requirements.txt && curl http://127.0.0.1:11434/api/tags`
2. Check status: `git log --oneline | head -5`
3. Read architecture: See `docs/ARCHITECTURE.md`
4. Run first execution: `python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run`
5. For governance: `docs/governance/CURRENT_OPERATING_CONTEXT.md`
