# Repository Map

Key directories and their purpose.

## Source Code

- `framework/` — Core runtime: job scheduling, code execution, inference adapters
- `bin/` — Executable scripts: stage RAG pipeline, managers, compiler
- `shell/` — Shell utilities for local execution

## Documentation & Governance

- `docs/roadmap/` — Roadmap items (.yaml) and execution packs (.md)
- `docs/agent/` — Agent-facing reference (this directory)
- `governance/` — Machine-readable authority: schema, policy, state
- `docs/progress-contract.md` — Session contract requirements

## Artifacts & Output

- `artifacts/` — System outputs: validation, benchmarks, runs
- `artifacts/governance/` — Governance artifacts (validation evidence)

## Configuration

- `config/` — Configuration files and routing rules
- `policies/` — Model routing policies for Ollama
- `Makefile` — Build and validation commands

## Testing

- `tests/` — Test suites and offline scenarios
- `regressions/` — Regression test packs

## Key Files for Agents

- `CLAUDE.md` — System architecture and development patterns
- `AGENTS.md` — Session discipline and operating rules
- `governance/execution_control_template.yaml` — Execution package template
- `governance/cmdb_lite.v1.yaml` — System inventory and model profiles
- `governance/roadmap_graph.v1.yaml` — Item dependencies

## File Access Patterns

- **Read-only**: framework/, bin/, tests/, docs/ (content only, no modifications)
- **Writable**: artifacts/, governance/ (output and authority files)
- **Forbidden**: .github/, .git/, external integrations
