# Aider Performance Guide

Codex owns orchestration. Aider exists to execute tightly scoped patches with minimal context. Follow this checklist every time.

## 1. Preflight Checklist
- ✅ Pick a task class from `config/aider_task_classes.json` (bugfix-small, refactor-narrow, test-repair, lint-fix, docs-sync, typed-cleanup, targeted-feature-patch).
- ✅ Confirm class limits: max files, max LOC, max roots, and forbidden globs.
- ✅ Objective + target files known (`AIDER_OBJECTIVE`/`AIDER_FILES` or `AIDER_AUTO_FILES`).
- ✅ Guardrails confirmed: no ports/secrets/systemd/policy files unless Codex handles manually.

## 2. Brief Template (required fields)
Preferred command path:
```sh
make aider-bugfix-small \
  AIDER_NAME="login-fix" \
  AIDER_OBJECTIVE="Stop nil session panic" \
  AIDER_FILES="browser_operator_login_flow.sh tests/mock_login_flow.sh"
```
Shortcuts: `make aider-docs-micro`, `make aider-shell-micro`, `make aider-test-micro`, `make aider-lint-micro` auto-fill objectives and classes. `make aider-auto AIDER_OBJECTIVE=... AIDER_AUTO_FILES="file1 file2"` calls the classifier.

This pipeline generates JSON briefs, enforces budgets, and runs the guard automatically.

## 3. Invocation Rules
- Use `make aider-<class>` or `./bin/aider_task_runner.sh` to avoid manual prompt building.
- Prompts stay short because the JSON brief already encodes target files/constraints.
- `bin/aider_loop.sh` automatically runs `bin/aider_guard.py` after patch application; `--skip-guard` is only for emergency fallback.

Default fast tactical settings (CPU-reliable path):
```sh
make aider-fast
make aider-hard
make aider-smart        # run against 32B (requires OLLAMA_API_BASE_32B)
make aider-smart-status # ping the 32B endpoint before smart
```

This uses:
- `OLLAMA_API_BASE=http://127.0.0.1:11535`
- `--model ollama_chat/qwen2.5-coder:1.5b`
- `--map-tokens 0`
- `--timeout 60`

Pass-through args are supported with `AIDER_ARGS`, for example:
```sh
make aider-fast AIDER_ARGS="--message 'reply exactly READY'"
make aider-hard AIDER_ARGS="path/to/file.py"
make aider-smart AIDER_ARGS="--message 'reply READY for smart run' docs/aider-performance-guide.md"
```

### Micro lane for tiny autonomous tasks

The default fast micro lane is **already production-proven for anchored literal wording/comment replacements**. Treat that as the steady-state default until further promotions land:

- exactly one shell/bin file per probe (`shell/*.sh`, `bin/*.sh`, launcher scripts stay out unless already covered)
- literal or comment wording only — **no** `set`, `if`, `trap`, or other shell-control tokens
- explicit anchor syntax `file::<literal description>` plus an action verb (`replace`, `update`, `clarify`, …)
- immediate commit (or rollback) before attempting the next probe; the helper enforces a clean tree

When you only need a one- or two-file patch and want strict guard rails, use:

```sh
make aider-micro-help
make aider-micro-safe \
  AIDER_MICRO_MESSAGE="shell/common.sh::extract_session add guard for blank ids" \
  AIDER_MICRO_FILES="shell/common.sh"
```

This helper enforces:
- clean working tree requirement
- maximum two repo-relative files
- automatic `make quick`
- failure if aider touches any other file or produces no change
- supervisor artifacts under `artifacts/aider_runs/` for audit
- message must explicitly name the target file(s) and include a concrete action verb
- only code-adjacent files (`shell/`, `src/`, `tests/`, `bin/`, `config/`, `Makefile`, select scripts) are allowed; Markdown/README edits should use docs-specific flows

Recommended starter tasks for fast lane:
- anchor to a single function or literal (e.g., “tests/mock_login_flow.sh::SUCCESS replace literal SUCCESS with PASS”)
- comment-only or docstring additions in `shell/` or `src/`
- guard clauses or simple string replacements in shell helpers

