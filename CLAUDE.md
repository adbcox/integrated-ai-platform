# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is an integrated AI platform advancing toward the **Codex 5.1 replacement milestone**. It combines local-first execution, progressive retrieval-augmented generation (RAG), and orchestrated planning to enable bounded complex AI coding tasks.

**Primary goal**: Build real capability gain on local-first code execution, not just infrastructure or benchmarks.

## Core Architecture

### Stage RAG Pipeline (Retrieval-Augmented Generation)

Progressive refinement stages that retrieve relevant code context for planning:

- **stage_rag1** (`bin/stage_rag1_*`): Initial code search with metrics
- **stage_rag2** (`bin/stage_rag2_*`): Search refinement with ranking signals
- **stage_rag3** (`bin/stage_rag3_*`): Context aggregation and deduplication
- **stage_rag4** (`bin/stage_rag4_plan_probe.py`): **Entity-aware reranking and target selection** — selects files that define specific code entities (classes, functions) extracted from queries
  - Uses BM25 token matching + entity definition scoring + domain-aware bonuses
  - Entity extraction: Identifies CamelCase tokens (ExecutorFactory, Stage, RAG)
  - Entity definition scoring: Boosts files containing "class EntityName" or "def EntityName"
  - Domain penalties: Deprioritizes docs files for code-intent queries
- **stage_rag6** (`bin/stage_rag6_plan_probe.py`): Multi-target orchestration planning

### Manager Hierarchy (Execution Orchestration)

Progressive execution layers that plan and coordinate code modifications:

- **stage3_manager** (`bin/stage3_manager.py`): Direct file modification execution with executor abstraction
  - Parses modification instructions: `target:: replace exact text 'old' with 'new'`
  - Routes to available executors (ClaudeCodeExecutor primary, AiderExecutor fallback)
- **stage4_manager** (`bin/stage4_manager.py`): Enhanced execution with validation
- **stage5_manager** (`bin/stage5_manager.py`): Higher-level task coordination
- **stage6_manager** (`bin/stage6_manager.py`): Multi-target orchestration — plans sequences of modifications across multiple files
- **stage7_manager** (`bin/stage7_manager.py`): Full AI agent execution — complete autonomy with learning loops

### Framework Core (`framework/` package)

Foundation infrastructure for execution:

- **worker_runtime.py** (42KB): WorkerPool, WorkerRuntime — parallel job execution
- **scheduler.py**: Job scheduling and lifecycle management
- **job_schema.py**: Job, JobClass, JobLifecycle, ValidationRequirement, EscalationPolicy definitions
- **code_executor.py**: ExecutorFactory, ClaudeCodeExecutor, AiderExecutor — abstraction for code modification
- **inference_adapter.py**: Abstract inference backend (local Ollama, remote APIs)
- **state_store.py**: Artifact persistence and state tracking
- **permission_engine.py**: Tool permissions and safety gates
- **learning_hooks.py**: Attribution and learning event recording
- **codebase_repomap.py**: Repository symbol extraction and indexing

## Common Development Commands

### Validation & Testing

```sh
make check                          # Full shell + Python syntax check
make quick                          # Fast checks on changed files
make test-offline                   # Run 7 deterministic offline scenarios (no NAS/API)
make test-changed-offline           # Run only scenarios affected by current changes
make micro-lane-regression          # Verify Stage 3 micro lane integrity
make micro-lane-stage6              # Dry-run Stage 6 planning with test queries
make preflight-normalization-guard  # Pre-commit normalization checks
```

### Local-First Execution (Aider Integration)

```sh
# Tactical rapid-iteration profiles (against local Ollama)
make aider-fast                     # qwen2.5-coder:14b (default local model)
make aider-hard                     # deepseek-coder-v2 (harder tasks)
make aider-smart                    # 32B model via OLLAMA_API_BASE_32B

# Micro lane: tiny autonomous edits with strict guardrails
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="shell/file.sh::token_name add guard clause" \
  AIDER_MICRO_FILES="shell/file.sh"
```

