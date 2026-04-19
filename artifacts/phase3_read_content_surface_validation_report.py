"""Introspection-only validation report for phase3_read_content_surface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_read_content_surface_validation_report() -> dict:
    failures: list[str] = []
    extract_importable = False
    summary_importable = False
    extract_empty_ok = False
    extract_read_file_ok = False
    extract_non_read_excluded = False
    summary_keys_ok = False
    summary_counts_ok = False
    main_wires_read_content = False
    error_msg = ""

    try:
        from framework.framework_control_plane import _phase3_extract_read_content
        extract_importable = True
    except Exception as exc:
        failures.append(f"extract_importable: {exc}")

    try:
        from framework.framework_control_plane import _phase3_read_content_summary
        summary_importable = True
    except Exception as exc:
        failures.append(f"summary_importable: {exc}")

    if extract_importable:
        try:
            result = _phase3_extract_read_content([])
            extract_empty_ok = result == []
            if not extract_empty_ok:
                failures.append(f"extract_empty_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"extract_empty_ok raised: {exc}")

        try:
            obs = {
                "tool_name": "read_file",
                "status": "executed",
                "stdout": "file content",
                "structured_payload": {"path": "framework/x.py", "size_bytes": 12},
                "duration_ms": 5,
                "error": "",
                "return_code": 0,
            }
            result = _phase3_extract_read_content([obs])
            extract_read_file_ok = (
                len(result) == 1
                and result[0]["path"] == "framework/x.py"
                and result[0]["stdout"] == "file content"
                and result[0]["size_bytes"] == 12
            )
            if not extract_read_file_ok:
                failures.append(f"extract_read_file_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"extract_read_file_ok raised: {exc}")

        try:
            search_obs = {
                "tool_name": "search",
                "status": "executed",
                "stdout": "",
                "structured_payload": {"matches": []},
                "duration_ms": 1,
                "error": "",
                "return_code": 0,
            }
            result = _phase3_extract_read_content([search_obs])
            extract_non_read_excluded = result == []
            if not extract_non_read_excluded:
                failures.append(f"extract_non_read_excluded: got {result!r}")
        except Exception as exc:
            failures.append(f"extract_non_read_excluded raised: {exc}")

    if summary_importable:
        try:
            required_keys = {"files_read", "file_paths", "total_bytes", "top_file", "top_file_bytes", "any_errors"}
            s = _phase3_read_content_summary([])
            summary_keys_ok = set(s.keys()) == required_keys
            if not summary_keys_ok:
                failures.append(f"summary_keys_ok: got keys {set(s.keys())!r}")
        except Exception as exc:
            failures.append(f"summary_keys_ok raised: {exc}")

        try:
            obs1 = {
                "tool_name": "read_file", "status": "executed",
                "stdout": "abc", "structured_payload": {"path": "a.py", "size_bytes": 3},
                "duration_ms": 1, "error": "", "return_code": 0,
            }
            obs2 = {
                "tool_name": "read_file", "status": "executed",
                "stdout": "de", "structured_payload": {"path": "b.py", "size_bytes": 2},
                "duration_ms": 1, "error": "", "return_code": 0,
            }
            s = _phase3_read_content_summary([obs1, obs2])
            summary_counts_ok = s["files_read"] == 2 and s["total_bytes"] == 5
            if not summary_counts_ok:
                failures.append(f"summary_counts_ok: files_read={s['files_read']}, total_bytes={s['total_bytes']}")
        except Exception as exc:
            failures.append(f"summary_counts_ok raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        main_wires_read_content = (
            "_phase3_extract_read_content" in source
            and "_phase3_read_content_summary" in source
            and "phase3_read_content_results" in source
            and "phase3_read_content_summary" in source
        )
        if not main_wires_read_content:
            failures.append("main_wires_read_content: one or more expected names absent from bin source")
    except Exception as exc:
        failures.append(f"main_wires_read_content raised: {exc}")

    all_checks_pass = (
        extract_importable
        and summary_importable
        and extract_empty_ok
        and extract_read_file_ok
        and extract_non_read_excluded
        and summary_keys_ok
        and summary_counts_ok
        and main_wires_read_content
        and not failures
    )

    return {
        "phase3_read_content_surface_check": "phase3_read_content_surface",
        "extract_importable": extract_importable,
        "summary_importable": summary_importable,
        "extract_empty_ok": extract_empty_ok,
        "extract_read_file_ok": extract_read_file_ok,
        "extract_non_read_excluded": extract_non_read_excluded,
        "summary_keys_ok": summary_keys_ok,
        "summary_counts_ok": summary_counts_ok,
        "main_wires_read_content": main_wires_read_content,
        "failures": failures,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_read_content_surface_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
