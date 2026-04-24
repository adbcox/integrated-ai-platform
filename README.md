# Integrated AI Platform

Governed local-first AI operating system and control plane for autonomous business, personal, operational, and development workflows.

## What this repository is

This repository is the implementation and governance home for a platform whose broader mission is **not only AI coding**.

Its purpose is to provide:
- a central governed AI brain / control plane
- reusable connector and workflow infrastructure
- bounded local execution with evidence and validation
- multiple ingress channels for commands, ideas, and automation
- domain-specific autonomous functions built on one shared substrate

## Role of local coding autonomy

Local coding autonomy is a **foundational enabling capability** of the platform.
It is important because it lets the system improve, extend, and govern itself locally.

It is **not** the sole purpose of the platform.
The broader mission is autonomous and semi-autonomous execution across business, personal, operational, and development domains.

For the explicit mission/scope statement, read:
- `docs/architecture/SYSTEM_MISSION_AND_SCOPE.md`

For the full architecture source of truth, read:
- `docs/architecture/MASTER_SYSTEM_ARCHITECTURE.md`

For roadmap authority and current operating posture, read:
- `docs/roadmap/ROADMAP_AUTHORITY.md`
- `docs/governance/CURRENT_OPERATING_CONTEXT.md`
- `docs/roadmap/POST_CONVERGENCE_OPERATING_MODE.md`

## Quick Start

### New to this project?

1. **Read the handoff guide:** [`docs/HANDOFF_GUIDE.md`](docs/HANDOFF_GUIDE.md)
   - Repository structure and what each folder does
   - How to check progress and resume execution
   - Common issues and how to fix them
   - SSH connection details

2. **Understand the architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
   - System overview and component responsibilities
   - Data flow from roadmap items to executed code
   - Technology stack and design decisions

3. **Run the autonomous executor:**
   ```bash
   # Check that dependencies are installed
   pip install -r requirements.txt
   
   # Verify Ollama is running (local code generation backend)
   curl http://127.0.0.1:11434/api/tags
   
   # Check current progress
   python3 -c "from bin.roadmap_parser import parse_roadmap_directory; from pathlib import Path; items = parse_roadmap_directory(Path('docs/roadmap/ITEMS')); completed = sum(1 for i in items if i.status == 'Completed'); print(f'{completed}/{len(items)} items completed ({100*completed/len(items):.1f}%)')"
   
   # Run executor in dry-run mode (no git commits)
   python3 bin/auto_execute_roadmap.py --target-completions 1 --dry-run
   
   # Run executor for real (will commit status changes to git)
   python3 bin/auto_execute_roadmap.py --target-completions 5
   
   # Resume from where you left off
   python3 bin/auto_execute_roadmap.py --resume --target-completions 10
   ```

4. **Run the test suite:**
   ```bash
   # Run all tests
   python3 -m pytest tests/test_autonomous_executor.py -v
   
   # Run offline validation suite
   make test-offline
   ```

## Current Roadmap Status

- **Total Items:** 223 roadmap items (up from 194, +30 Monitoring/Deployment/CI-CD)
- **Completed:** 57 items (25.6% completion rate)
- **In Progress:** Selected items executing via autonomous executor
- **Remaining:** 166 items in planned backlog
- **Execution Rate:** ~45-60 minutes per item (varies by complexity)
- **Circular Dependencies:** 0 detected (all 45 cycles broken and committed)
- **Primary Executor:** Autonomous executor with local Ollama (qwen2.5-coder:14b)

### Recent Progress

Check progress with: `git log --oneline | head -20`

Newly added families (post-convergence expansion):
- **RM-MON-001 through RM-MON-010** — Monitoring infrastructure
- **RM-DEPLOY-001 through RM-DEPLOY-010** — Blue-green deployment, feature flags
- **RM-CI-001 through RM-CI-010** — CI/CD pipelines, artifact management
- **Plus** — Security, Reliability, Observability, Data, Integration, Testing improvements

## Current operating posture

The repository is operating in **post-convergence governed local-execution mode**.

That means:
- the local-autonomy substrate is treated as materially closed unless canonical repo truth shows regression
- future work should extend the governed platform instead of re-litigating the foundation by default
- bounded execution, artifact evidence, validation, and truth-surface sync remain mandatory
- roadmap closeout is not accepted until committed, pushed, and remote-visible

## Key operating layers

The platform is built around these layers:
- architecture and mission truth
- canonical roadmap item truth
- derived planning and dependency surfaces
- governed execution modes
- local-first implementation and validation substrate
- domain workflows and autonomous functions on top of the shared substrate

## Repo governance entry points

Start here when working in the repo:
- `docs/governance/CURRENT_OPERATING_CONTEXT.md`
- `docs/governance/DOCUMENT_STATE_INDEX.md`
- `docs/execution_modes/EXECUTION_ROUTER.md`
- `docs/governance/PROMPT_PACKET_STANDARD.md`

## Maintenance and validation

Run combined shell + Python syntax checks:

```sh
make check
```

Run fast changed-file checks:

```sh
make quick
```

Run deterministic offline behavior tests (no NAS/API dependency):

```sh
make test-offline
```

Run only offline scenarios affected by current file changes:

```sh
make test-changed-offline
```

## Local Aider tactical entry points

Fast local tactical Aider entry points:

```sh
make aider-fast
make aider-hard
make aider-smart
make aider-smart-status
```

Micro lane:

```sh
make aider-micro-help
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="shell/common.sh::extract_session add guard for blank ids" \
  AIDER_MICRO_FILES="shell/common.sh"
```

## Tooling references

- `docs/execution_modes/LOCAL_AIDER_EXEC_MODE.md`
- `docs/execution_modes/CODEX_CONTROL_MODE.md`
- `docs/execution_modes/CODEX_EXEC_MODE.md`
- `docs/execution_modes/CLAUDE_CODE_EXEC_MODE.md`
- `docs/execution_modes/LOCAL_CONTROL_WINDOW_MODE.md`

## Notes

This repository contains implementation, governance, and operating surfaces for a broader AI operating platform.
Do not treat it as only a coding-assistant repo or only a browser-automation repo.
