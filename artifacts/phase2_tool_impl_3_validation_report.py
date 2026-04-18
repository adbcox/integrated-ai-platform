"""Validation report for phase2_tool_impl_3: apply_patch and publish_artifact."""

from __future__ import annotations

import tempfile
from pathlib import Path

from framework.runtime_validation_pack import (
    REQUIRED_PHASE2_TYPED_TOOLS_IMPL_3,
    run_phase2_typed_tool_impl_3_validation,
)
from framework.tool_action_observation_contract import ToolContractStatus


def generate_phase2_tool_impl_3_validation_report() -> dict:
    with tempfile.TemporaryDirectory(prefix="p2_impl3_report_allow_") as tmp_allow:
        allow_result = run_phase2_typed_tool_impl_3_validation(
            base_root=tmp_allow,
            session_id="phase2-tool-impl-3-report-allow",
            allow_all_tools=True,
        )

    with tempfile.TemporaryDirectory(prefix="p2_impl3_report_block_") as tmp_block:
        block_result = run_phase2_typed_tool_impl_3_validation(
            base_root=tmp_block,
            session_id="phase2-tool-impl-3-report-block",
            allow_all_tools=False,
        )

    allow_trace = (allow_result.get("session_bundle") or {}).get("tool_trace") or []
    block_trace = (block_result.get("session_bundle") or {}).get("tool_trace") or []

    tools_observed_allowed = [
        r.get("tool_name") or r.get("contract_name")
        for r in allow_trace
        if (r.get("status") == ToolContractStatus.EXECUTED.value or r.get("allowed") is True)
    ]

    allowed_payload_ok = bool(
        any(t == "apply_patch" for t in tools_observed_allowed)
        and any(t == "publish_artifact" for t in tools_observed_allowed)
    )

    blocked_payload_ok = bool(
        any(
            r.get("status") == ToolContractStatus.BLOCKED.value and r.get("allowed") is False
            for r in block_trace
        )
    )

    all_checks_pass = allowed_payload_ok and blocked_payload_ok

    return {
        "status": "pass" if all_checks_pass else "fail",
        "all_checks_pass": all_checks_pass,
        "allowed_payload_ok": allowed_payload_ok,
        "blocked_payload_ok": blocked_payload_ok,
        "required_tools": list(REQUIRED_PHASE2_TYPED_TOOLS_IMPL_3),
        "tools_observed_allowed": tools_observed_allowed,
        "allow_trace_count": len(allow_trace),
        "block_trace_count": len(block_trace),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(generate_phase2_tool_impl_3_validation_report(), indent=2))
