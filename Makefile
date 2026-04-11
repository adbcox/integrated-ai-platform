SHELL := /bin/sh

.PHONY: check check-shell check-python quick quick-shell quick-python test-offline test-changed-offline remote-prepare remote-finalize aider-start-task aider-handoff aider-finalize aider-capture-feedback aider-export-training aider-loop preflight-normalization-guard workflow-mode-show workflow-mode-list workflow-mode-validate workflow-mode-tactical workflow-mode-codex-assist workflow-mode-codex-investigate workflow-mode-codex-failure escalation-index-tail local-model-eval local-model-eval-json local-model-plan local-model-plan-json

check: check-shell check-python
	@echo "PASS: make check complete."

check-shell:
	@./validate_shell.sh

check-python:
	@echo "[python] Syntax-checking top-level Python files..."
	@find . -maxdepth 1 -type f -name '*.py' | sort | while IFS= read -r file; do \
		python3 -m py_compile "$$file"; \
		echo "OK: $${file#./}"; \
	done

quick:
	@./bin/quick_check.sh --all
	@echo "PASS: make quick complete."

quick-shell:
	@./bin/quick_check.sh --shell-only

quick-python:
	@./bin/quick_check.sh --python-only

test-offline:
	@./tests/run_offline_scenarios.sh

test-changed-offline:
	@./tests/run_changed_offline.sh

remote-prepare:
	@echo "Usage: ./bin/remote_prepare.sh --task-file <path> --name <task> --include <file> [--include <file>...]"

remote-finalize:
	@./bin/remote_finalize.sh --offline changed

aider-start-task:
	@echo "Usage: ./bin/aider_start_task.sh --name <task-name> [--goal <text>]"

aider-handoff:
	@echo "Usage: ./bin/aider_handoff.sh --task-file <path> [--name <task>] [--include <file>...]"

aider-finalize:
	@./bin/aider_finalize.sh

aider-capture-feedback:
	@echo "Usage: ./bin/aider_capture_feedback.sh --name <task-name> [--summary <path>] [--outcome <path>] [--checks <path>]"

aider-export-training:
	@./bin/aider_export_training_jsonl.sh

aider-loop:
	@echo "Usage: WORKFLOW_MODE=<mode> ./bin/aider_loop.sh --name <task-name> [--goal <text>] [--dry-run]"
	@echo "Modes: tactical | codex-assist | codex-investigate | codex-failure"

preflight-normalization-guard:
	@./bin/preflight_normalization_guard.sh

workflow-mode-show:
	@./bin/workflow_mode.sh show

workflow-mode-list:
	@./bin/workflow_mode.sh list

workflow-mode-validate:
	@./bin/workflow_mode.sh validate

workflow-mode-tactical:
	@echo "export WORKFLOW_MODE=tactical"

workflow-mode-codex-assist:
	@echo "export WORKFLOW_MODE=codex-assist"

workflow-mode-codex-investigate:
	@echo "export WORKFLOW_MODE=codex-investigate"

workflow-mode-codex-failure:
	@echo "export WORKFLOW_MODE=codex-failure"

escalation-index-tail:
	@tail -n 20 artifacts/escalations/index.jsonl 2>/dev/null || echo "No escalation index yet: artifacts/escalations/index.jsonl"

local-model-eval:
	@./bin/evaluate_escalations.py --write-report

local-model-eval-json:
	@./bin/evaluate_escalations.py --json-only --write-report

local-model-plan:
	@./bin/evaluate_escalations.py --write-report >/dev/null
	@./bin/plan_local_model_improvements.py --write-plan

local-model-plan-json:
	@./bin/evaluate_escalations.py --write-report >/dev/null
	@./bin/plan_local_model_improvements.py --json-only --write-plan
