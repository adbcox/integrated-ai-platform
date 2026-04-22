# Agent Commands Reference

Real repo commands executable by agents. All commands are Makefile targets or shell scripts.

## Validation Commands

- `make check` — Full repo syntax and Python compilation check
- `make quick` — Fast checks on changed files only
- `make test-offline` — Run 7 deterministic offline scenarios (no NAS/API)

## Agent Operating Commands

- `make workflow-mode-show` — Display current workflow mode
- `make workflow-mode-tactical` — Set tactical (local aider) mode
- `make workflow-mode-codex-assist` — Set Codex-assisted planning mode

## Benchmarking Commands

- `make aider-bench-report` — Show recent aider run summary
- `make codex51-benchmark` — Run Codex 5.1 replacement benchmark
- `make test-offline` — Run deterministic validation suite

## Investigation Commands

- `grep -r "pattern" docs/` — Search documentation
- `python3 bin/stage_rag4_plan_probe.py --top 6 --max-targets 4 <query>` — Test retrieval
- `ls -ltr artifacts/` — View recent artifact changes
- `cat governance/*.yaml | grep "status:"` — View governance state

## Rules for Agent Execution

1. Always run `make check` after code changes
2. Run `make quick` for affected-file validation
3. Verify all artifacts exist before claiming success
4. Use `make test-offline` for real-path validation
5. Never modify files in forbidden_files without explicit approval
