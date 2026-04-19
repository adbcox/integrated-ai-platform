#!/usr/bin/env python3
"""Standalone validation report for PHASE2-RESULTS-WIRE-1.

Introspection-only: no live runtime required.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def generate_phase2_results_wire_validation_report() -> dict:
    failures: list[str] = []

    # 1. extractor importable
    extractor_importable = False
    try:
        from framework.framework_control_plane import _phase2_extract_typed_results
        extractor_importable = True
    except ImportError as exc:
        failures.append(f"extractor_import_failed: {exc}")

    # 2. empty_payload_ok
    empty_payload_ok = False
    if extractor_importable:
        try:
            result = _phase2_extract_typed_results({})
            empty_payload_ok = result == []
            if not empty_payload_ok:
                failures.append(f"empty_payload: expected [] got {result!r}")
        except Exception as exc:
            failures.append(f"empty_payload_raised: {exc}")

    # 3. observation_extraction_ok
    observation_extraction_ok = False
    if extractor_importable:
        try:
            trace = [
                {
                    "kind": "tool_observation",
                    "tool_name": "read_file",
                    "status": "executed",
                    "stdout": "hello world",
                    "structured_payload": {"path": "/x", "size_bytes": 11},
                    "return_code": 0,
                    "duration_ms": 7,
                    "error": "",
                }
            ]
            result = _phase2_extract_typed_results({"typed_tool_trace": trace})
            ok = (
                len(result) == 1
                and result[0]["tool_name"] == "read_file"
                and result[0]["stdout"] == "hello world"
                and result[0]["structured_payload"] == {"path": "/x", "size_bytes": 11}
                and result[0]["return_code"] == 0
                and result[0]["duration_ms"] == 7
            )
            observation_extraction_ok = ok
            if not ok:
                failures.append(f"observation_extraction: unexpected result {result!r}")
        except Exception as exc:
            failures.append(f"observation_extraction_raised: {exc}")

    # 4. action_exclusion_ok
    action_exclusion_ok = False
    if extractor_importable:
        try:
            trace = [
                {"kind": "tool_action", "tool_name": "read_file"},
                {"kind": "tool_observation", "tool_name": "apply_patch", "status": "executed"},
            ]
            result = _phase2_extract_typed_results({"typed_tool_trace": trace})
            action_exclusion_ok = (
                len(result) == 1 and result[0]["tool_name"] == "apply_patch"
            )
            if not action_exclusion_ok:
                failures.append(f"action_exclusion: unexpected result {result!r}")
        except Exception as exc:
            failures.append(f"action_exclusion_raised: {exc}")

    # 5. bin_import_ok (regression guard)
    bin_import_ok = False
    try:
        from bin.framework_control_plane import _compute_phase2_exit_code  # noqa: F401
        bin_import_ok = True
    except ImportError as exc:
        failures.append(f"bin_import_failed: {exc}")

    # 6. __all__ contains extractor
    all_contains_extractor = False
    try:
        import framework.framework_control_plane as fcp
        all_contains_extractor = "_phase2_extract_typed_results" in fcp.__all__
        if not all_contains_extractor:
            failures.append("__all__ missing _phase2_extract_typed_results")
    except Exception as exc:
        failures.append(f"all_check_raised: {exc}")

    all_checks_pass = len(failures) == 0
    return {
        "status": "pass" if all_checks_pass else "fail",
        "all_checks_pass": all_checks_pass,
        "extractor_importable": extractor_importable,
        "empty_payload_ok": empty_payload_ok,
        "observation_extraction_ok": observation_extraction_ok,
        "action_exclusion_ok": action_exclusion_ok,
        "bin_import_ok": bin_import_ok,
        "all_contains_extractor": all_contains_extractor,
        "failures": failures,
    }


if __name__ == "__main__":
    import json

    report = generate_phase2_results_wire_validation_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_checks_pass"]:
        sys.exit(1)
