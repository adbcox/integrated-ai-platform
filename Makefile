SHELL := /bin/sh

.PHONY: check check-shell check-python quick quick-shell quick-python test-offline test-changed-offline remote-prepare remote-finalize aider-start-task aider-handoff aider-finalize aider-capture-feedback aider-export-training aider-loop

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
	@echo "Usage: ./bin/aider_loop.sh --name <task-name> [--goal <text>] [--dry-run]"