To stay inside the proven lane, start from `templates/safe-literal-probe-template.msg` (see [docs/safe-literal-probes.md](safe-literal-probes.md)) and customize the quoted literal + file anchor before each run. Pair it with `bin/aider_micro.sh` so every probe documents its exact literal intent.

### Stage RAG-1 planning + telemetry

1. Run `bin/stage_rag1_plan_probe.py --stage stage4 --top 6 -- "describe literal"` to retrieve candidate anchors before editing the probe message.
2. Enter the file + line range that you plan to touch so the helper logs it under `artifacts/stage_rag1/usage.jsonl`.
3. After a Stage-4 battery, run `bin/stage_rag1_metrics.py --window 40` to summarize how many logged probes overlapped with guard failures (`literal_replace_missing_old`, `missing_file_ref`, `missing_anchor`) and how many preflight rejections (`literal_shell_risky`, `prompt_contract_rejection`, etc.) were captured in `artifacts/micro_runs/events.jsonl`.

This keeps the planning assistance “read-only” while giving us measurable signals on whether retrieval is reducing literal misses, wrong-file probes, and anchor mistakes.

### Stage-4 promotion decision (Apr 2026)

Latest telemetry (`python3 bin/stage_rag1_metrics.py --window 20`) logged 17 Stage-4 planning events with **zero guard failures** across the five tracked signatures, while the preflight event log still reports `literal_replace_missing_old` and `literal_shell_risky` at 10 % each. Based on that evidence plus the standing Stage-4 battery:

- **Promotable task shapes (production, Stage 3 default):** single-file literal or comment edits covering one or two adjacent lines, anchored with `<file>::<token>` and logged through Stage RAG-1 before launch. These are the only shapes demonstrating clean guard metrics.
- **Constrained-but-allowed (experimental, requires explicit Stage RAG logs + micro lane):** same as above but with explicit “fallback” notes when you expect a literal re-sync. Treat them as Stage-3 jobs with extra scrutiny; no multi-line expansion yet.
- **Boundary-only rejection probes (remain in `bin/micro_lane_stage4.sh`):**
  - `literal three-line` → `aider_exit` (status 124) every run.
  - `comment pair` → `no_change` (guarded) every run.
  - `literal miss` → `literal_replace_missing_old`.
  - `shell risky` → `literal_shell_risky`.

Result: **Stage 3 stays the production default**; Stage-4 remains an experimental boundary pack whose job is to prove the guard still rejects the scenarios above. Keep those four probes in the regression pack unchanged so we continue exercising the metrics pipeline.

Rejected patterns:
- vague wording like “clarify docs” or “polish README”
- markdown edits without `<file>::<token>` anchor
- multi-section doc updates
- multi-file refactors beyond two files

## 4. Validation & Artifacts
- Guard enforces file scope, diff size, forbidden globs, root limits, and runs validation commands. Results saved under `artifacts/aider_runs/` with failure context.
- Fast lane pings `OLLAMA_API_BASE` before launching; failure will mention unreachable endpoint unless you set `AIDER_LOCAL_SKIP_PING=1`.
- If guard fails twice, escalate to Codex with the artifact path and failure_code.
- Manual review still occurs before commit; reference the guard artifact in summaries.

## 5. Failure Handling
| Failure | Action |
|---------|--------|
| Scope violation (extra files / forbidden globs / extra roots) | Use guard artifact to identify offenders, split task or adjust file list, rerun once. |
| Diff budget exceeded | Decompose into smaller patches; guard artifact reports lines changed. |
| Partial edit / missing files | Annotate missing pieces, shrink scope, rerun Aider or hand-edit. |
| Noisy or off-target diff | Reject immediately, tighten brief with explicit deny list or adjust class. |
| Validation failure | Save logs from guard artifact, revert patch if necessary, diagnose locally before another Aider call. |

## 6. Anti-Patterns (Never do these)
- “Improve” or “refactor” without measurable success metrics or class fit.
- Delegating debugging/planning/investigation to Aider.
- Skipping guard or validations because the diff “looks small”.
- Allowing Aider to touch `config/**`, `systemd/**`, `secrets/**`, or `policies/**` unless Codex handles manually.
- Accepting patches without referencing guard artifacts.

Keep this guide paired with `AGENTS.md` and reference it whenever Codex prepares a tactical task.
