# CLAUDE.md — System Operating Rules and Architecture

This file guides Claude Code execution on the integrated AI platform.

## Quick Start for Agents

1. **Read these first**: docs/agent/commands.md, docs/agent/validation_order.md
2. **System role**: Ollama-first local execution, Claude API for escalation only, Aider as transport adapter
3. **Key constraint**: All execution must be bounded, artifact-driven, and validatable

## System Architecture

**Three-layer design**:

1. **Inference Layer** — Ollama local models (primary), Claude API (escalation), Aider (adapter)
2. **Execution Layer** — Bounded task execution with fallback strategies
3. **Governance Layer** — Authority decisions, dependency tracking, memory policy

## Operating Rules

### Ollama-First Principle

- Default to local Ollama models (qwen2.5-coder:14b or equivalent)
- Use Claude API only for architecture, governance, blocker removal
- Never let external models displace local learning

### Aider as Transport Adapter

- Aider is a controlled transport adapter, not architecture authority
- Use only for tactical rapid-iteration local execution
- All strategic decisions must be repo-visible and ratified

### Bounded Execution Discipline

- Every task must declare: primary_objective, allowed_files, forbidden_files
- Every modification must be validatable with `make check` or `make quick`
- Artifacts must exist; claims without evidence are rejected

## Key Files

- **docs/agent/commands.md** — Real repo commands agents can execute
- **docs/agent/validation_order.md** — Exact validation sequence
- **docs/agent/known_failures.md** — Common failure patterns + fixes
- **docs/agent/repo_map.md** — Directory guide and file access patterns
- **governance/execution_control_template.yaml** — Execution package schema
- **governance/cmdb_lite.v1.yaml** — System inventory and model profiles
- **governance/roadmap_graph.v1.yaml** — 6-item integration dependencies

## Repository Structure

```
bin/                 # Executables: stage pipeline, managers
framework/           # Core runtime: scheduling, code execution
governance/          # Machine-readable authority
docs/agent/          # Agent-facing reference layer (READ FIRST)
docs/roadmap/        # Roadmap items and execution packs
artifacts/           # System outputs (validation, benchmarks)
config/              # Configuration and routing
policies/            # Model routing rules
tests/               # Test suites
AGENTS.md            # Session discipline (READ BEFORE MAJOR WORK)
```

## Validation Commands

- `make check` — Full repo syntax validation
- `make quick` — Fast checks on changed files
- `make test-offline` — 7 offline scenarios

## Allowed/Forbidden File Patterns

**Default allowed**: governance/**, docs/agent/**, docs/roadmap/**  
**Default forbidden**: framework/**, bin/**, tests/**, .github/**  
(Override in execution control template)

## Escalation Policy

Use Claude API for:
- Architecture decisions
- Governance updates
- Blocker removal
- Design reviews

Use Ollama for:
- Code modifications
- Tactical rapid iteration
- Bounded task execution
- Local-first optimization

## Execution Checklist

1. ✓ Read docs/agent/* (quick ~5 min read)
2. ✓ Understand objective and scope
3. ✓ Review allowed_files and forbidden_files
4. ✓ Create/modify files only in allowed_files
5. ✓ Run validation_order checks
6. ✓ Verify all expected_artifacts exist
7. ✓ Run `make check` and `make quick`
8. ✓ Report completion with artifact list

## Final Rule

Artifacts prove execution. Documentation without working code is not progress.