**Micro lane requirements**:
- Clean working tree (no staged/unstaged changes)
- Max 2 code-adjacent files (shell/, src/, bin/, tests/, config/, Makefile only)
- Message must name the file and give concrete action: `file.sh::function_name add docstring`
- Doc/README edits rejected
- Auto-runs `make quick` validation

### Workflow Modes

```sh
make workflow-mode-show             # Show current mode
make workflow-mode-tactical         # Opt into tactical (local aider) mode
make workflow-mode-codex-assist     # Opt into Codex-assisted planning mode
```

### Benchmarking & Learning Loops

```sh
make aider-bench-report             # Summary of recent aider runs
make aider-bench-compare SCENARIO=single-file-edit
make aider-bench-models             # Show default fast/hard/smart configs

make codex51-benchmark              # Codex 5.1 replacement benchmark
make codex51-learning-loop          # Analyze attribution and plan improvements
make codex51-campaign-list          # List active learning campaigns
make codex51-campaign-run TASK_ID='...' DRY_RUN=0
```

## Key Concepts & Patterns

### Entity-Aware Reranking (stage_rag4)

**Problem**: BM25 token frequency ranks files that *mention* concepts higher than files that *define* them.

**Solution**: Extract entity names from queries (CamelCase: ExecutorFactory, Stage) and boost scores for files that actually define those entities with regex matching on "class EntityName" or "def EntityName".

**Impact**: Improves retrieval accuracy by 28.5 percentage points on bounded task coverage (28.6% → 57.1%).

**Key files**:
- `bin/stage_rag4_plan_probe.py` — `_extract_entities()`, `_entity_definition_score()` functions
- `tests/run_offline_scenarios.sh` — Validates entity-aware reranking on representative queries

### Intent-Driven Ranking

Queries are classified as:
- **modification_intent**: "improve ExecutorFactory", "enhance promotion workflow"
- **code_intent**: "where is manager orchestration code?", "what files implement execution?"
- **docs_intent**: "what docs explain codex51?"
- **mixed**: Combination of above

Domain penalties are applied based on intent:
- Code queries get -2.5 penalty for docs/ files (deprioritize documentation)
- Modification queries get context-specific bonuses for targeted paths

### Executor Abstraction

Code modifications route through an executor abstraction (`framework/code_executor.py`):

- **ClaudeCodeExecutor** (primary): Direct file manipulation via Claude Code
- **AiderExecutor** (fallback): Delegates to local aider for complex edits
- **ExecutorFactory**: Auto-selects based on availability

Message format parsed by stage3_manager:
```
target:: replace exact text 'old_literal' with 'new_literal'
```

### Bounded Session Discipline

From AGENTS.md — every session must declare:

1. **primary_session_type**: capability_session | measurement_session | planning_session | governance_session
2. **primary_objective**: Single focused goal (not "improve everything")
3. **accepted_baseline_state**: What metrics/state are we starting from
4. **blockers_resolved_in_order**: List of specific blockers tackled with evidence
5. **real_paths_rerun_by_step**: Validation at each step on real code
6. **final_remaining_blocker_or_stop_reason**: Why we stopped (not safely attackable, external blocker, or completed)

Sessions are **incomplete** without:
- Full repo validation (make check, make quick, make test-offline after meaningful changes)
- Real path reruns (not just fixture/dry-run validation)
- Evidence-based blocker identification (metrics, not speculation)

## Important Constraints

### Validation Discipline (Mandatory)

After ANY meaningful code change:
1. Run `make check` (syntax validation)
2. Run `make quick` (fast affected-file checks)  
3. Run affected real paths (e.g., `make test-offline`, `make micro-lane-stage6`)
4. Run full benchmark if retrieval/ranking changes made

**Do not stop after**:
- Only fixture-level proof
- Only dry-run validation
- Only benchmark improvements without real path rerun
- Only code-path additions without full validation

### No Reopening Accepted Work

If a previous session's work is marked complete with validation evidence:
- Do NOT narrate the fix again as if it still needs implementation
- Do NOT re-measure the same baseline without regression evidence
- Treat it as foundation for the next blocker

