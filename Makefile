SHELL := /bin/sh

.PHONY: check check-shell check-python quick quick-shell quick-python test-offline test-changed-offline remote-prepare remote-finalize aider-start-task aider-handoff aider-finalize aider-capture-feedback aider-export-training aider-loop aider-run aider-bugfix-small aider-refactor-narrow aider-test-repair aider-lint-fix aider-docs-sync aider-typed-cleanup aider-targeted-feature-patch aider-fast aider-hard preflight-normalization-guard workflow-mode-show workflow-mode-list workflow-mode-validate workflow-mode-tactical workflow-mode-codex-assist workflow-mode-codex-investigate workflow-mode-codex-failure escalation-index-tail local-model-eval local-model-eval-json local-model-plan local-model-plan-json local-model-rules-refresh local-model-rules-show local-model-route local-task-intake local-front-door local-model-train-plan local-model-train-plan-json prompt-rule-plan prompt-rule-plan-json assess-candidate-class codex51-benchmark codex51-benchmark-json codex51-campaign-list codex51-campaign-run codex51-campaign-batch codex51-curation-export codex51-curation-export-json codex51-learning-loop codex51-learning-loop-json

.PHONY: aider-docs-micro aider-test-micro aider-shell-micro aider-lint-micro aider-smart aider-smart-status aider-bench-report aider-bench-compare aider-bench-models aider-micro-safe

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

# Automated Aider flows
AIDER_CLASS ?= bugfix-small
AIDER_NAME ?= aider-task
AIDER_OBJECTIVE ?=
AIDER_FILES ?=
AIDER_FILE_ARGS = $(foreach f,$(AIDER_FILES),--file $(f))

aider-run:
	@[ -n "$(AIDER_OBJECTIVE)" ] || { echo "AIDER_OBJECTIVE is required"; exit 1; }
	@[ -n "$(AIDER_FILES)" ] || { echo "AIDER_FILES is required"; exit 1; }
	@./bin/aider_task_runner.py --class "$(AIDER_CLASS)" --name "$(AIDER_NAME)" --objective "$(AIDER_OBJECTIVE)" $(AIDER_FILE_ARGS)

aider-bugfix-small:
	@$(MAKE) aider-run AIDER_CLASS=bugfix-small

aider-refactor-narrow:
	@$(MAKE) aider-run AIDER_CLASS=refactor-narrow

aider-test-repair:
	@$(MAKE) aider-run AIDER_CLASS=test-repair

aider-lint-fix:
	@$(MAKE) aider-run AIDER_CLASS=lint-fix

aider-docs-sync:
	@$(MAKE) aider-run AIDER_CLASS=docs-sync

aider-typed-cleanup:
	@$(MAKE) aider-run AIDER_CLASS=typed-cleanup

aider-targeted-feature-patch:
	@$(MAKE) aider-run AIDER_CLASS=targeted-feature-patch
	@echo "Modes: tactical | codex-assist | codex-investigate | codex-failure"

AIDER_ARGS ?=

aider-fast:
	@bash bin/aider_local.sh $(AIDER_ARGS)

aider-hard:
	@bash bin/aider_local.sh --hard $(AIDER_ARGS)

aider-smart:
	@bash bin/aider_local.sh --smart $(AIDER_ARGS)

aider-smart-status:
	@bash bin/aider_local.sh --smart-status

aider-bench-report:
	@python3 bin/aider_benchmark.py --report

aider-bench-models:
	@python3 bin/aider_benchmark.py --models

aider-bench-compare:
	@if [ -z "$(SCENARIO)" ]; then \
		echo "SCENARIO is required, e.g. make aider-bench-compare SCENARIO=single-file-edit"; \
		exit 1; \
	fi
	@python3 bin/aider_benchmark.py --compare "$(SCENARIO)"

AIDER_AUTO_FILES ?=

aider-auto:
	@[ -n "$(AIDER_OBJECTIVE)" ] || { echo "AIDER_OBJECTIVE is required"; exit 1; }
	@[ -n "$(AIDER_AUTO_FILES)" ] || { echo "AIDER_AUTO_FILES is required"; exit 1; }
	@./bin/aider_auto_route.py --name "$(AIDER_NAME)" --objective "$(AIDER_OBJECTIVE)" $(foreach f,$(AIDER_AUTO_FILES),--file $(f))

