"""Phase 2 typed tool impl-2 validation report (SEARCH, REPO_MAP).

Drives run_phase2_typed_tool_impl_2_validation on both allow_all_tools=True
and allow_all_tools=False paths, asserts both required tools appear in the
allowed trace, and confirms at least one blocked observation in the blocked
trace.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def generate_phase2_tool_impl_2_validation_report() -> dict:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    from framework.runtime_validation_pack import (
        REQUIRED_PHASE2_TYPED_TOOLS_IMPL_2,
        run_phase2_typed_tool_impl_2_validation,
    )

    tools_observed_allowed: list[str] = []
    tools_observed_blocked: list[str] = []
    error_msg = ""

    try:
        with tempfile.TemporaryDirectory(prefix="p2_tool_impl2_allow_") as d_allow:
            allow_result = run_phase2_typed_tool_impl_2_validation(
                base_root=Path(d_allow),
                allow_all_tools=True,
            )

        typed_trace_allow = allow_result.get("typed_tool_trace", [])
        for entry in typed_trace_allow:
            if entry.get("kind") == "tool_observation":
                name = entry.get("tool_name")
                if name and name not in tools_observed_allowed:
                    tools_observed_allowed.append(name)

        with tempfile.TemporaryDirectory(prefix="p2_tool_impl2_block_") as d_block:
            block_result = run_phase2_typed_tool_impl_2_validation(
                base_root=Path(d_block),
                allow_all_tools=False,
            )

        typed_trace_block = block_result.get("typed_tool_trace", [])
        for entry in typed_trace_block:
            if entry.get("kind") == "tool_observation":
                name = entry.get("tool_name")
                if name and name not in tools_observed_blocked:
                    tools_observed_blocked.append(name)

    except Exception as exc:
        error_msg = str(exc)

    required = list(REQUIRED_PHASE2_TYPED_TOOLS_IMPL_2)
    allowed_payload_ok = all(t in tools_observed_allowed for t in required)

    blocked_obs = []
    try:
        for entry in block_result.get("typed_tool_trace", []):  # type: ignore[possibly-undefined]
            if (
                entry.get("kind") == "tool_observation"
                and entry.get("status") == "blocked"
                and entry.get("allowed") is False
            ):
                blocked_obs.append(entry)
    except Exception:
        pass
    blocked_payload_ok = len(blocked_obs) >= 1

    all_checks_pass = (
        not error_msg
        and allowed_payload_ok
        and blocked_payload_ok
    )

    return {
        "phase2_tool_impl_2_check": "phase2_tool_impl_2",
        "required_tools": required,
        "tools_observed_allowed": sorted(tools_observed_allowed),
        "tools_observed_blocked": sorted(tools_observed_blocked),
        "allowed_payload_ok": allowed_payload_ok,
        "blocked_payload_ok": blocked_payload_ok,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    import json

    report = generate_phase2_tool_impl_2_validation_report()
    print(json.dumps(report, indent=2))
    if not report["all_checks_pass"]:
        print("\nFAIL: some checks did not pass.", file=sys.stderr)
        sys.exit(1)
    print("\nPASS: all_checks_pass=True")