### Safely Attackable Rule

Only implement improvements that are:
1. **Scoped** — Affect specific, identifiable behavior
2. **Measurable** — Impact visible on real paths
3. **Non-speculative** — Don't require redesign of adjacent systems
4. **Validatable** — Full repo validation passes

**Stop if remaining blockers require**:
- Redesign of core components
- Speculative infrastructure additions
- Acceptance of additional unknowns

### Local-First Preference

- Use local Ollama models (aider-fast, aider-hard) for in-scope bounded work
- Use Codex/manual intervention only for architecture/blocker removal/governance
- Do not let Codex displace the local system on work it should be learning

## Repository Structure

```
bin/                 # Executable stage probes and managers
  stage_rag{1-6}_*   # Retrieval and planning stages
  stage{3-7}_manager.py
  aider_*.sh, aider_*.py
  codex51_*.py
  
framework/           # Core execution runtime
  worker_runtime.py  # Job scheduling and parallel execution
  code_executor.py   # Executor abstraction for code modifications
  job_schema.py      # Job lifecycle and schema
  inference_adapter.py
  scheduler.py
  state_store.py
  
promotion/           # Promotion logic and workflows
docs/                # Policy and roadmap documentation
tests/               # Offline scenario validation suite
artifacts/           # Output: stage_rag*, manager runs, benchmarks, escalations
config/              # Configuration and routing rules
policies/            # Local model routing rules
regressions/         # Regression test packs for micro lane
```

## Useful Commands for Investigation

```sh
# Understand current failing tests
make test-offline 2>&1 | head -100

# Check recent stage_rag4 retrieval decisions
cat artifacts/stage_rag4/usage.jsonl | tail -5 | python3 -m json.tool

# View recent manager plans
ls -ltr artifacts/stage6_manager/ | tail -5

# Check micro lane integrity
make micro-lane-regression

# Investigate escalation index
tail -20 artifacts/escalations/index.jsonl

# List local model routing rules
make local-model-rules-show
```

## Testing a Single Scenario

To test specific stage_rag4 retrieval behavior:

```bash
python3 bin/stage_rag4_plan_probe.py --top 6 --max-targets 4 improve ExecutorFactory
python3 bin/stage_rag4_plan_probe.py --top 6 --max-targets 4 where is manager orchestration code
```

Output includes:
- `targets`: Selected files with rank scores and selection reasons
- `entity_names`: Extracted CamelCase entities from query
- `entity_boost`: Points added for files defining those entities

## Recommended Session Template

1. **Preamble**: State primary_session_type, primary_objective, accepted_baseline_state
2. **Blocker Analysis**: Identify the strongest safe next-step blocker from previous work
3. **Implementation**: Code the fix in a bounded scope
4. **Real Path Validation**: Run affected scenarios (test-offline, micro-lane-*, bench if relevant)
5. **Full Validation**: make check, make quick, full test suite
6. **Final Report**: Document blockers_resolved, real_paths_rerun, final_remaining_blocker_or_stop_reason

See `/tmp/final_session_report.md` for an example of the expected 12-section format.

## Governance authority (machine-readable)

The coding-runtime side of this repository has machine-readable governance
authority under `governance/`. Narrative roadmaps under `docs/` are historical
or advisory. The legacy `config/promotion_manifest.json` is tactical release
authority only and is frozen pending explicit migration (see
`governance/authority_adr_0001_source_of_truth.md`).

- [governance/README.md](governance/README.md) — human-readable authority map
- [governance/current_phase.json](governance/current_phase.json) — current canonical phase and next allowed package class
- [governance/canonical_roadmap.json](governance/canonical_roadmap.json) — canonical phases 0..6 and statuses
- [governance/phase_gate_status.json](governance/phase_gate_status.json) — gate table for canonical phases 0..6
- [governance/runtime_contract_version.json](governance/runtime_contract_version.json) — runtime primitive surface and contract version
- [governance/tactical_family_classification.json](governance/tactical_family_classification.json) — EO / ED / MC / LOB / ORT / PGS classification
