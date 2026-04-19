"""Introspection-only validation report for phase3_retrieval_consume."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_retrieval_consume_validation_report() -> dict:
    error_msg = ""
    derive_importable = False
    summary_importable = False
    derive_empty_input_ok = False
    derive_extracts_path_ok = False
    derive_deduplication_ok = False
    derive_max_files_ok = False
    summary_empty_ok = False
    summary_query_ok = False
    summary_read_targets_count_ok = False
    bin_imports_ok = False

    try:
        from framework.framework_control_plane import _phase2_derive_read_targets
        derive_importable = True
        from framework.framework_control_plane import _phase2_retrieval_summary
        summary_importable = True

        derive_empty_input_ok = _phase2_derive_read_targets([]) == []

        single = [
            {
                "tool_name": "search",
                "status": "executed",
                "structured_payload": {
                    "query": "_execute_job",
                    "match_count": 1,
                    "matches": [{"path": "framework/worker_runtime.py", "line_number": 10, "line_text": "x"}],
                    "matches_truncated_by_limit": False,
                },
                "stdout": "", "return_code": 0, "duration_ms": 1, "error": "",
            }
        ]
        targets = _phase2_derive_read_targets(single)
        derive_extracts_path_ok = (
            len(targets) == 1
            and targets[0]["contract_name"] == "read_file"
            and targets[0]["arguments"]["path"] == "framework/worker_runtime.py"
        )

        dedup_input = [
            {
                "tool_name": "search",
                "status": "executed",
                "structured_payload": {
                    "query": "x",
                    "match_count": 3,
                    "matches": [
                        {"path": "a.py", "line_number": 1, "line_text": ""},
                        {"path": "a.py", "line_number": 2, "line_text": ""},
                        {"path": "b.py", "line_number": 3, "line_text": ""},
                    ],
                    "matches_truncated_by_limit": False,
                },
                "stdout": "", "return_code": 0, "duration_ms": 1, "error": "",
            }
        ]
        dedup_targets = _phase2_derive_read_targets(dedup_input, max_files=5)
        derive_deduplication_ok = len(dedup_targets) == 2 and dedup_targets[0]["arguments"]["path"] == "a.py"

        many_matches = [
            {
                "tool_name": "search",
                "status": "executed",
                "structured_payload": {
                    "query": "x",
                    "match_count": 10,
                    "matches": [{"path": f"f{i}.py", "line_number": i, "line_text": ""} for i in range(10)],
                    "matches_truncated_by_limit": False,
                },
                "stdout": "", "return_code": 0, "duration_ms": 1, "error": "",
            }
        ]
        derive_max_files_ok = len(_phase2_derive_read_targets(many_matches, max_files=2)) == 2

        s_empty = _phase2_retrieval_summary([])
        summary_empty_ok = (
            s_empty["query"] == ""
            and s_empty["search_match_count"] == 0
            and s_empty["unique_file_paths"] == []
            and s_empty["top_match_file"] == ""
            and s_empty["read_targets_derived"] == 0
        )

        s_query = _phase2_retrieval_summary(single)
        summary_query_ok = s_query["query"] == "_execute_job"

        many_paths = [
            {
                "tool_name": "search",
                "status": "executed",
                "structured_payload": {
                    "query": "x",
                    "match_count": 5,
                    "matches": [{"path": f"f{i}.py", "line_number": i, "line_text": ""} for i in range(5)],
                    "matches_truncated_by_limit": False,
                },
                "stdout": "", "return_code": 0, "duration_ms": 1, "error": "",
            }
        ]
        s_count = _phase2_retrieval_summary(many_paths, max_files=3)
        summary_read_targets_count_ok = s_count["read_targets_derived"] == 3

        import importlib
        import importlib.util
        spec = importlib.util.find_spec("bin.framework_control_plane")
        if spec is None:
            bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
            source = bin_path.read_text(encoding="utf-8")
        else:
            source = Path(spec.origin).read_text(encoding="utf-8")
        bin_imports_ok = (
            "_phase2_derive_read_targets" in source
            and "_phase2_retrieval_summary" in source
            and "phase2_retrieval_read_targets" in source
            and "phase2_retrieval_summary" in source
        )

    except Exception as exc:
        error_msg = str(exc)

    all_checks_pass = (
        not error_msg
        and derive_importable
        and summary_importable
        and derive_empty_input_ok
        and derive_extracts_path_ok
        and derive_deduplication_ok
        and derive_max_files_ok
        and summary_empty_ok
        and summary_query_ok
        and summary_read_targets_count_ok
        and bin_imports_ok
    )

    return {
        "phase3_retrieval_consume_check": "phase3_retrieval_consume",
        "derive_importable": derive_importable,
        "summary_importable": summary_importable,
        "derive_empty_input_ok": derive_empty_input_ok,
        "derive_extracts_path_ok": derive_extracts_path_ok,
        "derive_deduplication_ok": derive_deduplication_ok,
        "derive_max_files_ok": derive_max_files_ok,
        "summary_empty_ok": summary_empty_ok,
        "summary_query_ok": summary_query_ok,
        "summary_read_targets_count_ok": summary_read_targets_count_ok,
        "bin_imports_ok": bin_imports_ok,
        "error": error_msg,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_retrieval_consume_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
