"""Introspection-only validation report for phase3_context_bundle."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_context_bundle_validation_report() -> dict:
    failures: list[str] = []
    importable = False
    empty_inputs_ok = False
    total_files_ok = False
    total_symbols_ok = False
    top_file_ok = False
    prompt_ready_true_ok = False
    prompt_ready_false_no_query_ok = False
    join_ok = False
    all_contains = False
    bin_wires_context_bundle = False

    _BUNDLE_KEYS = {"query", "total_files", "total_symbols", "files_with_symbols",
                    "files", "top_file", "top_file_symbol_count", "prompt_ready"}

    try:
        from framework.framework_control_plane import _phase3_assemble_context_bundle
        importable = True
    except Exception as exc:
        failures.append(f"importable: {exc}")

    if importable:
        try:
            b = _phase3_assemble_context_bundle({}, [], [])
            empty_inputs_ok = (
                set(b.keys()) == _BUNDLE_KEYS
                and b["total_files"] == 0
                and b["total_symbols"] == 0
                and b["files"] == []
                and b["top_file"] == ""
                and b["prompt_ready"] is False
            )
            if not empty_inputs_ok:
                failures.append(f"empty_inputs_ok: got {b!r}")
        except Exception as exc:
            failures.append(f"empty_inputs_ok raised: {exc}")

        def _sym(path, classes=None, functions=None):
            c = list(classes or [])
            f = list(functions or [])
            return {"path": path, "classes": c, "functions": f, "symbol_count": len(c) + len(f)}

        try:
            syms = [_sym("a.py", classes=["A"]), _sym("b.py", functions=["f"])]
            b = _phase3_assemble_context_bundle({}, [], syms)
            total_files_ok = b["total_files"] == 2
            if not total_files_ok:
                failures.append(f"total_files_ok: got {b['total_files']}")
        except Exception as exc:
            failures.append(f"total_files_ok raised: {exc}")

        try:
            syms = [_sym("a.py", classes=["A", "B"], functions=["f"]),
                    _sym("b.py", functions=["g", "h"])]
            b = _phase3_assemble_context_bundle({}, [], syms)
            total_symbols_ok = b["total_symbols"] == 5
            if not total_symbols_ok:
                failures.append(f"total_symbols_ok: got {b['total_symbols']}")
        except Exception as exc:
            failures.append(f"total_symbols_ok raised: {exc}")

        try:
            syms = [_sym("a.py", classes=["X"]), _sym("b.py", classes=["Y", "Z"], functions=["f"])]
            b = _phase3_assemble_context_bundle({"query": "q"}, [], syms)
            top_file_ok = b["top_file"] == "b.py" and b["top_file_symbol_count"] == 3
            if not top_file_ok:
                failures.append(f"top_file_ok: top_file={b['top_file']!r}, count={b['top_file_symbol_count']}")
        except Exception as exc:
            failures.append(f"top_file_ok raised: {exc}")

        try:
            syms = [_sym("a.py", classes=["A"])]
            b = _phase3_assemble_context_bundle({"query": "myquery"}, [], syms)
            prompt_ready_true_ok = b["prompt_ready"] is True
            if not prompt_ready_true_ok:
                failures.append(f"prompt_ready_true_ok: got {b['prompt_ready']!r}")
        except Exception as exc:
            failures.append(f"prompt_ready_true_ok raised: {exc}")

        try:
            syms = [_sym("a.py", classes=["A"])]
            b = _phase3_assemble_context_bundle({"query": ""}, [], syms)
            prompt_ready_false_no_query_ok = b["prompt_ready"] is False
            if not prompt_ready_false_no_query_ok:
                failures.append(f"prompt_ready_false_no_query_ok: got {b['prompt_ready']!r}")
        except Exception as exc:
            failures.append(f"prompt_ready_false_no_query_ok raised: {exc}")

        try:
            rcs = [{"path": "x.py", "stdout": "hello world", "size_bytes": 42,
                    "structured_payload": {}, "duration_ms": 1, "error": ""}]
            syms = [_sym("x.py", classes=["Foo"])]
            b = _phase3_assemble_context_bundle({"query": "q"}, rcs, syms)
            join_ok = (
                b["files"][0]["size_bytes"] == 42
                and b["files"][0]["stdout_excerpt"] == "hello world"
            )
            if not join_ok:
                failures.append(f"join_ok: files={b['files']!r}")
        except Exception as exc:
            failures.append(f"join_ok raised: {exc}")

        try:
            import framework.framework_control_plane as m
            all_contains = "_phase3_assemble_context_bundle" in m.__all__
            if not all_contains:
                failures.append("all_contains: not in __all__")
        except Exception as exc:
            failures.append(f"all_contains raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        bin_wires_context_bundle = "phase3_context_bundle" in source
        if not bin_wires_context_bundle:
            failures.append("bin_wires_context_bundle: 'phase3_context_bundle' not found in bin source")
    except Exception as exc:
        failures.append(f"bin_wires_context_bundle raised: {exc}")

    all_checks_pass = (
        importable and empty_inputs_ok and total_files_ok and total_symbols_ok
        and top_file_ok and prompt_ready_true_ok and prompt_ready_false_no_query_ok
        and join_ok and all_contains and bin_wires_context_bundle
        and not failures
    )

    return {
        "phase3_context_bundle_check": "phase3_context_bundle",
        "importable": importable,
        "empty_inputs_ok": empty_inputs_ok,
        "total_files_ok": total_files_ok,
        "total_symbols_ok": total_symbols_ok,
        "top_file_ok": top_file_ok,
        "prompt_ready_true_ok": prompt_ready_true_ok,
        "prompt_ready_false_no_query_ok": prompt_ready_false_no_query_ok,
        "join_ok": join_ok,
        "all_contains": all_contains,
        "bin_wires_context_bundle": bin_wires_context_bundle,
        "failures": failures,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_context_bundle_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
