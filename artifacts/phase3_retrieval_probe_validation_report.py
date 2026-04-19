"""Introspection-only validation report for phase3_retrieval_probe."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_retrieval_probe_validation_report() -> dict:
    error_msg = ""
    template_importable = False
    search_contract_present = False
    repo_map_contract_present = False
    apply_patch_contract_present = False
    search_query_correct = False
    repo_map_path_correct = False
    build_job_has_three_typed_tools = False
    retrieval_probe_in_choices = False

    try:
        from bin.framework_control_plane import _retrieval_probe_template, build_job, parse_args
        import argparse

        template_importable = True

        t = _retrieval_probe_template()
        tools = t.get("phase2_typed_tools") or []
        names = {e.get("contract_name", "") for e in tools if isinstance(e, dict)}

        search_contract_present = "search" in names
        repo_map_contract_present = "repo_map" in names
        apply_patch_contract_present = "apply_patch" in names

        for e in tools:
            if e.get("contract_name") == "search":
                search_query_correct = e.get("arguments", {}).get("query") == "_execute_job"
            if e.get("contract_name") == "repo_map":
                repo_map_path_correct = e.get("arguments", {}).get("path") == "framework"

        probe_args = argparse.Namespace(
            task_template="retrieval_probe",
            shell_command="",
            requested_output=[],
            artifact_input=[],
            priority="p1",
            inference_prompt="",
            inference_mode="heuristic",
            inference_replay="",
            retry_budget=0,
            retry_backoff_seconds=0,
            auto_escalate=False,
            task_portfolio="none",
            task_class="validation_check_execution",
        )
        job = build_job(probe_args)
        probe_tools = job.metadata.get("phase2_typed_tools") or []
        build_job_has_three_typed_tools = len(probe_tools) == 3

        try:
            with patch.object(sys, "argv", ["framework_control_plane.py", "--task-template", "retrieval_probe"]):
                parsed = parse_args()
            retrieval_probe_in_choices = parsed.task_template == "retrieval_probe"
        except SystemExit:
            retrieval_probe_in_choices = False

    except Exception as exc:
        error_msg = str(exc)

    all_checks_pass = (
        not error_msg
        and template_importable
        and search_contract_present
        and repo_map_contract_present
        and apply_patch_contract_present
        and search_query_correct
        and repo_map_path_correct
        and build_job_has_three_typed_tools
        and retrieval_probe_in_choices
    )

    return {
        "phase3_retrieval_probe_check": "phase3_retrieval_probe",
        "template_importable": template_importable,
        "search_contract_present": search_contract_present,
        "repo_map_contract_present": repo_map_contract_present,
        "apply_patch_contract_present": apply_patch_contract_present,
        "search_query_correct": search_query_correct,
        "repo_map_path_correct": repo_map_path_correct,
        "build_job_has_three_typed_tools": build_job_has_three_typed_tools,
        "retrieval_probe_in_choices": retrieval_probe_in_choices,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_retrieval_probe_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