aider-docs-micro:
	@$(MAKE) aider-docs-sync AIDER_OBJECTIVE="$(or $(AIDER_OBJECTIVE),Update docs to match behavior)" AIDER_FILES="$(AIDER_FILES)"

aider-test-micro:
	@$(MAKE) aider-test-repair AIDER_OBJECTIVE="$(or $(AIDER_OBJECTIVE),Stabilize failing tests)" AIDER_FILES="$(AIDER_FILES)"

aider-shell-micro:
	@$(MAKE) aider-bugfix-small AIDER_OBJECTIVE="$(or $(AIDER_OBJECTIVE),Patch shell helper)" AIDER_FILES="$(AIDER_FILES)"

aider-lint-micro:
	@$(MAKE) aider-lint-fix AIDER_OBJECTIVE="$(or $(AIDER_OBJECTIVE),Apply lint fixes)" AIDER_FILES="$(AIDER_FILES)"

AIDER_MICRO_MESSAGE ?=
AIDER_MICRO_MESSAGE_FILE ?=
AIDER_MICRO_FILES ?=

.PHONY: aider-micro-help
aider-micro-help:
	@echo "Micro lane requirements:" && \
	 echo "  make aider-micro-safe AIDER_MICRO_MESSAGE=\"file.sh::token add ...\" AIDER_MICRO_FILES=\"shell/file.sh\"" && \
	 echo "  - Message must anchor each file: e.g. shell/common.sh::extract_session" && \
	 echo "  - Only one or two code-adjacent files" && \
	 echo "  - Doc/README edits will be rejected" && \
	 echo "  - Alternatively set AIDER_MICRO_MESSAGE_FILE=path/to/prompt.txt"

