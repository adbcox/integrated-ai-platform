#!/usr/bin/env python3
"""Framework control-plane entrypoint for local bounded parallel execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework import (
    EscalationPolicy,
    Job,
    JobAction,
    JobClass,
    JobPriority,
    LearningHooks,
    RetryPolicy,
    Scheduler,
    StateStore,
    ValidationRequirement,
    WorkTarget,
    build_inference_adapter,
    get_backend_profile,
    select_backend_profile_auto,
)
from framework.job_schema import LearningHooksConfig
from framework.framework_control_plane import (
    _phase2_manager_extract,
    _phase2_manager_decision,
    _phase2_extract_typed_results,
    _phase2_derive_read_targets,
    _phase2_retrieval_summary,
    _phase3_extract_read_content,
    _phase3_read_content_summary,
    _phase3_extract_symbol_index,
    _phase3_assemble_context_bundle,
    _phase3_build_context_prompt,
    _phase3_extract_inference_response,
    _phase3_derive_next_action,
    _phase3_select_followon_template,
    _phase3_build_recommendation,
    _phase3_build_edit_plan,
    _phase3_validate_edit_plan,
    _phase3_build_stage3_manager_invocation,
)

DEFAULT_STATE_ROOT = REPO_ROOT / "artifacts" / "framework"
DEFAULT_LEARNING_LATEST = DEFAULT_STATE_ROOT / "learning" / "latest.json"
DEFAULT_CODE_LIBRARY_LATEST = REPO_ROOT / "artifacts" / "codex51" / "learning" / "code_library" / "latest.json"
DEFAULT_TRUSTED_PATTERNS_LATEST = REPO_ROOT / "artifacts" / "codex51" / "trusted_patterns" / "latest.json"
DEFAULT_REPLAY_QUEUE = REPO_ROOT / "artifacts" / "framework" / "replay_queue_latest.json"
DEFAULT_CODEX51_LEARNING_LATEST = REPO_ROOT / "artifacts" / "codex51" / "learning" / "latest.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run framework scheduler/worker local job flow")
    parser.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="Framework artifact root")
    parser.add_argument(
        "--learning-latest",
        default="",
        help=(
            "Path for framework learning snapshot output. "
            "Defaults to <state-root>/learning/latest.json to avoid overwriting Codex51 learning artifacts."
        ),
    )
    parser.add_argument(
        "--backend-profile",
        default="auto",
        choices=["auto", "mac_local", "threadripper_local", "multi_host_future"],
    )
    parser.add_argument("--inference-mode", default="heuristic", choices=["heuristic", "artifact_replay", "ollama", "claude_code_cli"])
    parser.add_argument("--inference-replay", default="", help="Artifact replay payload for inference adapter")
    parser.add_argument("--task-class", default=JobClass.FRAMEWORK_BOOTSTRAP.value, choices=[item.value for item in JobClass])
    parser.add_argument(
        "--task-template",
        default="none",
        choices=[
            "none",
            "learning_refresh",
            "benchmark_refresh",
            "campaign_artifact_processing",
            "validation_check_execution",
            "validation_check_inner_loop",
            "validation_check_tracked_inner_loop",
            "validation_check_tracked_multi_file_inner_loop",
            "validation_check_artifact_backed_multi_file_inner_loop",
            "trusted_pattern_refresh",
            "replay_queue_generation",
            "replay_queue_execution",
            "campaign_profile_matrix",
            "typed_tool_probe",
            "retrieval_probe",
            "read_after_retrieval",
            "context_bundle_probe",
            "context_bundle_inference_probe",
            "phase3_followon",
            "phase3_edit_plan_probe",
            "phase3_validate_edit_plan_probe",
            "phase3_apply_edit_plan_probe",
        ],
        help="Predefined real repo workflow template routed through framework execution.",
    )
    parser.add_argument(
        "--phase3-auto-continue",
        action="store_true",
        help=(
            "When set and phase3_next_action signals refine_retrieval or insufficient_context, "
            "perform a second scheduler pass with the selected follow-on template."
        ),
    )
    parser.add_argument(
        "--task-portfolio",
        default="none",
        choices=["none", "next5_high_value"],
        help="Submit a bounded portfolio of real framework jobs in one scheduler run.",
    )
    parser.add_argument("--replay-max-items", type=int, default=1, help="Max replay queue items to execute.")
    parser.add_argument(
        "--replay-execution-mode",
        default="dry_run",
        choices=["dry_run", "as_is"],
        help="Whether replay commands should be rewritten to dry-run or executed as-is.",
    )
    parser.add_argument(
        "--replay-queue-path",
        default=str(DEFAULT_REPLAY_QUEUE),
        help="Path to replay queue JSON artifact.",
    )
    parser.add_argument("--priority", default=JobPriority.P1.value, choices=[item.value for item in JobPriority])
    parser.add_argument("--shell-command", default="", help="Shell command to run inside repo root")
    parser.add_argument("--inference-prompt", default="", help="Prompt passed to inference adapter")
    parser.add_argument("--artifact-input", action="append", default=[], help="Artifact input file path")
    parser.add_argument("--requested-output", action="append", default=[], help="Expected output file path")
    parser.add_argument("--retry-budget", type=int, default=0)
    parser.add_argument("--retry-backoff-seconds", type=int, default=0)
    parser.add_argument("--auto-escalate", action="store_true")
    parser.add_argument("--wait-timeout-seconds", type=float, default=30.0)
    parser.add_argument(
        "--scheduler-replay-attempt-limit",
        type=int,
        default=2,
        help="Max scheduler replay attempts before dead-lettering stranded jobs.",
    )
    parser.add_argument(
        "--replay-pending",
        action="store_true",
        help="Replay pending/inflight persisted framework jobs before accepting new work.",
    )
    parser.add_argument(
        "--phase3-query",
        nargs="+",
        default=["_execute_job"],
        help="Query terms for the Phase 3 retrieval probe. Multiple words joined with spaces.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser.parse_args()


def _default_command() -> str:
    return (
        "python3 -c \"from pathlib import Path; "
        "p = Path('artifacts/framework/demo_output.txt'); "
        "p.parent.mkdir(parents=True, exist_ok=True); "
        "p.write_text('framework demo output\\n', encoding='utf-8')\""
    )


def _learning_refresh_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.LEARNING_ARTIFACT_SYNTHESIS.value,
        "shell_command": (
            "python3 bin/codex51_curation_export.py --json-only > artifacts/framework/curation_refresh_stdout.json && "
            "python3 bin/codex51_learning_loop.py --write-report --json-only "
            "> artifacts/framework/learning_refresh_stdout.json"
        ),
        "inference_prompt": (
            "Synthesize Codex51 learning artifacts from real benchmark/campaign/curation/traces. "
            "Keep execution bounded and artifact-first."
        ),
        "artifact_inputs": [
            "artifacts/codex51/benchmark/latest.json",
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/codex51/curation/training_examples.jsonl",
            "artifacts/manager6/traces.jsonl",
            "artifacts/manager6/plans",
        ],
        "requested_outputs": [
            "artifacts/codex51/curation/training_examples.jsonl",
            "artifacts/codex51/learning/latest.json",
            "artifacts/codex51/learning/latest.md",
            "artifacts/framework/curation_refresh_stdout.json",
            "artifacts/framework/learning_refresh_stdout.json",
            "artifacts/codex51/learning/code_library/latest.json",
        ],
    }


def _benchmark_refresh_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.BENCHMARK_ANALYSIS.value,
        "shell_command": (
            "python3 bin/codex51_replacement_benchmark.py --write-report --json-only "
            "> artifacts/framework/benchmark_refresh_stdout.json"
        ),
        "inference_prompt": (
            "Run Codex51 replacement benchmark analysis and publish latest benchmark artifacts "
            "for replacement-gate attribution."
        ),
        "artifact_inputs": [
            "config/codex51_replacement_benchmark.json",
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/codex51/attribution/latest.json",
            "artifacts/manager6/plans",
        ],
        "requested_outputs": [
            "artifacts/codex51/benchmark/latest.json",
            "artifacts/codex51/benchmark/latest.md",
            "artifacts/framework/benchmark_refresh_stdout.json",
        ],
    }


def _campaign_artifact_processing_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.CAMPAIGN_ARTIFACT_PROCESSING.value,
        "shell_command": (
            "python3 bin/codex51_attribution.py > artifacts/framework/campaign_attribution_stdout.json && "
            "python3 bin/codex51_quality.py > artifacts/framework/campaign_quality_stdout.json"
        ),
        "inference_prompt": (
            "Process existing campaign artifacts into attribution and first-attempt quality reports "
            "for manager and benchmark consumption."
        ),
        "artifact_inputs": [
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/manager6/plans",
            "artifacts/manager6/traces.jsonl",
        ],
        "requested_outputs": [
            "artifacts/codex51/attribution/latest.json",
            "artifacts/codex51/quality/latest.json",
            "artifacts/framework/campaign_attribution_stdout.json",
            "artifacts/framework/campaign_quality_stdout.json",
        ],
    }


def _validation_check_execution_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "make quick > artifacts/framework/validation_quick_stdout.txt",
        "inference_prompt": "Execute bounded repository validation checks and persist artifacts for audit/replay.",
        "permission_policy": {
            "allow_command_patterns": [r"^make\s+quick(\s+.*)?$"],
            "deny_command_patterns": [r"\brm\b\s+-rf\b"],
        },
        "artifact_inputs": [
            "Makefile",
            "bin/quick_check.sh",
            "artifacts/manager6/traces.jsonl",
        ],
        "requested_outputs": [
            "artifacts/framework/validation_quick_stdout.txt",
        ],
    }


def _validation_check_inner_loop_template() -> dict[str, Any]:
    target_file = "artifacts/framework/inner_loop_target.py"
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Run bounded edit-test-fix inner loop for validation execution. "
            "Repair a deterministic syntax failure and stop on successful validation."
        ),
        "permission_policy": {
            "allow_command_patterns": [
                r"^python3\s+-c\s+.*$",
                r"^python3\s+-m\s+py_compile\s+artifacts/framework/inner_loop_target\.py$",
            ],
            "allow_edit_path_patterns": [r"artifacts/framework/inner_loop_target\.py$"],
            "deny_command_patterns": [r"\brm\b\s+-rf\b"],
        },
        "artifact_inputs": [
            "framework/worker_runtime.py",
            "bin/framework_control_plane.py",
        ],
        "requested_outputs": [
            target_file,
        ],
        "inner_loop": {
            "enabled": True,
            "max_cycles": 2,
            "setup_command": (
                "python3 -c \"from pathlib import Path; p=Path('artifacts/framework/inner_loop_target.py'); "
                "p.parent.mkdir(parents=True, exist_ok=True); "
                "p.write_text('def value():\\n    return 1+\\n', encoding='utf-8')\""
            ),
            "validate_command": "python3 -m py_compile artifacts/framework/inner_loop_target.py",
            "repair_edits": [
                {
                    "path": target_file,
                    "find": "return 1+",
                    "replace": "return 1+1",
                }
            ],
        },
    }


def _validation_check_tracked_inner_loop_template() -> dict[str, Any]:
    tracked_file = REPO_ROOT / "framework" / "queue_types.py"
    tracked_rel = "framework/queue_types.py"
    baseline_text = tracked_file.read_text(encoding="utf-8")
    broken_text = baseline_text.replace("from dataclasses import dataclass, field", "from dataclasses import dataclass,", 1)
    baseline_sha = hashlib.sha256(baseline_text.encode("utf-8")).hexdigest()
    broken_sha = hashlib.sha256(broken_text.encode("utf-8")).hexdigest()
    setup_cmd = (
        "python3 -c \"from pathlib import Path; p=Path('framework/queue_types.py'); "
        "txt=p.read_text(encoding='utf-8'); "
        "needle='from dataclasses import dataclass, field'; "
        "assert needle in txt, 'tracked_setup_missing_needle'; "
        "p.write_text(txt.replace(needle, 'from dataclasses import dataclass,', 1), encoding='utf-8')\""
    )
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Run bounded tracked-source edit-test-fix loop with strict patch contracts and rollback support. "
            "Repair deterministic syntax break in framework/queue_types.py."
        ),
        "permission_policy": {
            "allow_command_patterns": [
                r"^python3\s+-c\s+.*$",
                r"^python3\s+-m\s+py_compile\s+framework/queue_types\.py$",
            ],
            "allow_edit_path_patterns": [r"/framework/queue_types\.py$"],
            "deny_command_patterns": [r"\brm\b\s+-rf\b"],
        },
        "artifact_inputs": [
            tracked_rel,
            "framework/worker_runtime.py",
            "framework/permission_engine.py",
        ],
        "requested_outputs": [tracked_rel],
        "inner_loop": {
            "enabled": True,
            "max_cycles": 2,
            "tracked_paths": [tracked_rel],
            "setup_command": setup_cmd,
            "validate_command": "python3 -m py_compile framework/queue_types.py",
            "repair_edits": [
                {
                    "path": tracked_rel,
                    "find": "from dataclasses import dataclass,",
                    "replace": "from dataclasses import dataclass, field",
                    "expected_before_sha256": broken_sha,
                    "expected_after_sha256": baseline_sha,
                }
            ],
        },
    }


def _validation_check_tracked_multi_file_inner_loop_template() -> dict[str, Any]:
    tool_file = REPO_ROOT / "framework" / "tool_system.py"
    permission_file = REPO_ROOT / "framework" / "permission_engine.py"
    tool_rel = "framework/tool_system.py"
    permission_rel = "framework/permission_engine.py"

    tool_baseline = tool_file.read_text(encoding="utf-8")
    permission_baseline = permission_file.read_text(encoding="utf-8")
    tool_broken = tool_baseline.replace('APPLY_EDIT = "apply_edit"', 'APPLY_EDIT = "apply_patch"', 1)
    permission_broken = permission_baseline.replace(
        '"apply_edit": ToolName.APPLY_EDIT.value,',
        '"apply_edit": "apply_patch",',
        1,
    )

    setup_cmd = (
        "python3 -c \"from pathlib import Path; "
        "tool=Path('framework/tool_system.py'); perm=Path('framework/permission_engine.py'); "
        "t=tool.read_text(encoding='utf-8'); p=perm.read_text(encoding='utf-8'); "
        "a='APPLY_EDIT = \\\"apply_edit\\\"'; b='\\\"apply_edit\\\": ToolName.APPLY_EDIT.value,'; "
        "assert a in t, 'multi_setup_tool_missing'; assert b in p, 'multi_setup_perm_missing'; "
        "tool.write_text(t.replace(a, 'APPLY_EDIT = \\\"apply_patch\\\"', 1), encoding='utf-8'); "
        "perm.write_text(p.replace(b, '\\\"apply_edit\\\": \\\"apply_patch\\\",', 1), encoding='utf-8')\""
    )
    validate_cmd = (
        "python3 -c \"from framework.tool_system import ToolName, ToolAction; "
        "from framework.permission_engine import PermissionEngine; "
        "assert ToolName.APPLY_EDIT.value == 'apply_edit'; "
        "engine=PermissionEngine(); "
        "decision=engine.evaluate("
        "action=ToolAction(job_id='v', tool=ToolName.APPLY_EDIT, arguments={'path':'/tmp/x'}), "
        "allowed_tools_actions=['apply_edit'], "
        "metadata={'permission_policy': {'allow_edit_path_patterns': ['.*']}}); "
        "assert decision.allowed, decision.reason\""
    )
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Run bounded coordinated multi-file edit-test-fix loop on tracked framework code "
            "with strict per-file hash contracts and conflict-aware stop semantics."
        ),
        "permission_policy": {
            "allow_command_patterns": [
                r"^python3\s+-c\s+.*$",
            ],
            "allow_edit_path_patterns": [
                r"/framework/tool_system\.py$",
                r"/framework/permission_engine\.py$",
            ],
            "deny_command_patterns": [r"\brm\b\s+-rf\b"],
        },
        "artifact_inputs": [
            tool_rel,
            permission_rel,
            "framework/worker_runtime.py",
        ],
        "requested_outputs": [tool_rel, permission_rel],
        "inner_loop": {
            "enabled": True,
            "coordinated_repairs": True,
            "max_cycles": 2,
            "tracked_paths": [tool_rel, permission_rel],
            "setup_command": setup_cmd,
            "validate_command": validate_cmd,
            "repair_edits": [
                {
                    "path": tool_rel,
                    "find": 'APPLY_EDIT = "apply_patch"',
                    "replace": 'APPLY_EDIT = "apply_edit"',
                    "expected_before_sha256": hashlib.sha256(tool_broken.encode("utf-8")).hexdigest(),
                    "expected_after_sha256": hashlib.sha256(tool_baseline.encode("utf-8")).hexdigest(),
                },
                {
                    "path": permission_rel,
                    "find": '"apply_edit": "apply_patch",',
                    "replace": '"apply_edit": ToolName.APPLY_EDIT.value,',
                    "expected_before_sha256": hashlib.sha256(permission_broken.encode("utf-8")).hexdigest(),
                    "expected_after_sha256": hashlib.sha256(permission_baseline.encode("utf-8")).hexdigest(),
                },
            ],
        },
    }


def _load_artifact_backed_failure_evidence() -> dict[str, Any]:
    fallback = {
        "plan_id": "",
        "task_id": "bootstrap-artifact-backed-multi-file",
        "query": "stage7 manager orchestration subplan split defer rescue",
        "failure_signature": "bootstrap_missing_learning_artifact",
        "target_paths": [
            "bin/stage_rag4_plan_probe.py",
            "bin/stage_rag6_plan_probe.py",
        ],
        "weak_signals": ["missing learning artifact on local node; using deterministic bootstrap evidence"],
        "source_artifact": str(DEFAULT_CODEX51_LEARNING_LATEST),
        "evidence_mode": "bootstrap_fallback",
    }
    if not DEFAULT_CODEX51_LEARNING_LATEST.exists():
        return fallback
    payload = json.loads(DEFAULT_CODEX51_LEARNING_LATEST.read_text(encoding="utf-8"))
    lessons = payload.get("lessons") if isinstance(payload, dict) else []
    if not isinstance(lessons, list):
        fallback["failure_signature"] = "invalid_learning_lessons_payload"
        fallback["weak_signals"] = ["learning artifact payload invalid; using deterministic bootstrap evidence"]
        return fallback

    target_pair = {"bin/stage_rag6_plan_probe.py", "bin/stage_rag4_plan_probe.py"}
    for row in lessons:
        if not isinstance(row, dict):
            continue
        task = row.get("task") if isinstance(row.get("task"), dict) else {}
        attempted = row.get("attempted") if isinstance(row.get("attempted"), dict) else {}
        wrong = row.get("what_initially_went_wrong") or []
        signature = (row.get("prevention") or {}).get("failure_signature")
        targets = set(str(path) for path in (attempted.get("target_paths") or []) if str(path))
        if task.get("task_class") != "multi_file_orchestration":
            continue
        if not target_pair.issubset(targets):
            continue
        if "first attempt did not fully succeed" not in wrong:
            continue
        if not signature:
            continue
        evidence_mode = "artifact_backed"
        return {
            "plan_id": str(row.get("plan_id") or ""),
            "task_id": str(task.get("task_id") or ""),
            "query": str(task.get("query") or "stage7 manager orchestration subplan split defer rescue"),
            "failure_signature": str(signature),
            "target_paths": sorted(targets),
            "weak_signals": list(wrong),
            "source_artifact": str(DEFAULT_CODEX51_LEARNING_LATEST),
            "evidence_mode": evidence_mode,
        }
    fallback["failure_signature"] = "no_matching_artifact_backed_failure_class_found"
    fallback["weak_signals"] = ["no matching lesson found; using deterministic bootstrap evidence"]
    return fallback


def _validation_check_artifact_backed_multi_file_inner_loop_template() -> dict[str, Any]:
    evidence = _load_artifact_backed_failure_evidence()
    rag6_file = REPO_ROOT / "bin" / "stage_rag6_plan_probe.py"
    rag4_file = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"
    rag6_rel = "bin/stage_rag6_plan_probe.py"
    rag4_rel = "bin/stage_rag4_plan_probe.py"

    rag6_baseline = rag6_file.read_text(encoding="utf-8")
    rag4_baseline = rag4_file.read_text(encoding="utf-8")
    rag6_broken = rag6_baseline.replace(
        'STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"',
        'STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe_typo.py"',
        1,
    )
    rag4_broken = rag4_baseline.replace(
        "Stage RAG-4 planning helper for Stage-6 multi-target orchestration.",
        "Stage RAG-4 planning helper for Stage-6 multi-target orchestration (drifted).",
        1,
    )

    setup_cmd = (
        "python3 -c \"from pathlib import Path; "
        "a=Path('bin/stage_rag6_plan_probe.py'); b=Path('bin/stage_rag4_plan_probe.py'); "
        "ta=a.read_text(encoding='utf-8'); tb=b.read_text(encoding='utf-8'); "
        "na='STAGE_RAG4_PLAN = REPO_ROOT / \\\"bin\\\" / \\\"stage_rag4_plan_probe.py\\\"'; "
        "nb='Stage RAG-4 planning helper for Stage-6 multi-target orchestration.'; "
        "assert na in ta, 'artifact_setup_missing_rag6_anchor'; "
        "assert nb in tb, 'artifact_setup_missing_rag4_anchor'; "
        "a.write_text(ta.replace(na, 'STAGE_RAG4_PLAN = REPO_ROOT / \\\"bin\\\" / \\\"stage_rag4_plan_probe_typo.py\\\"', 1), encoding='utf-8'); "
        "b.write_text(tb.replace(nb, 'Stage RAG-4 planning helper for Stage-6 multi-target orchestration (drifted).', 1), encoding='utf-8')\""
    )
    validate_cmd = (
        "python3 -c \"import json, subprocess, pathlib; "
        "cmd=['python3','bin/stage_rag6_plan_probe.py','--plan-id','framework-artifact-backed-multi-file','--max-targets','3','--max-subplans','2','--subplan-size','2','--preferred-prefix','bin/'] + "
        "'stage7 manager orchestration subplan split defer rescue'.split(); "
        "proc=subprocess.run(cmd,capture_output=True,text=True,check=True); "
        "payload=json.loads(proc.stdout); "
        "assert payload.get('subplans'), 'missing_subplans'; "
        "txt=pathlib.Path('bin/stage_rag4_plan_probe.py').read_text(encoding='utf-8'); "
        "assert 'Stage RAG-4 planning helper for Stage-6 multi-target orchestration.' in txt, 'rag4_contract_drift'\""
    )
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Run artifact-backed bounded coordinated multi-file edit-test-fix loop for a real "
            "multi_file_orchestration failure class with strict contracts and rollback safety."
        ),
        "permission_policy": {
            "allow_command_patterns": [
                r"^python3\s+-c\s+.*$",
                r"^python3\s+bin/stage_rag6_plan_probe\.py(\s+.*)?$",
            ],
            "allow_edit_path_patterns": [
                r"/bin/stage_rag6_plan_probe\.py$",
                r"/bin/stage_rag4_plan_probe\.py$",
            ],
            "deny_command_patterns": [r"\brm\b\s+-rf\b"],
        },
        "artifact_inputs": [
            evidence["source_artifact"],
            rag6_rel,
            rag4_rel,
        ],
        "requested_outputs": [rag6_rel, rag4_rel],
        "inner_loop": {
            "enabled": True,
            "coordinated_repairs": True,
            "max_cycles": 2,
            "tracked_paths": [rag6_rel, rag4_rel],
            "setup_command": setup_cmd,
            "validate_command": validate_cmd,
            "repair_edits": [
                {
                    "path": rag6_rel,
                    "find": 'STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe_typo.py"',
                    "replace": 'STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"',
                    "expected_before_sha256": hashlib.sha256(rag6_broken.encode("utf-8")).hexdigest(),
                    "expected_after_sha256": hashlib.sha256(rag6_baseline.encode("utf-8")).hexdigest(),
                },
                {
                    "path": rag4_rel,
                    "find": "Stage RAG-4 planning helper for Stage-6 multi-target orchestration (drifted).",
                    "replace": "Stage RAG-4 planning helper for Stage-6 multi-target orchestration.",
                    "expected_before_sha256": hashlib.sha256(rag4_broken.encode("utf-8")).hexdigest(),
                    "expected_after_sha256": hashlib.sha256(rag4_baseline.encode("utf-8")).hexdigest(),
                },
            ],
        },
        "artifact_evidence": evidence,
    }


def _trusted_pattern_refresh_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.TRUSTED_PATTERN_REFRESH.value,
        "shell_command": (
            "python3 bin/codex51_trusted_pattern_intake.py --json-only > artifacts/framework/trusted_pattern_refresh_stdout.json "
            "&& python3 bin/codex51_learning_loop.py --write-report --json-only > artifacts/framework/trusted_pattern_learning_stdout.json"
        ),
        "inference_prompt": (
            "Refresh trusted external pattern intake and re-run learning synthesis so reusable patterns "
            "and prevention guidance feed first-attempt priors."
        ),
        "artifact_inputs": [
            "config/trusted_pattern_sources.json",
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/codex51/benchmark/latest.json",
        ],
        "requested_outputs": [
            "artifacts/codex51/trusted_patterns/latest.json",
            "artifacts/codex51/learning/latest.json",
            "artifacts/framework/trusted_pattern_refresh_stdout.json",
            "artifacts/framework/trusted_pattern_learning_stdout.json",
        ],
    }


def _replay_queue_generation_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.REPLAY_QUEUE_GENERATION.value,
        "shell_command": (
            "python3 bin/codex51_learning_loop.py --write-report --json-only > artifacts/framework/replay_queue_learning_stdout.json "
            "&& python3 -c \"import json; from pathlib import Path; "
            "src=Path('artifacts/codex51/learning/latest.json'); "
            "dst=Path('artifacts/framework/replay_queue_latest.json'); "
            "dst.parent.mkdir(parents=True, exist_ok=True); "
            "payload=json.loads(src.read_text(encoding='utf-8')) if src.exists() else {}; "
            "queue=payload.get('prioritized_replay_queue') or payload.get('replay_queue') or []; "
            "dst.write_text(json.dumps({'generated_from': str(src), 'replay_queue': queue}, ensure_ascii=False, indent=2)+'\\n', encoding='utf-8')\""
        ),
        "inference_prompt": (
            "Refresh blocker-first replay queue from real learning artifacts and persist a bounded queue artifact "
            "for scheduler and manager consumption."
        ),
        "artifact_inputs": [
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/codex51/benchmark/latest.json",
            "artifacts/codex51/curation/failures_for_training.jsonl",
            "artifacts/manager6/traces.jsonl",
        ],
        "requested_outputs": [
            "artifacts/codex51/learning/latest.json",
            "artifacts/framework/replay_queue_latest.json",
            "artifacts/framework/replay_queue_learning_stdout.json",
        ],
    }


def _campaign_profile_matrix_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.CAMPAIGN_ARTIFACT_PROCESSING.value,
        "shell_command": (
            "python3 bin/local_replacement_campaign.py run-profile-matrix --dry-run --allow-dirty-worktree "
            "> artifacts/framework/campaign_profile_matrix_stdout.json"
        ),
        "inference_prompt": (
            "Run bounded campaign profile matrix so manager/retrieval paths have fresh per-profile evidence."
        ),
        "artifact_inputs": [
            "config/local_first_campaign.json",
            "artifacts/manager6/plans",
            "artifacts/manager6/traces.jsonl",
        ],
        "requested_outputs": [
            "artifacts/codex51/campaign/runs.jsonl",
            "artifacts/codex51/attribution/latest.json",
            "artifacts/framework/campaign_profile_matrix_stdout.json",
        ],
        "permission_policy": {
            "allow_command_patterns": [r"^python3\s+bin/local_replacement_campaign\.py\s+run-profile-matrix(\s+.*)?$"]
        },
    }


def _typed_tool_probe_template() -> dict[str, Any]:
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Phase 2 typed tool probe: read "
            "framework/framework_control_plane.py "
            "then write probe artifact via APPLY_PATCH write_text contract."
        ),
        "artifact_inputs": ["framework/framework_control_plane.py"],
        "requested_outputs": ["artifacts/framework/typed_tool_probe_output.txt"],
        "phase2_typed_tools": [
            {
                "contract_name": "read_file",
                "arguments": {"path": "framework/framework_control_plane.py"},
            },
            {
                "contract_name": "apply_patch",
                "arguments": {
                    "path": "artifacts/framework/typed_tool_probe_output.txt",
                    "mode": "write_text",
                    "content": "phase2_typed_tool_probe_ok\n",
                },
            },
        ],
        "permission_policy": {
            "allow_edit_path_patterns": [r"artifacts/framework/typed_tool_probe_output\.txt$"],
        },
    }


def _retrieval_probe_template(query: str = "_execute_job") -> dict[str, Any]:
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            f"Phase 3 retrieval probe: search for {query!r} across the repo, "
            "map the framework/ directory, then write a retrieval summary artifact."
        ),
        "artifact_inputs": ["framework/worker_runtime.py"],
        "requested_outputs": ["artifacts/framework/retrieval_probe_output.txt"],
        "phase2_typed_tools": [
            {
                "contract_name": "search",
                "arguments": {"query": query},
            },
            {
                "contract_name": "repo_map",
                "arguments": {"path": "framework"},
            },
            {
                "contract_name": "apply_patch",
                "arguments": {
                    "path": "artifacts/framework/retrieval_probe_output.txt",
                    "mode": "write_text",
                    "content": "phase3_retrieval_probe_ok\n",
                },
            },
        ],
        "permission_policy": {
            "allow_edit_path_patterns": [r"artifacts/framework/retrieval_probe_output\.txt$"],
        },
    }


_DEFAULT_RETRIEVAL_TARGETS_PATH = DEFAULT_STATE_ROOT / "retrieval_read_targets.json"
_DEFAULT_RETRIEVAL_QUERY_PATH = DEFAULT_STATE_ROOT / "retrieval_query_latest.json"
_DEFAULT_CONTEXT_BUNDLE_PATH = DEFAULT_STATE_ROOT / "context_bundle_latest.json"
_DEFAULT_PHASE3_FOLLOWON_PATH = DEFAULT_STATE_ROOT / "phase3_followon_template.json"
_DEFAULT_RECOMMENDATION_PATH = DEFAULT_STATE_ROOT / "phase3_recommendation_latest.json"
_DEFAULT_EDIT_PLAN_PATH = DEFAULT_STATE_ROOT / "phase3_edit_plan_latest.json"
_DEFAULT_EDIT_PLAN_VALIDATION_PATH = DEFAULT_STATE_ROOT / "phase3_edit_plan_validation_latest.json"
_DEFAULT_STAGE3_INVOCATION_PATH = DEFAULT_STATE_ROOT / "phase3_stage3_manager_invocation_latest.json"


def _load_retrieval_targets(path: Path) -> list[dict[str, Any]]:
    """Return typed-tool READ_FILE specs from a persisted retrieval_read_targets artifact.

    Returns [] on any missing/malformed file without raising.
    """
    try:
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            return []
        return [entry for entry in payload if isinstance(entry, dict)]
    except Exception:
        return []


def _load_retrieval_query(path: Path) -> str:
    """Return the persisted search query from a retrieval_query_latest.json artifact.

    Returns '' on any missing/malformed file without raising.
    """
    try:
        if not path.exists():
            return ""
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return ""
        return str(payload.get("query") or "")
    except Exception:
        return ""


def _load_context_bundle(path: Path) -> dict[str, Any]:
    """Return a persisted context_bundle dict from *path*.

    Returns {} on any missing/malformed file without raising.
    """
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _load_recommendation(path: Path) -> dict[str, Any]:
    """Return a persisted phase3_recommendation dict from *path*.

    Returns {} on any missing/malformed file without raising.
    """
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _load_phase3_followon(path: Path) -> dict[str, Any]:
    """Return a persisted phase3_followon record from *path*.

    Returns {} on missing path, malformed JSON, or non-dict payload without raising.
    """
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _load_edit_plan(path: Path) -> dict[str, Any]:
    """Return a persisted phase3_edit_plan dict from *path*.

    Returns {} on missing path, malformed JSON, or non-dict payload without raising.
    """
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _load_edit_plan_validation(path: Path) -> dict[str, Any]:
    """Return a persisted phase3_edit_plan_validation dict from *path*.

    Returns {} on missing path, malformed JSON, or non-dict payload without raising.
    """
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return {}
        return payload
    except Exception:
        return {}


def _read_after_retrieval_template(
    targets_path: Path = _DEFAULT_RETRIEVAL_TARGETS_PATH,
) -> dict[str, Any]:
    """Build a typed-tool template that reads files derived from a prior retrieval run.

    Loads persisted phase2_retrieval_read_targets from *targets_path*.
    Appends an APPLY_PATCH write_text sentinel artifact so the job validates.
    Returns an empty phase2_typed_tools list if no targets are available.
    """
    read_specs = _load_retrieval_targets(targets_path)
    phase2_typed_tools: list[dict[str, Any]] = list(read_specs)
    phase2_typed_tools.append(
        {
            "contract_name": "apply_patch",
            "arguments": {
                "path": "artifacts/framework/read_after_retrieval_output.txt",
                "mode": "write_text",
                "content": f"phase3_read_after_retrieval_ok targets={len(read_specs)}\n",
            },
        }
    )
    allow_patterns: list[str] = [r"artifacts/framework/read_after_retrieval_output\.txt$"]
    for spec in read_specs:
        path = str((spec.get("arguments") or {}).get("path") or "").strip()
        if path:
            allow_patterns.append(re.escape(path) + "$")
    if len(allow_patterns) == 1:
        allow_patterns.extend([r"^framework/", r"^bin/", r"^tests/", r"^promotion/", r"^shell/"])
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": (
            "Phase 3 read-after-retrieval: read files derived from the prior retrieval probe, "
            "then write a read-after-retrieval summary artifact."
        ),
        "artifact_inputs": [str(targets_path)],
        "requested_outputs": ["artifacts/framework/read_after_retrieval_output.txt"],
        "phase2_typed_tools": phase2_typed_tools,
        "permission_policy": {
            "allow_edit_path_patterns": allow_patterns,
        },
    }


def _context_bundle_probe_template() -> dict[str, Any]:
    """Build a typed-tool template that injects the persisted context bundle as an inference prompt."""
    bundle = _load_context_bundle(_DEFAULT_CONTEXT_BUNDLE_PATH)
    formatted_prompt = _phase3_build_context_prompt(bundle)
    inference_prompt = formatted_prompt or (
        "Phase 3 context bundle probe: no context bundle available; executing with default prompt."
    )
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": "true",
        "inference_prompt": inference_prompt,
        "artifact_inputs": [str(_DEFAULT_CONTEXT_BUNDLE_PATH)],
        "requested_outputs": ["artifacts/framework/context_bundle_probe_output.txt"],
        "phase2_typed_tools": [
            {
                "contract_name": "apply_patch",
                "arguments": {
                    "path": "artifacts/framework/context_bundle_probe_output.txt",
                    "mode": "write_text",
                    "content": f"phase3_context_bundle_probe_ok prompt_chars={len(formatted_prompt)}\n",
                },
            }
        ],
        "permission_policy": {
            "allow_edit_path_patterns": [r"artifacts/framework/context_bundle_probe_output\.txt$"],
        },
    }


def _context_bundle_inference_probe_template() -> dict[str, Any]:
    """Build a template that routes through the inference path with the context-bundle-derived prompt.

    Deliberately omits phase2_typed_tools so worker_runtime fires inference.run()
    instead of taking the typed-tool early-return path.
    """
    bundle = _load_context_bundle(_DEFAULT_CONTEXT_BUNDLE_PATH)
    formatted_prompt = _phase3_build_context_prompt(bundle)
    inference_prompt = formatted_prompt or (
        "Phase 3 context bundle inference probe: no context bundle available; "
        "executing default inference path."
    )
    prompt_len = len(formatted_prompt)
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": (
            "python3 -c \""
            "from pathlib import Path; "
            "p = Path('artifacts/framework/context_bundle_inference_probe_output.txt'); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            f"p.write_text('phase3_context_bundle_inference_probe_ok prompt_chars={prompt_len}\\n', encoding='utf-8')\""
        ),
        "inference_prompt": inference_prompt,
        "artifact_inputs": [str(_DEFAULT_CONTEXT_BUNDLE_PATH)],
        "requested_outputs": [
            "artifacts/framework/context_bundle_inference_probe_output.txt"
        ],
        "permission_policy": {
            "allow_edit_path_patterns": [
                r"artifacts/framework/context_bundle_inference_probe_output\.txt$"
            ],
        },
    }


def _phase3_edit_plan_probe_template(
    recommendation_path: Path = _DEFAULT_RECOMMENDATION_PATH,
) -> dict[str, Any]:
    """Build a template that instructs Ollama to generate a stage3_manager edit instruction.

    Reads the persisted recommendation artifact to build a context-rich inference prompt.
    Falls back to a placeholder prompt when no recommendation is available.
    """
    rec = _load_recommendation(recommendation_path)
    if not rec or not rec.get("recommendation_ready"):
        inference_prompt = "No prior recommendation available. Run make phase3-query first."
    else:
        query = str(rec.get("query") or "")
        inference_text = str(rec.get("inference_text") or "")[:1200]
        top_file = str(rec.get("top_file") or "")
        inference_prompt = (
            f"Query: {query}\n\n"
            f"Code analysis:\n{inference_text}\n\n"
            f"Primary file: {top_file}\n\n"
            "Based on the analysis above, generate ONE specific, minimal code modification "
            "to address the query. Your response must be exactly one line in this format:\n"
            f"{top_file}:: replace exact text 'EXACT_OLD_TEXT' with 'EXACT_NEW_TEXT'\n"
            "The old text must appear verbatim in the file. The replacement must be minimal."
        )
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": (
            "python3 -c \""
            "from pathlib import Path; "
            "p = Path('artifacts/framework/phase3_edit_plan_output.txt'); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            "p.write_text('phase3_edit_plan_probe_ok\\n', encoding='utf-8')\""
        ),
        "inference_prompt": inference_prompt,
        "artifact_inputs": [str(recommendation_path)],
        "requested_outputs": ["artifacts/framework/phase3_edit_plan_output.txt"],
        "permission_policy": {
            "allow_edit_path_patterns": [r"artifacts/framework/phase3_edit_plan_output\.txt$"],
        },
    }


def _phase3_validate_edit_plan_probe_template(
    edit_plan_path: Path = _DEFAULT_EDIT_PLAN_PATH,
) -> dict[str, Any]:
    """Validate the OLD text from the persisted edit plan against the real target file.

    Performs validation in-process (no inference needed). Persists the validation
    result to _DEFAULT_EDIT_PLAN_VALIDATION_PATH and embeds it under
    '_phase3_validation_result' in the returned template dict so main() can surface
    it without re-loading.
    """
    edit_plan = _load_edit_plan(edit_plan_path)
    validation_result = _phase3_validate_edit_plan(edit_plan, REPO_ROOT)
    try:
        _DEFAULT_EDIT_PLAN_VALIDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DEFAULT_EDIT_PLAN_VALIDATION_PATH.write_text(
            json.dumps(validation_result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": (
            "python3 -c \""
            "from pathlib import Path; "
            "p = Path('artifacts/framework/phase3_edit_plan_validate_output.txt'); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            "p.write_text('phase3_edit_plan_validate_ok\\n', encoding='utf-8')\""
        ),
        "inference_prompt": "Phase 3 edit plan validation: no inference needed.",
        "artifact_inputs": [str(edit_plan_path)],
        "requested_outputs": ["artifacts/framework/phase3_edit_plan_validate_output.txt"],
        "permission_policy": {
            "allow_edit_path_patterns": [
                r"artifacts/framework/phase3_edit_plan_validate_output\.txt$"
            ],
        },
        "_phase3_validation_result": validation_result,
    }


def _phase3_apply_edit_plan_probe_template(
    edit_plan_validation_path: Path = _DEFAULT_EDIT_PLAN_VALIDATION_PATH,
    edit_plan_path: Path = _DEFAULT_EDIT_PLAN_PATH,
    recommendation_path: Path = _DEFAULT_RECOMMENDATION_PATH,
) -> dict[str, Any]:
    """Build stage3_manager invocation spec from persisted validation + edit plan + recommendation.

    Runs in-process (no inference needed). Persists the invocation spec to
    _DEFAULT_STAGE3_INVOCATION_PATH and embeds it under '_phase3_invocation_result'.
    """
    validation_result = _load_edit_plan_validation(edit_plan_validation_path)
    edit_plan = _load_edit_plan(edit_plan_path)
    recommendation = _load_recommendation(recommendation_path)
    invocation = _phase3_build_stage3_manager_invocation(validation_result, edit_plan, recommendation)
    try:
        _DEFAULT_STAGE3_INVOCATION_PATH.parent.mkdir(parents=True, exist_ok=True)
        _DEFAULT_STAGE3_INVOCATION_PATH.write_text(
            json.dumps(invocation, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
    return {
        "task_class": JobClass.VALIDATION_CHECK_EXECUTION.value,
        "shell_command": (
            "python3 -c \""
            "from pathlib import Path; "
            "p = Path('artifacts/framework/phase3_apply_edit_plan_output.txt'); "
            "p.parent.mkdir(parents=True, exist_ok=True); "
            "p.write_text('phase3_apply_edit_plan_probe_ok\\n', encoding='utf-8')\""
        ),
        "inference_prompt": "Phase 3 apply edit plan: no inference needed.",
        "artifact_inputs": [str(edit_plan_validation_path)],
        "requested_outputs": ["artifacts/framework/phase3_apply_edit_plan_output.txt"],
        "permission_policy": {
            "allow_edit_path_patterns": [
                r"artifacts/framework/phase3_apply_edit_plan_output\.txt$"
            ],
        },
        "_phase3_invocation_result": invocation,
    }


def _phase3_followon_template() -> dict[str, Any]:
    """Delegate to the template selected by the persisted phase3_followon_template artifact.

    Reads _DEFAULT_PHASE3_FOLLOWON_PATH; falls back to retrieval_probe if absent or malformed.
    """
    record = _load_phase3_followon(_DEFAULT_PHASE3_FOLLOWON_PATH)
    selected = str(record.get("template") or "retrieval_probe").strip() or "retrieval_probe"
    _PHASE3_ALLOWED = frozenset({
        "retrieval_probe",
        "read_after_retrieval",
        "context_bundle_probe",
        "context_bundle_inference_probe",
    })
    if selected not in _PHASE3_ALLOWED:
        selected = "retrieval_probe"
    payload = _template_payload(selected)
    payload["_phase3_followon_resolved_template"] = selected
    return payload


def _coerce_job_class(value: str) -> JobClass:
    try:
        return JobClass(str(value))
    except ValueError:
        return JobClass.BOUNDED_ARCHITECTURE


def _apply_task_policy(job: Job) -> Job:
    """Apply stable task-class defaults so scheduling/retry/escalation stay explicit."""
    policy: dict[JobClass, dict[str, Any]] = {
        JobClass.VALIDATION_CHECK_EXECUTION: {
            "priority": JobPriority.P0,
            "retry_budget": 0,
            "auto_escalate": True,
        },
        JobClass.BENCHMARK_ANALYSIS: {
            "priority": JobPriority.P1,
            "retry_budget": 0,
            "auto_escalate": True,
        },
        JobClass.CAMPAIGN_ARTIFACT_PROCESSING: {
            "priority": JobPriority.P1,
            "retry_budget": 1,
            "auto_escalate": True,
        },
        JobClass.LEARNING_ARTIFACT_SYNTHESIS: {
            "priority": JobPriority.P1,
            "retry_budget": 1,
            "auto_escalate": True,
        },
        JobClass.REPLAY_QUEUE_EXECUTION: {
            "priority": JobPriority.P0,
            "retry_budget": 0,
            "auto_escalate": True,
        },
        JobClass.TRUSTED_PATTERN_REFRESH: {
            "priority": JobPriority.P2,
            "retry_budget": 1,
            "auto_escalate": True,
        },
    }
    row = policy.get(job.task_class)
    if not row:
        return job
    job.priority = row["priority"]
    job.retry_policy = RetryPolicy(
        retry_budget=int(row["retry_budget"]),
        retry_backoff_seconds=int(job.retry_policy.retry_backoff_seconds),
    )
    job.escalation_policy = EscalationPolicy(
        allow_auto_escalation=bool(row["auto_escalate"]),
        escalate_on_retry_exhaustion=True,
        escalation_label="framework_manual_review",
    )
    job.metadata["task_policy"] = {
        "priority": job.priority.value,
        "retry_budget": int(job.retry_policy.retry_budget),
        "auto_escalate": bool(job.escalation_policy.allow_auto_escalation),
    }
    return job


def _rewrite_replay_command(command: str, *, mode: str) -> str:
    if mode == "as_is":
        return command
    if not command:
        return command
    parts = shlex.split(command)
    if "--no-dry-run" in parts:
        parts = ["--dry-run" if token == "--no-dry-run" else token for token in parts]
    elif "--dry-run" not in parts:
        parts.append("--dry-run")
    if "--allow-dirty-worktree" not in parts:
        parts.append("--allow-dirty-worktree")
    return " ".join(shlex.quote(item) for item in parts)


def _load_replay_queue(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, dict):
        return []
    queue = payload.get("replay_queue")
    if not isinstance(queue, list):
        return []
    return [row for row in queue if isinstance(row, dict)]


def _build_replay_jobs(args: argparse.Namespace) -> list[Job]:
    queue_path = Path(str(args.replay_queue_path)).resolve()
    rows = _load_replay_queue(queue_path)
    if not rows:
        return []
    jobs: list[Job] = []
    for index, row in enumerate(rows[: max(1, int(args.replay_max_items))], start=1):
        task_class = _coerce_job_class(str(row.get("task_class") or JobClass.REPLAY_QUEUE_EXECUTION.value))
        replay_command = _rewrite_replay_command(str(row.get("replay_command") or ""), mode=str(args.replay_execution_mode))
        if not replay_command:
            continue
        requested_output = f"artifacts/framework/replay_exec_{index}_{str(row.get('task_id') or 'unknown')}.txt"
        jobs.append(
            Job(
                task_class=task_class,
                priority=JobPriority(args.priority),
                target=WorkTarget(repo_root=str(REPO_ROOT), worktree_target=str(REPO_ROOT)),
                action=JobAction.INFERENCE_AND_SHELL,
                artifact_inputs=[
                    str(queue_path),
                    "artifacts/codex51/learning/latest.json",
                    "artifacts/codex51/campaign/runs.jsonl",
                ],
                requested_outputs=[requested_output],
                allowed_tools_actions=["inference", "shell_command"],
                retry_policy=RetryPolicy(
                    retry_budget=max(0, int(args.retry_budget)),
                    retry_backoff_seconds=max(0, int(args.retry_backoff_seconds)),
                ),
                escalation_policy=EscalationPolicy(
                    allow_auto_escalation=bool(args.auto_escalate),
                    escalate_on_retry_exhaustion=True,
                    escalation_label="framework_manual_review",
                ),
                validation_requirements=[
                    ValidationRequirement.EXIT_CODE_ZERO,
                    ValidationRequirement.ARTIFACT_WRITTEN,
                ],
                learning_hooks=LearningHooksConfig(
                    emit_lessons=True,
                    emit_prevention_candidates=True,
                    emit_reuse_candidates=True,
                    task_class_priors=[task_class.value, JobClass.REPLAY_QUEUE_EXECUTION.value],
                ),
                metadata={
                    "shell_command": f"{replay_command} > {requested_output}",
                    "inference_prompt": (
                        "Execute blocker-first replay task from learning queue through bounded framework runtime."
                    ),
                    "context_hint": "framework-replay",
                    "submitted_by": "framework_control_plane",
                    "task_template": "replay_queue_execution",
                    "replay_execution_mode": str(args.replay_execution_mode),
                    "replay_source_queue": str(queue_path),
                    "replay_source_task_id": str(row.get("task_id") or ""),
                    "replay_reason": str(row.get("reason") or ""),
                },
            )
        )
    return jobs


def _template_payload(name: str) -> dict[str, Any]:
    if name == "learning_refresh":
        return _learning_refresh_template()
    if name == "benchmark_refresh":
        return _benchmark_refresh_template()
    if name == "campaign_artifact_processing":
        return _campaign_artifact_processing_template()
    if name == "validation_check_execution":
        return _validation_check_execution_template()
    if name == "validation_check_inner_loop":
        return _validation_check_inner_loop_template()
    if name == "validation_check_tracked_inner_loop":
        return _validation_check_tracked_inner_loop_template()
    if name == "validation_check_tracked_multi_file_inner_loop":
        return _validation_check_tracked_multi_file_inner_loop_template()
    if name == "validation_check_artifact_backed_multi_file_inner_loop":
        return _validation_check_artifact_backed_multi_file_inner_loop_template()
    if name == "trusted_pattern_refresh":
        return _trusted_pattern_refresh_template()
    if name == "replay_queue_generation":
        return _replay_queue_generation_template()
    if name == "replay_queue_execution":
        return {
            "task_class": JobClass.REPLAY_QUEUE_EXECUTION.value,
            "shell_command": "true",
            "inference_prompt": "Replay queue execution template is expanded into concrete queued jobs.",
            "artifact_inputs": [str(DEFAULT_REPLAY_QUEUE)],
            "requested_outputs": [],
        }
    if name == "campaign_profile_matrix":
        return _campaign_profile_matrix_template()
    if name == "typed_tool_probe":
        return _typed_tool_probe_template()
    if name == "retrieval_probe":
        return _retrieval_probe_template()
    if name == "read_after_retrieval":
        return _read_after_retrieval_template()
    if name == "context_bundle_probe":
        return _context_bundle_probe_template()
    if name == "context_bundle_inference_probe":
        return _context_bundle_inference_probe_template()
    if name == "phase3_followon":
        return _phase3_followon_template()
    if name == "phase3_edit_plan_probe":
        return _phase3_edit_plan_probe_template()
    if name == "phase3_validate_edit_plan_probe":
        return _phase3_validate_edit_plan_probe_template()
    if name == "phase3_apply_edit_plan_probe":
        return _phase3_apply_edit_plan_probe_template()
    return {}


def build_job(args: argparse.Namespace, *, template_name: str | None = None) -> Job:
    resolved_template = str(template_name or args.task_template)
    if resolved_template == "retrieval_probe":
        _query = " ".join(getattr(args, "phase3_query", None) or ["_execute_job"])
        template_payload = _retrieval_probe_template(query=_query)
    else:
        template_payload = _template_payload(resolved_template)

    command = args.shell_command.strip() or str(template_payload.get("shell_command") or _default_command())
    requested_outputs = args.requested_output or list(
        template_payload.get("requested_outputs") or ["artifacts/framework/demo_output.txt"]
    )
    artifact_inputs = list(args.artifact_input) or list(template_payload.get("artifact_inputs") or [])
    task_class = str(template_payload.get("task_class") or args.task_class)
    inference_prompt = (
        args.inference_prompt
        or str(template_payload.get("inference_prompt") or "Execute bounded local-first job and emit artifacts.")
    )

    return Job(
        task_class=JobClass(task_class),
        priority=JobPriority(args.priority),
        target=WorkTarget(repo_root=str(REPO_ROOT), worktree_target=str(REPO_ROOT)),
        action=JobAction.INFERENCE_AND_SHELL,
        artifact_inputs=artifact_inputs,
        requested_outputs=requested_outputs,
        allowed_tools_actions=["inference", "shell_command", "apply_edit"],
        retry_policy=RetryPolicy(
            retry_budget=max(0, int(args.retry_budget)),
            retry_backoff_seconds=max(0, int(args.retry_backoff_seconds)),
        ),
        escalation_policy=EscalationPolicy(
            allow_auto_escalation=bool(args.auto_escalate),
            escalate_on_retry_exhaustion=True,
            escalation_label="framework_manual_review",
        ),
        validation_requirements=[
            ValidationRequirement.EXIT_CODE_ZERO,
            ValidationRequirement.ARTIFACT_WRITTEN,
        ],
        learning_hooks=LearningHooksConfig(
            emit_lessons=True,
            emit_prevention_candidates=True,
            emit_reuse_candidates=True,
            task_class_priors=[task_class],
        ),
        metadata={
            "shell_command": command,
            "inference_prompt": inference_prompt,
            "context_hint": "framework",
            "submitted_by": "framework_control_plane",
            "task_template": resolved_template,
            "permission_policy": template_payload.get("permission_policy")
            if isinstance(template_payload.get("permission_policy"), dict)
            else {},
            "inner_loop": template_payload.get("inner_loop") if isinstance(template_payload.get("inner_loop"), dict) else {},
            "artifact_evidence": template_payload.get("artifact_evidence")
            if isinstance(template_payload.get("artifact_evidence"), dict)
            else {},
            "phase2_typed_tools": (
                template_payload.get("phase2_typed_tools")
                if isinstance(template_payload.get("phase2_typed_tools"), list)
                else []
            ),
        },
    )


def _compute_phase2_exit_code(output: dict[str, Any], result_rows: list[dict[str, Any]]) -> int:
    """Return the process exit code from a completed scheduler output dict.

    Exit codes:
      0 — idle, all jobs terminal, no all-tools-blocked signal
      2 — scheduler did not reach idle
      3 — idle but jobs not yet in a terminal state
      4 — idle, terminal, but all tool attempts were blocked by the permission engine
      5 — Phase 3 action is refine_retrieval (applied by _compute_phase3_exit_code)
      6 — Phase 3 action is insufficient_context (applied by _compute_phase3_exit_code)
    """
    if not output.get("idle_reached"):
        return 2
    statuses = {str((row.get("result") or {}).get("status") or "") for row in result_rows}
    if not (statuses and statuses.issubset({"completed", "escalated", "failed"})):
        return 3
    signal = str((output.get("phase2_operational_signal") or {}).get("signal") or "")
    if signal == "all_tools_blocked":
        return 4
    return 0


def _compute_phase3_exit_code(output: dict[str, Any]) -> int:
    """Return a supplemental Phase 3 exit code derived from phase3_next_action.

    Called only when _compute_phase2_exit_code returns 0.

    Exit codes:
      0 — no Phase 3 override (action is ready, no_context, or signal absent)
      5 — Phase 3 action is refine_retrieval (context inadequate; more retrieval needed)
      6 — Phase 3 action is insufficient_context (inference produced no usable content)
    """
    _nxt = output.get("phase3_next_action")
    action = str((_nxt if isinstance(_nxt, dict) else {}).get("action") or "")
    if action == "refine_retrieval":
        return 5
    if action == "insufficient_context":
        return 6
    return 0


def _compute_phase3_continuation_exit_code(output: dict[str, Any]) -> int:
    """Return the continuation-pass exit code derived from phase3_continuation_result.

    Returns:
      -1 — sentinel: no continuation ran; caller must not override primary exit code
       0 — continuation ran and action is ready (or unknown)
       5 — continuation ran and action is refine_retrieval
       6 — continuation ran and action is insufficient_context
    """
    cont_result = output.get("phase3_continuation_result")
    if not isinstance(cont_result, dict) or not cont_result.get("ran"):
        return -1
    action = str((cont_result.get("phase3_continuation_next_action") or {}).get("action") or "")
    if action == "refine_retrieval":
        return 5
    if action == "insufficient_context":
        return 6
    return 0


def _run_phase3_continuation(
    args: argparse.Namespace,
    store: Any,
    learning: Any,
    inference: Any,
    profile: Any,
    followon_template: str,
) -> dict[str, Any]:
    """Run a single follow-on job using *followon_template* on a fresh scheduler pass.

    Builds a fresh Scheduler from the provided store/learning/inference/profile components.
    Returns a compact status dict. Does not re-run full Phase 3 analysis helpers.
    All exceptions are caught and surfaced in the returned dict.
    """
    _CONTINUATION_SAFE: dict[str, Any] = {
        "ran": False,
        "template_used": followon_template,
        "idle_reached": False,
        "job_status": "",
        "return_code": -1,
        "typed_tool_count": 0,
        "error": "",
        "phase3_continuation_next_action": {},
        "phase3_continuation_recommendation_ready": False,
    }
    try:
        scheduler = Scheduler(
            store=store,
            learning=learning,
            inference=inference,
            backend_profile=profile,
            replay_pending_on_start=bool(getattr(args, "replay_pending", False)),
            replay_attempt_limit=max(1, int(getattr(args, "scheduler_replay_attempt_limit", 2))),
        )
        cont_job = _apply_task_policy(build_job(args, template_name=followon_template))
        scheduler.start()
        cont_queued = scheduler.submit(cont_job)
        cont_idle = scheduler.wait_for_idle(
            timeout_seconds=max(1.0, float(args.wait_timeout_seconds))
        )
        scheduler.stop()
        cont_result_path = (
            Path(args.state_root).resolve() / "results" / f"{cont_queued.job_id}.json"
        )
        cont_payload: dict[str, Any] = {}
        if cont_result_path.exists():
            try:
                cont_payload = json.loads(
                    cont_result_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                cont_payload = {}
        typed_trace = cont_payload.get("typed_tool_trace")
        typed_count = len(typed_trace) if isinstance(typed_trace, list) else 0

        # Re-run Phase 3 analysis pipeline on the continuation's raw result.
        cont_typed_results = _phase2_extract_typed_results(cont_payload)
        cont_inference_response = _phase3_extract_inference_response(cont_payload)
        cont_context_bundle = _load_context_bundle(_DEFAULT_CONTEXT_BUNDLE_PATH)
        if cont_typed_results:
            cont_retrieval_summary = _phase2_retrieval_summary(cont_typed_results)
            cont_read_content = _phase3_extract_read_content(cont_typed_results)
            cont_symbol_index = _phase3_extract_symbol_index(cont_read_content)
            new_bundle = _phase3_assemble_context_bundle(
                cont_retrieval_summary, cont_read_content, cont_symbol_index
            )
            if new_bundle.get("prompt_ready"):
                cont_context_bundle = new_bundle
                try:
                    _DEFAULT_CONTEXT_BUNDLE_PATH.parent.mkdir(parents=True, exist_ok=True)
                    _DEFAULT_CONTEXT_BUNDLE_PATH.write_text(
                        json.dumps(new_bundle, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                except Exception:
                    pass
        cont_next_action = _phase3_derive_next_action(cont_context_bundle, cont_inference_response)

        cont_recommendation_ready = False
        if str((cont_next_action or {}).get("action") or "") == "ready" and cont_inference_response.get("has_content"):
            _cont_rec = _phase3_build_recommendation(cont_context_bundle, cont_inference_response)
            try:
                _DEFAULT_RECOMMENDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
                _DEFAULT_RECOMMENDATION_PATH.write_text(
                    json.dumps(_cont_rec, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                cont_recommendation_ready = True
            except Exception:
                pass

        return {
            "ran": True,
            "template_used": followon_template,
            "idle_reached": cont_idle,
            "job_status": str(cont_payload.get("status") or ""),
            "return_code": int(cont_payload.get("return_code") or -1),
            "typed_tool_count": typed_count,
            "error": "",
            "phase3_continuation_next_action": cont_next_action,
            "phase3_continuation_recommendation_ready": cont_recommendation_ready,
        }
    except Exception as exc:
        return {**_CONTINUATION_SAFE, "error": str(exc)}


def main() -> int:
    args = parse_args()

    state_root = Path(args.state_root).resolve()
    profile = select_backend_profile_auto() if args.backend_profile == "auto" else get_backend_profile(args.backend_profile)
    store = StateStore(root=state_root)
    learning_latest = (
        Path(str(args.learning_latest)).resolve()
        if str(args.learning_latest).strip()
        else (state_root / "learning" / "latest.json").resolve()
    )
    manager_bridge_latest = (state_root / "bridge" / "latest_manager_learning_bridge.json").resolve()
    learning = LearningHooks(
        store=store,
        learning_latest_path=learning_latest,
        code_library_path=DEFAULT_CODE_LIBRARY_LATEST,
        trusted_patterns_path=DEFAULT_TRUSTED_PATTERNS_LATEST,
        manager_bridge_path=manager_bridge_latest,
    )
    inference = build_inference_adapter(
        backend_profile=profile.name,
        mode=args.inference_mode,
        replay_path=args.inference_replay,
    )
    scheduler = Scheduler(
        store=store,
        learning=learning,
        inference=inference,
        backend_profile=profile,
        replay_pending_on_start=bool(args.replay_pending),
        replay_attempt_limit=max(1, int(args.scheduler_replay_attempt_limit)),
    )

    portfolio_templates: list[str] = []
    if args.task_portfolio == "next5_high_value":
        portfolio_templates = [
            "campaign_profile_matrix",
            "campaign_artifact_processing",
            "replay_queue_generation",
            "trusted_pattern_refresh",
            "benchmark_refresh",
        ]

    if args.task_template == "replay_queue_execution":
        jobs = [_apply_task_policy(job) for job in _build_replay_jobs(args)]
        if not jobs:
            print(
                json.dumps(
                    {
                        "job": {},
                        "jobs": [],
                        "results": [],
                        "idle_reached": True,
                        "scheduler_status": {},
                        "state_root": str(state_root),
                        "learning_latest": str(learning_latest),
                        "manager_learning_bridge": str(manager_bridge_latest),
                        "task_portfolio": args.task_portfolio,
                        "replay_queue_path": str(Path(str(args.replay_queue_path)).resolve()),
                        "note": "no replay items available",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
    elif portfolio_templates:
        jobs = [_apply_task_policy(build_job(args, template_name=template)) for template in portfolio_templates]
    else:
        jobs = [_apply_task_policy(build_job(args))]
    scheduler.start()
    queued_jobs = [scheduler.submit(job) for job in jobs]
    idle = scheduler.wait_for_idle(timeout_seconds=max(1.0, float(args.wait_timeout_seconds)))
    scheduler.stop()
    job_rows: list[dict[str, Any]] = []
    result_rows: list[dict[str, Any]] = []
    for queued in queued_jobs:
        persisted_job = store.load_job(queued.job_id)
        result_path = state_root / "results" / f"{queued.job_id}.json"
        result_payload: dict[str, Any] = {}
        if result_path.exists():
            try:
                result_payload = json.loads(result_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                result_payload = {}
        job_rows.append(persisted_job.to_dict() if persisted_job else queued.to_dict())
        result_rows.append(
            {
                "job_id": queued.job_id,
                "result_path": str(result_path),
                "result": result_payload,
            }
        )

    primary_result_path = result_rows[0]["result_path"] if result_rows else ""
    primary_result_payload = result_rows[0]["result"] if result_rows else {}
    output = {
        "job": job_rows[0] if job_rows else {},
        "jobs": job_rows,
        "result_path": primary_result_path,
        "result": primary_result_payload,
        "results": result_rows,
        "idle_reached": idle,
        "scheduler_status": scheduler.status_snapshot(),
        "state_root": str(state_root),
        "learning_latest": str(learning_latest),
        "manager_learning_bridge": str(manager_bridge_latest),
        "task_portfolio": args.task_portfolio,
    }
    output["phase2_manager_view"] = _phase2_manager_extract(primary_result_payload)
    output["phase2_operational_signal"] = _phase2_manager_decision(output["phase2_manager_view"])
    output["phase2_typed_tool_results"] = _phase2_extract_typed_results(primary_result_payload)
    output["phase2_retrieval_read_targets"] = _phase2_derive_read_targets(
        output["phase2_typed_tool_results"]
    )
    output["phase2_retrieval_summary"] = _phase2_retrieval_summary(
        output["phase2_typed_tool_results"]
    )
    output["phase3_read_content_results"] = _phase3_extract_read_content(
        output["phase2_typed_tool_results"]
    )
    output["phase3_read_content_summary"] = _phase3_read_content_summary(
        output["phase2_typed_tool_results"]
    )
    output["phase3_symbol_index"] = _phase3_extract_symbol_index(
        output["phase3_read_content_results"]
    )

    if args.task_template == "read_after_retrieval":
        try:
            _injected_query = str((output.get("phase2_retrieval_summary") or {}).get("query") or "")
            if not _injected_query:
                _injected_query = _load_retrieval_query(_DEFAULT_RETRIEVAL_QUERY_PATH)
            if _injected_query:
                _patched_summary = dict(output.get("phase2_retrieval_summary") or {})
                _patched_summary["query"] = _injected_query
                output["phase2_retrieval_summary"] = _patched_summary
                output["phase3_retrieval_query_injected"] = _injected_query
        except Exception:
            pass

    output["phase3_context_bundle"] = _phase3_assemble_context_bundle(
        output["phase2_retrieval_summary"],
        output["phase3_read_content_results"],
        output["phase3_symbol_index"],
    )

    _bundle = output["phase3_context_bundle"]
    if _bundle.get("prompt_ready"):
        _bundle_out = _DEFAULT_CONTEXT_BUNDLE_PATH
        try:
            _bundle_out.parent.mkdir(parents=True, exist_ok=True)
            _bundle_out.write_text(
                json.dumps(_bundle, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            output["phase3_context_bundle_persisted"] = str(_bundle_out)
        except Exception as _e:
            output["phase3_context_bundle_persist_error"] = str(_e)

    output["phase3_inference_response"] = _phase3_extract_inference_response(
        primary_result_payload
    )
    output["phase3_next_action"] = _phase3_derive_next_action(
        output["phase3_context_bundle"],
        output["phase3_inference_response"],
    )

    _ready_action = str((output.get("phase3_next_action") or {}).get("action") or "")
    if _ready_action == "ready" and output.get("phase3_inference_response", {}).get("has_content"):
        _rec = _phase3_build_recommendation(
            output["phase3_context_bundle"],
            output["phase3_inference_response"],
        )
        try:
            _DEFAULT_RECOMMENDATION_PATH.parent.mkdir(parents=True, exist_ok=True)
            _DEFAULT_RECOMMENDATION_PATH.write_text(
                json.dumps(_rec, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            output["phase3_recommendation"] = _rec
            output["phase3_recommendation_persisted"] = str(_DEFAULT_RECOMMENDATION_PATH)
        except Exception as _rec_e:
            output["phase3_recommendation"] = _rec
            output["phase3_recommendation_persist_error"] = str(_rec_e)

    _followon_template = _phase3_select_followon_template(
        output["phase3_next_action"],
        context_bundle=output.get("phase3_context_bundle"),
        retrieval_targets_exist=bool(output.get("phase2_retrieval_read_targets")),
    )
    _followon_record = {
        "template": _followon_template,
        "action": str((output["phase3_next_action"] or {}).get("action") or ""),
    }
    _followon_out = _DEFAULT_PHASE3_FOLLOWON_PATH
    try:
        _followon_out.parent.mkdir(parents=True, exist_ok=True)
        _followon_out.write_text(
            json.dumps(_followon_record, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        output["phase3_followon_template"] = _followon_template
        output["phase3_followon_persisted"] = str(_followon_out)
    except Exception as _e:
        output["phase3_followon_persist_error"] = str(_e)

    _auto_continue_actions = {"refine_retrieval", "insufficient_context"}
    _current_action = str((output.get("phase3_next_action") or {}).get("action") or "")
    if getattr(args, "phase3_auto_continue", False) and _current_action in _auto_continue_actions:
        _cont_template = str(output.get("phase3_followon_template") or "retrieval_probe")
        output["phase3_continuation_result"] = _run_phase3_continuation(
            args, store, learning, inference, profile, _cont_template
        )

    try:
        if args.task_template == "phase3_edit_plan_probe" and output.get("phase3_inference_response", {}).get("has_content"):
            _edit_plan = _phase3_build_edit_plan(
                output["phase3_inference_response"],
                _load_recommendation(_DEFAULT_RECOMMENDATION_PATH),
            )
            try:
                _DEFAULT_EDIT_PLAN_PATH.parent.mkdir(parents=True, exist_ok=True)
                _DEFAULT_EDIT_PLAN_PATH.write_text(
                    json.dumps(_edit_plan, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                output["phase3_edit_plan"] = _edit_plan
                output["phase3_edit_plan_persisted"] = str(_DEFAULT_EDIT_PLAN_PATH)
            except Exception as _ep_e:
                output["phase3_edit_plan"] = _edit_plan
                output["phase3_edit_plan_persist_error"] = str(_ep_e)
    except Exception:
        pass

    try:
        if args.task_template == "phase3_validate_edit_plan_probe":
            _val_result: dict[str, Any] = {}
            if _DEFAULT_EDIT_PLAN_VALIDATION_PATH.exists():
                try:
                    _val_result = json.loads(_DEFAULT_EDIT_PLAN_VALIDATION_PATH.read_text(encoding="utf-8"))
                    if not isinstance(_val_result, dict):
                        _val_result = {}
                except Exception:
                    _val_result = {}
            output["phase3_edit_plan_validation"] = _val_result
            output["phase3_edit_plan_validation_persisted"] = str(_DEFAULT_EDIT_PLAN_VALIDATION_PATH)
    except Exception:
        pass

    try:
        if args.task_template == "phase3_apply_edit_plan_probe":
            _inv_result: dict[str, Any] = {}
            if _DEFAULT_STAGE3_INVOCATION_PATH.exists():
                try:
                    _inv_result = json.loads(_DEFAULT_STAGE3_INVOCATION_PATH.read_text(encoding="utf-8"))
                    if not isinstance(_inv_result, dict):
                        _inv_result = {}
                except Exception:
                    _inv_result = {}
            output["phase3_stage3_manager_invocation"] = _inv_result
            output["phase3_stage3_manager_invocation_persisted"] = str(_DEFAULT_STAGE3_INVOCATION_PATH)
    except Exception:
        pass

    read_targets = output["phase2_retrieval_read_targets"]
    if read_targets:
        _targets_out = _DEFAULT_RETRIEVAL_TARGETS_PATH
        try:
            _targets_out.parent.mkdir(parents=True, exist_ok=True)
            _targets_out.write_text(
                json.dumps(read_targets, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            output["phase2_retrieval_targets_persisted"] = str(_targets_out)
        except Exception as _e:
            output["phase2_retrieval_targets_persist_error"] = str(_e)

    if args.task_template == "retrieval_probe":
        _ret_query_str = str((output.get("phase2_retrieval_summary") or {}).get("query") or "")
        try:
            _DEFAULT_RETRIEVAL_QUERY_PATH.parent.mkdir(parents=True, exist_ok=True)
            _DEFAULT_RETRIEVAL_QUERY_PATH.write_text(
                json.dumps({"query": _ret_query_str}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            output["phase3_retrieval_query_persisted"] = str(_DEFAULT_RETRIEVAL_QUERY_PATH)
        except Exception as _rqe:
            output["phase3_retrieval_query_persist_error"] = str(_rqe)

    _exit = _compute_phase2_exit_code(output, result_rows)
    if _exit == 0:
        _phase3_exit = _compute_phase3_exit_code(output)
        if _phase3_exit != 0:
            _exit = _phase3_exit
    _cont_exit = _compute_phase3_continuation_exit_code(output)
    if _cont_exit >= 0:
        _exit = _cont_exit

    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(f"framework_job_id={output['job']['job_id']}")
        print(f"framework_job_lifecycle={output['job']['lifecycle']}")
        print(f"framework_idle_reached={str(output['idle_reached']).lower()}")
        print(f"framework_result_path={output['result_path']}")
        print(f"framework_learning_latest={output['learning_latest']}")
        if len(job_rows) > 1:
            print(f"framework_jobs_submitted={len(job_rows)}")
        _cont_surf = output.get("phase3_continuation_result") or {}
        if isinstance(_cont_surf, dict) and _cont_surf.get("ran"):
            _cont_action_str = str((_cont_surf.get("phase3_continuation_next_action") or {}).get("action") or "")
            print(f"phase3_continuation_ran=true")
            print(f"phase3_continuation_action={_cont_action_str}")
            print(f"phase3_continuation_exit_code={_exit}")
        _rec_out = output.get("phase3_recommendation_persisted")
        if _rec_out:
            print(f"phase3_recommendation_persisted={_rec_out}")
            _rec_query = str((output.get("phase3_recommendation") or {}).get("query") or "")
            print(f"phase3_recommendation_query={_rec_query}")
        _ep_out = output.get("phase3_edit_plan_persisted")
        if _ep_out:
            _ep_target = str((output.get("phase3_edit_plan") or {}).get("target_file") or "")
            _ep_ready = bool((output.get("phase3_edit_plan") or {}).get("plan_ready"))
            print(f"phase3_edit_plan_persisted={_ep_out}")
            print(f"phase3_edit_plan_target={_ep_target}")
            print(f"phase3_edit_plan_ready={str(_ep_ready).lower()}")
        _rq_persisted = output.get("phase3_retrieval_query_persisted")
        if _rq_persisted:
            print(f"phase3_retrieval_query_persisted={_rq_persisted}")
        _rq_injected = output.get("phase3_retrieval_query_injected") or ""
        if _rq_injected:
            print(f"phase3_retrieval_query_injected={_rq_injected[:80]}")
        _val = output.get("phase3_edit_plan_validation") or {}
        if _val:
            print(f"phase3_edit_plan_validation_status={_val.get('validation_status', '')}")
            print(f"phase3_edit_plan_old_text_found={str(_val.get('old_text_found', False)).lower()}")
            _em = str(_val.get("executor_message") or "")
            if _em:
                print(f"phase3_executor_message_ready=true")
                print(f"phase3_executor_message={_em[:120]}")
        _inv = output.get("phase3_stage3_manager_invocation") or {}
        if _inv:
            _inv_ready = bool(_inv.get("invocation_ready"))
            print(f"phase3_invocation_ready={str(_inv_ready).lower()}")
            _inv_persisted = output.get("phase3_stage3_manager_invocation_persisted", "")
            if _inv_persisted:
                print(f"phase3_stage3_invocation_persisted={_inv_persisted}")
            if _inv_ready:
                print(f"phase3_shell_command_preview={str(_inv.get('shell_command_preview') or '')[:200]}")
            else:
                print(f"phase3_invocation_blocked_reason={str(_inv.get('blocked_reason') or '')}")

    return _exit


if __name__ == "__main__":
    raise SystemExit(main())
