"""Phase 2 typed tool implementation validation report.

Drives run_phase2_typed_tool_validation on both allow_all_tools=True and
allow_all_tools=False paths, asserts all four required tools appear in the
allowed trace, and confirms at least one blocked observation exists in the
blocked trace.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def generate_phase2_tool_impl_validation_report() -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from framework.runtime_validation_pack import (
        REQUIRED_PHASE2_TYPED_TOOLS,
        run_phase2_typed_tool_validation,
    )

    checks: list[dict] = []
    all_pass = True

    def _record(name: str, passed: bool, detail: str = "") -> None:
        nonlocal all_pass
        checks.append({"check": name, "passed": passed, "detail": detail})
        if not passed:
            all_pass = False

    with tempfile.TemporaryDirectory(prefix="p2_tool_impl_allow_") as d_allow:
        allow_result = run_phase2_typed_tool_validation(
            allow_all_tools=True,
            tmp_root=Path(d_allow),
        )

    typed_trace_allow = allow_result.get("typed_tool_trace", [])
    observed_tools_allow = {
        entry.get("tool_name")
        for entry in typed_trace_allow
        if entry.get("kind") == "tool_observation"
    }
    for required_tool in REQUIRED_PHASE2_TYPED_TOOLS:
        present = required_tool in observed_tools_allow
        _record(
            f"allow_trace_has_{required_tool}",
            present,
            f"observed_tools={sorted(observed_tools_allow)}",
        )

    allow_status = allow_result.get("final_outcome")
    _record(
        "allow_job_completed",
        allow_status == "completed",
        f"final_outcome={allow_status}",
    )

    with tempfile.TemporaryDirectory(prefix="p2_tool_impl_block_") as d_block:
        block_result = run_phase2_typed_tool_validation(
            allow_all_tools=False,
            tmp_root=Path(d_block),
        )

    typed_trace_block = block_result.get("typed_tool_trace", [])
    blocked_obs = [
        e for e in typed_trace_block
        if e.get("kind") == "tool_observation"
        and e.get("status") == "blocked"
        and e.get("allowed") is False
    ]
    _record(
        "block_trace_has_at_least_one_blocked_observation",
        len(blocked_obs) >= 1,
        f"blocked_count={len(blocked_obs)}",
    )

    bundle_allow = allow_result.get("session_bundle")
    if isinstance(bundle_allow, dict):
        bundle_tool_trace = bundle_allow.get("tool_trace", [])
        bundle_tool_names = {e.get("tool_name") for e in bundle_tool_trace}
        for required_tool in REQUIRED_PHASE2_TYPED_TOOLS:
            present = required_tool in bundle_tool_names
            _record(
                f"session_bundle_tool_trace_has_{required_tool}",
                present,
                f"bundle_tool_names={sorted(bundle_tool_names)}",
            )
    else:
        _record("session_bundle_present", False, "session_bundle missing or wrong type")

    report = {
        "all_checks_pass": all_pass,
        "checks": checks,
        "allow_final_outcome": allow_result.get("final_outcome"),
        "block_final_outcome": block_result.get("final_outcome"),
        "required_tools": list(REQUIRED_PHASE2_TYPED_TOOLS),
    }
    return report


if __name__ == "__main__":
    import json

    report = generate_phase2_tool_impl_validation_report()
    print(json.dumps(report, indent=2))
    if not report["all_checks_pass"]:
        print("\nFAIL: some checks did not pass.", file=sys.stderr)
        sys.exit(1)
    print("\nPASS: all_checks_pass=True")