aider-micro-safe:
	@if [ -z "$(AIDER_MICRO_MESSAGE)" ] && [ -z "$(AIDER_MICRO_MESSAGE_FILE)" ]; then \
		echo "AIDER_MICRO_MESSAGE or AIDER_MICRO_MESSAGE_FILE is required"; exit 1; \
	  fi
	@[ -n "$(AIDER_MICRO_FILES)" ] || { echo "AIDER_MICRO_FILES is required (one or two repo-relative files)"; exit 1; }
	@FILES="$(strip $(AIDER_MICRO_FILES))"; \
		set -- $$FILES; \
		if [ $$# -gt 2 ]; then \
			echo "ERROR: aider-micro-safe supports at most two files"; exit 1; \
		fi; \
		if [ -n "$(AIDER_MICRO_MESSAGE_FILE)" ]; then \
			if [ ! -f "$(AIDER_MICRO_MESSAGE_FILE)" ]; then \
				echo "ERROR: message file $(AIDER_MICRO_MESSAGE_FILE) not found"; exit 1; \
			fi; \
			MICRO_MSG=$$(cat "$(AIDER_MICRO_MESSAGE_FILE)"); \
		else \
			MICRO_MSG="$(AIDER_MICRO_MESSAGE)"; \
		fi; \
		bash bin/aider_micro.sh "$$MICRO_MSG" "$$@"

.PHONY: micro-lane-regression micro-lane-stage6 level10-promote
micro-lane-regression:
	@./bin/micro_lane_regression.sh

micro-lane-stage6:
	@./bin/micro_lane_stage6.sh

level10-promote:
	@python3 ./bin/level10_promote.py --manifest ./config/promotion_manifest.json

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

local-model-rules-refresh:
	@./bin/evaluate_escalations.py --write-report >/dev/null
	@./bin/plan_local_model_improvements.py --write-plan >/dev/null
	@./bin/generate_local_routing_rules.py

local-model-rules-show:
	@sed -n '1,240p' policies/local-routing-rules.json 2>/dev/null || echo "No rules file yet. Run: make local-model-rules-refresh"

local-model-route:
	@if [ -n "$$TASK_CLASS" ]; then \
		./bin/select_workflow_mode.py --class "$$TASK_CLASS"; \
	elif [ -n "$$TRIGGER" ] && [ -n "$$FIX_PATTERN" ]; then \
		./bin/select_workflow_mode.py --trigger "$$TRIGGER" --fix-pattern "$$FIX_PATTERN"; \
	else \
		echo "Usage: TASK_CLASS='<trigger> | <fix_pattern>' make local-model-route"; \
		echo "   or: TRIGGER='<trigger>' FIX_PATTERN='<fix_pattern>' make local-model-route"; \
	fi

local-task-intake:
	@if [ -z "$$TASK_NAME" ] || [ -z "$$TASK_GOAL" ]; then \
		echo "Usage: TASK_NAME='<task>' TASK_GOAL='<goal>' [TASK_CLASS='<trigger> | <fix_pattern>'] make local-task-intake"; \
	else \
		set -- ./bin/local_task_intake.py --name "$$TASK_NAME" --goal "$$TASK_GOAL"; \
		if [ -n "$$TASK_CLASS" ]; then set -- "$$@" --class "$$TASK_CLASS"; fi; \
		if [ -n "$$TRIGGER" ]; then set -- "$$@" --trigger "$$TRIGGER"; fi; \
		if [ -n "$$FIX_PATTERN" ]; then set -- "$$@" --fix-pattern "$$FIX_PATTERN"; fi; \
		if [ -n "$$ESCALATE" ]; then set -- "$$@" --escalate "$$ESCALATE"; fi; \
		"$$@"; \
	fi

local-front-door:
	@if [ -z "$$TASK_NAME" ] || [ -z "$$TASK_GOAL" ]; then \
		echo "Usage: TASK_NAME='<task>' TASK_GOAL='<goal>' [TASK_CLASS='<trigger> | <fix_pattern>'] make local-front-door"; \
	else \
		set -- ./bin/local_front_door.py --name "$$TASK_NAME" --goal "$$TASK_GOAL"; \
		if [ -n "$$TASK_CLASS" ]; then set -- "$$@" --class "$$TASK_CLASS"; fi; \
		if [ -n "$$TRIGGER" ]; then set -- "$$@" --trigger "$$TRIGGER"; fi; \
		if [ -n "$$FIX_PATTERN" ]; then set -- "$$@" --fix-pattern "$$FIX_PATTERN"; fi; \
		if [ -n "$$ESCALATE" ]; then set -- "$$@" --escalate "$$ESCALATE"; fi; \
		if [ -n "$$TASK_ID" ]; then set -- "$$@" --task-id "$$TASK_ID"; fi; \
		"$$@"; \
	fi

local-model-train-plan:
	@./bin/plan_training_distillation.py --write-plan

local-model-train-plan-json:
	@./bin/plan_training_distillation.py --json-only --write-plan

codex51-benchmark:
	@./bin/codex51_replacement_benchmark.py --write-report

codex51-benchmark-json:
	@./bin/codex51_replacement_benchmark.py --json-only --write-report

codex51-campaign-list:
	@./bin/local_replacement_campaign.py list

codex51-campaign-run:
	@if [ -z "$$TASK_ID" ]; then \
		echo "Usage: TASK_ID='<campaign task id>' [PROFILE=normal] [DRY_RUN=1] make codex51-campaign-run"; \
		exit 1; \
	fi
	@set -- ./bin/local_replacement_campaign.py run --task-id "$$TASK_ID"; \
	if [ -n "$$PROFILE" ]; then set -- "$$@" --profile "$$PROFILE"; fi; \
	if [ "$$DRY_RUN" = "0" ]; then set -- "$$@" --no-dry-run; else set -- "$$@" --dry-run; fi; \
	"$$@"

codex51-campaign-batch:
	@set -- ./bin/local_replacement_campaign.py run-batch; \
	if [ -n "$$PROFILE" ]; then set -- "$$@" --profile "$$PROFILE"; fi; \
	if [ "$$DRY_RUN" = "0" ]; then set -- "$$@" --no-dry-run; else set -- "$$@" --dry-run; fi; \
	"$$@"

codex51-curation-export:
	@./bin/codex51_curation_export.py

codex51-curation-export-json:
	@./bin/codex51_curation_export.py --json-only

codex51-learning-loop:
	@python3 ./bin/codex51_learning_loop.py --write-report

codex51-learning-loop-json:
	@python3 ./bin/codex51_learning_loop.py --write-report --json-only

prompt-rule-plan:
	@./bin/plan_training_distillation.py --write-plan >/dev/null
	@./bin/plan_prompt_rule_tuning.py --write-plan

prompt-rule-plan-json:
	@./bin/plan_training_distillation.py --write-plan >/dev/null
	@./bin/plan_prompt_rule_tuning.py --json-only --write-plan

assess-candidate-class:
	@if [ -n "$$CLASS" ]; then \
		./bin/assess_candidate_class.py --class "$$CLASS"; \
	elif [ -n "$$TRIGGER" ] && [ -n "$$FIX_PATTERN" ]; then \
		./bin/assess_candidate_class.py --trigger "$$TRIGGER" --fix-pattern "$$FIX_PATTERN"; \
	else \
		echo "Usage: CLASS='trigger | fix' make assess-candidate-class"; \
		echo "   or: TRIGGER='...' FIX_PATTERN='...' make assess-candidate-class"; \
	fi

.PHONY: governance-check governance-write governance-test

governance-write:
	@python3 ./bin/governance_reconcile.py --write

governance-check:
	@python3 ./bin/governance_reconcile.py --check --fail-on-diff

governance-test:
	@python3 -m unittest -v tests.test_governance_reconcile tests.test_governance_phase0_closure tests.test_governance_phase1_ratification tests.test_governance_phase2_adoption tests.test_governance_tactical_unlock tests.test_governance_next_class

.PHONY: governance-phase0-close governance-phase1-ratify governance-phase2-extract governance-unlock-eval governance-ratify

governance-phase0-close:
	@python3 ./bin/governance_phase0_closer.py --write --fail-on-diff

governance-phase1-ratify:
	@python3 ./bin/governance_phase1_ratifier.py --write --fail-on-diff

governance-phase2-extract:
	@python3 ./bin/governance_phase2_extractor.py --write --fail-on-diff

governance-unlock-eval:
	@python3 ./bin/governance_unlock_evaluator.py --write --fail-on-diff

governance-ratify: governance-phase0-close governance-phase1-ratify governance-phase2-extract governance-unlock-eval
	@python3 ./bin/governance_phase0_closer.py --check --fail-on-diff
	@python3 ./bin/governance_phase1_ratifier.py --check --fail-on-diff
	@python3 ./bin/governance_phase2_extractor.py --check --fail-on-diff
	@python3 ./bin/governance_unlock_evaluator.py --check --fail-on-diff

.PHONY: capability-phase2-run capability-phase2-record

capability-phase2-run:
	@python3 -m pytest -q tests/capability/test_phase2_innerloop_closure.py tests/capability/test_phase2_innerloop_closure_negative.py

capability-phase2-record:
	@python3 ./bin/governance_phase2_evidence_recorder.py --write --fail-on-diff

.PHONY: phase1-runtime-test phase1-runtime-validate

phase1-runtime-test:
	@python3 -m unittest -v \
		tests.test_inference_gateway \
		tests.test_model_profiles \
		tests.test_runtime_workspace_contract \
		tests.test_runtime_artifact_service \
		tests.test_local_command_runner \
		tests.test_phase1_local_runtime_validation

phase1-runtime-validate:
	@python3 ./artifacts/phase1_local_runtime_validation_report.py

.PHONY: phase2-schema-test phase2-schema-validate

phase2-schema-test:
	@python3 -m unittest \
		tests.test_canonical_session_schema \
		tests.test_canonical_job_schema \
		tests.test_tool_action_observation_contract \
		tests.test_tool_contract_builders \
		tests.test_phase2_session_bundle \
		tests.test_phase2_schema_entry_validation

phase2-schema-validate:
	@python3 ./artifacts/phase2_schema_entry_validation_report.py

.PHONY: phase2-runtime-wire-test phase2-runtime-wire-validate

phase2-runtime-wire-test:
	@python3 -m unittest \
		tests.test_worker_runtime_phase2_integration \
		tests.test_state_store_phase2_payload \
		tests.test_runtime_validation_pack_phase2 \
		tests.test_phase2_runtime_wire_validation

phase2-runtime-wire-validate:
	@python3 ./artifacts/phase2_runtime_wire_validation_report.py


.PHONY: phase2-tool-impl-test phase2-tool-impl-validate

phase2-tool-impl-test:
	@python3 -m unittest -v \
		tests.test_worker_runtime_typed_tool_read_file \
		tests.test_worker_runtime_typed_tool_list_dir \
		tests.test_worker_runtime_typed_tool_git_diff \
		tests.test_worker_runtime_typed_tool_run_tests \
		tests.test_worker_runtime_typed_tool_dispatcher \
		tests.test_phase2_tool_impl_validation

phase2-tool-impl-validate:
	@python3 ./artifacts/phase2_tool_impl_validation_report.py

.PHONY: phase2-tool-impl-2-test phase2-tool-impl-2-validate

phase2-tool-impl-2-test:
	@python3 -m unittest -v \
		tests.test_worker_runtime_typed_tool_search \
		tests.test_worker_runtime_typed_tool_repo_map \
		tests.test_worker_runtime_typed_tool_dispatcher_phase2_tool_impl_2 \
		tests.test_phase2_tool_impl_2_validation

phase2-tool-impl-2-validate:
	@python3 ./artifacts/phase2_tool_impl_2_validation_report.py

.PHONY: phase2-tool-impl-3-test phase2-tool-impl-3-validate

phase2-tool-impl-3-test:
	@python3 -m unittest -v \
		tests.test_worker_runtime_typed_tool_apply_patch \
		tests.test_worker_runtime_typed_tool_publish_artifact \
		tests.test_worker_runtime_typed_tool_dispatcher_phase2_tool_impl_3 \
		tests.test_phase2_tool_impl_3_validation

phase2-tool-impl-3-validate:
	@PYTHONPATH=. python3 ./artifacts/phase2_tool_impl_3_validation_report.py

.PHONY: phase2-manager-wire-test phase2-manager-wire-validate

phase2-manager-wire-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase2_manager_wire \
		tests.test_runtime_validation_pack_phase2_manager_wire \
		tests.test_phase2_manager_wire_validation

phase2-manager-wire-validate:
	@python3 ./artifacts/phase2_manager_wire_validation_report.py

.PHONY: phase2-manager-decision-test phase2-manager-decision-validate

phase2-manager-decision-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase2_manager_decision \
		tests.test_runtime_validation_pack_phase2_manager_decision \
		tests.test_phase2_manager_decision_validation

phase2-manager-decision-validate:
	@python3 ./artifacts/phase2_manager_decision_validation_report.py

.PHONY: phase2-exit-wire-test phase2-exit-wire-validate

phase2-exit-wire-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_phase2_exit_wire \
		tests.test_phase2_exit_wire_validation

phase2-exit-wire-validate:
	@PYTHONPATH=. python3 ./artifacts/phase2_exit_wire_validation_report.py

.PHONY: phase2-probe-wire-test phase2-probe-wire-validate

phase2-probe-wire-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_typed_tool_probe \
		tests.test_phase2_probe_wire_validation

phase2-probe-wire-validate:
	@PYTHONPATH=. python3 ./artifacts/phase2_probe_wire_validation_report.py

.PHONY: phase2-results-wire-test phase2-results-wire-validate

phase2-results-wire-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase2_results_wire \
		tests.test_phase2_results_wire_validation

phase2-results-wire-validate:
	@PYTHONPATH=. python3 ./artifacts/phase2_results_wire_validation_report.py

.PHONY: phase3-retrieval-probe-test phase3-retrieval-probe-validate

phase3-retrieval-probe-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_retrieval_probe \
		tests.test_phase3_retrieval_probe_validation

phase3-retrieval-probe-validate:
	@PYTHONPATH=. python3 ./artifacts/phase3_retrieval_probe_validation_report.py

.PHONY: phase3-retrieval-consume-test phase3-retrieval-consume-validate

phase3-retrieval-consume-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_retrieval_consume \
		tests.test_phase3_retrieval_consume_validation

phase3-retrieval-consume-validate:
	@PYTHONPATH=. python3 ./artifacts/phase3_retrieval_consume_validation_report.py

.PHONY: phase3-read-after-retrieval-test phase3-read-after-retrieval-validate

phase3-read-after-retrieval-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_read_after_retrieval \
		tests.test_phase3_read_after_retrieval_validation

phase3-read-after-retrieval-validate:
	@PYTHONPATH=. python3 ./artifacts/phase3_read_after_retrieval_validation_report.py

.PHONY: phase3-read-content-surface-test phase3-read-content-surface-validate

phase3-read-content-surface-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_read_content \
		tests.test_phase3_read_content_surface_validation

phase3-read-content-surface-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_read_content_surface_validation_report.py

.PHONY: phase3-symbol-index-test phase3-symbol-index-validate

phase3-symbol-index-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_symbol_index \
		tests.test_phase3_symbol_index_validation

phase3-symbol-index-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_symbol_index_validation_report.py

.PHONY: phase3-context-bundle-test phase3-context-bundle-validate

phase3-context-bundle-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_context_bundle \
		tests.test_phase3_context_bundle_validation

phase3-context-bundle-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_context_bundle_validation_report.py

.PHONY: phase3-context-inject-test phase3-context-inject-validate

phase3-context-inject-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_context_inject \
		tests.test_phase3_context_inject_validation

phase3-context-inject-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_context_inject_validation_report.py

.PHONY: phase3-inference-response-test phase3-inference-response-validate

phase3-inference-response-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_inference_response \
		tests.test_phase3_inference_response_validation

phase3-inference-response-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_inference_response_validation_report.py

.PHONY: phase3-next-action-test phase3-next-action-validate

phase3-next-action-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_next_action \
		tests.test_phase3_next_action_validation

phase3-next-action-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_next_action_validation_report.py

.PHONY: phase3-exit-wire-test phase3-exit-wire-validate

phase3-exit-wire-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_phase3_exit_wire \
		tests.test_phase3_exit_wire_validation

phase3-exit-wire-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_exit_wire_validation_report.py

.PHONY: phase3-followon-select-test phase3-followon-select-validate

phase3-followon-select-test:
	@python3 -m unittest -v \
		tests.test_framework_control_plane_phase3_followon_select \
		tests.test_phase3_followon_select_validation

phase3-followon-select-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_followon_select_validation_report.py

.PHONY: phase3-auto-continue-test phase3-auto-continue-validate

phase3-auto-continue-test:
	@python3 -m unittest -v \
		tests.test_bin_framework_control_plane_phase3_auto_continue \
		tests.test_phase3_auto_continue_validation

phase3-auto-continue-validate:
	@PYTHONPATH=. python3 \
		./artifacts/phase3_auto_continue_validation_report.py

PHASE3_QUERY ?= _execute_job
PHASE3_INFERENCE_MODE ?= ollama

.PHONY: phase3-query

phase3-query:
	@PYTHONPATH=. python3 bin/framework_control_plane.py \
		--task-template retrieval_probe \
		--phase3-query $(PHASE3_QUERY) \
		--inference-mode $(PHASE3_INFERENCE_MODE)
	@PYTHONPATH=. python3 bin/framework_control_plane.py \
		--task-template read_after_retrieval \
		--inference-mode $(PHASE3_INFERENCE_MODE)
	@PYTHONPATH=. python3 bin/framework_control_plane.py \
		--task-template context_bundle_inference_probe \
		--inference-mode $(PHASE3_INFERENCE_MODE)

PHASE3_EDIT_PLAN_INFERENCE_MODE ?= ollama

.PHONY: phase3-edit-plan

phase3-edit-plan:
	@PYTHONPATH=. python3 bin/framework_control_plane.py \
		--task-template phase3_edit_plan_probe \
		--inference-mode $(PHASE3_EDIT_PLAN_INFERENCE_MODE)

.PHONY: phase3-validate-edit-plan

phase3-validate-edit-plan:
	@PYTHONPATH=. python3 bin/framework_control_plane.py \
		--task-template phase3_validate_edit_plan_probe
