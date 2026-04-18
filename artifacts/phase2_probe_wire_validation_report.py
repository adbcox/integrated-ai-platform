"""Introspection-only validation report for phase2_probe_wire."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bin.framework_control_plane import _typed_tool_probe_template, build_job


def generate_phase2_probe_wire_validation_report() -> dict:
    error_msg = ""
    template_has_phase2_typed_tools = False
    read_file_contract_present = False
    apply_patch_contract_present = False
    build_job_passes_phase2_typed_tools = False
    none_template_has_empty_typed_tools = False

    try:
        t = _typed_tool_probe_template()
        tools = t.get("phase2_typed_tools") or []
        template_has_phase2_typed_tools = isinstance(tools, list) and bool(tools)
        names = {spec.get("contract_name", "") for spec in tools if isinstance(spec, dict)}
        read_file_contract_present = "read_file" in names
        apply_patch_contract_present = "apply_patch" in names

        probe_args = argparse.Namespace(
            task_template="typed_tool_probe",
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
        probe_tools = job.metadata.get("phase2_typed_tools")
        build_job_passes_phase2_typed_tools = isinstance(probe_tools, list) and bool(probe_tools)

        none_args = argparse.Namespace(
            task_template="none",
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
            task_class="framework_bootstrap",
        )
        none_job = build_job(none_args)
        none_template_has_empty_typed_tools = none_job.metadata.get("phase2_typed_tools") == []
    except Exception as exc:
        error_msg = str(exc)

    all_checks_pass = (
        not error_msg
        and template_has_phase2_typed_tools
        and read_file_contract_present
        and apply_patch_contract_present
        and build_job_passes_phase2_typed_tools
        and none_template_has_empty_typed_tools
    )

    return {
        "phase2_probe_wire_check": "phase2_probe_wire",
        "template_has_phase2_typed_tools": template_has_phase2_typed_tools,
        "read_file_contract_present": read_file_contract_present,
        "apply_patch_contract_present": apply_patch_contract_present,
        "build_job_passes_phase2_typed_tools": build_job_passes_phase2_typed_tools,
        "none_template_has_empty_typed_tools": none_template_has_empty_typed_tools,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase2_probe_wire_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
