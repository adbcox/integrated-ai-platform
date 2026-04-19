"""Introspection-only validation report for phase3_symbol_index."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_symbol_index_validation_report() -> dict:
    failures: list[str] = []
    importable = False
    empty_input_ok = False
    no_symbols_ok = False
    class_extraction_ok = False
    def_extraction_ok = False
    dedup_ok = False
    all_contains = False
    bin_wires_symbol_index = False

    try:
        from framework.framework_control_plane import _phase3_extract_symbol_index
        importable = True
    except Exception as exc:
        failures.append(f"importable: {exc}")

    if importable:
        try:
            result = _phase3_extract_symbol_index([])
            empty_input_ok = result == []
            if not empty_input_ok:
                failures.append(f"empty_input_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"empty_input_ok raised: {exc}")

        try:
            entry = {"path": "x.py", "stdout": "", "size_bytes": 0,
                     "structured_payload": {}, "duration_ms": 0, "error": ""}
            result = _phase3_extract_symbol_index([entry])
            no_symbols_ok = (
                len(result) == 1
                and result[0]["classes"] == []
                and result[0]["functions"] == []
                and result[0]["symbol_count"] == 0
            )
            if not no_symbols_ok:
                failures.append(f"no_symbols_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"no_symbols_ok raised: {exc}")

        try:
            entry = {"path": "x.py", "stdout": "class Foo:\n    pass\n",
                     "size_bytes": 0, "structured_payload": {}, "duration_ms": 0, "error": ""}
            result = _phase3_extract_symbol_index([entry])
            class_extraction_ok = (
                len(result) == 1
                and "Foo" in result[0]["classes"]
                and result[0]["symbol_count"] >= 1
            )
            if not class_extraction_ok:
                failures.append(f"class_extraction_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"class_extraction_ok raised: {exc}")

        try:
            entry = {"path": "x.py", "stdout": "def bar():\n    pass\n",
                     "size_bytes": 0, "structured_payload": {}, "duration_ms": 0, "error": ""}
            result = _phase3_extract_symbol_index([entry])
            def_extraction_ok = (
                len(result) == 1
                and "bar" in result[0]["functions"]
                and result[0]["symbol_count"] >= 1
            )
            if not def_extraction_ok:
                failures.append(f"def_extraction_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"def_extraction_ok raised: {exc}")

        try:
            entry = {"path": "x.py", "stdout": "class X:\nclass X:\n",
                     "size_bytes": 0, "structured_payload": {}, "duration_ms": 0, "error": ""}
            result = _phase3_extract_symbol_index([entry])
            dedup_ok = (
                len(result) == 1
                and result[0]["classes"] == ["X"]
            )
            if not dedup_ok:
                failures.append(f"dedup_ok: got {result!r}")
        except Exception as exc:
            failures.append(f"dedup_ok raised: {exc}")

        try:
            import framework.framework_control_plane as m
            all_contains = "_phase3_extract_symbol_index" in m.__all__
            if not all_contains:
                failures.append("all_contains: not in __all__")
        except Exception as exc:
            failures.append(f"all_contains raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        bin_wires_symbol_index = "phase3_symbol_index" in source
        if not bin_wires_symbol_index:
            failures.append("bin_wires_symbol_index: 'phase3_symbol_index' not found in bin source")
    except Exception as exc:
        failures.append(f"bin_wires_symbol_index raised: {exc}")

    all_checks_pass = (
        importable
        and empty_input_ok
        and no_symbols_ok
        and class_extraction_ok
        and def_extraction_ok
        and dedup_ok
        and all_contains
        and bin_wires_symbol_index
        and not failures
    )

    return {
        "phase3_symbol_index_check": "phase3_symbol_index",
        "importable": importable,
        "empty_input_ok": empty_input_ok,
        "no_symbols_ok": no_symbols_ok,
        "class_extraction_ok": class_extraction_ok,
        "def_extraction_ok": def_extraction_ok,
        "dedup_ok": dedup_ok,
        "all_contains": all_contains,
        "bin_wires_symbol_index": bin_wires_symbol_index,
        "failures": failures,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_symbol_index_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
