"""Introspection-only validation report for phase3_context_inject."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_context_inject_validation_report() -> dict:
    failures: list[str] = []
    importable = False
    empty_bundle_returns_empty = False
    no_query_returns_empty = False
    valid_bundle_produces_prompt = False
    classes_in_prompt = False
    functions_in_prompt = False
    loader_importable = False
    loader_missing_returns_empty = False
    template_dispatches = False
    all_contains = False
    bin_wires_persistence = False
    choices_ok = False

    try:
        from framework.framework_control_plane import _phase3_build_context_prompt
        importable = True
    except Exception as exc:
        failures.append(f"importable: {exc}")

    if importable:
        try:
            empty_bundle_returns_empty = _phase3_build_context_prompt({}) == ""
            if not empty_bundle_returns_empty:
                failures.append("empty_bundle_returns_empty: non-empty result on {}")
        except Exception as exc:
            failures.append(f"empty_bundle_returns_empty raised: {exc}")

        try:
            b = {"query": "", "total_files": 1, "files": [], "top_file": "",
                 "top_file_symbol_count": 0, "prompt_ready": False}
            no_query_returns_empty = _phase3_build_context_prompt(b) == ""
            if not no_query_returns_empty:
                failures.append("no_query_returns_empty: non-empty result on empty query")
        except Exception as exc:
            failures.append(f"no_query_returns_empty raised: {exc}")

        try:
            b = {
                "query": "foo",
                "total_files": 1,
                "total_symbols": 1,
                "files_with_symbols": 1,
                "files": [{"path": "x.py", "classes": ["Foo"], "functions": [],
                            "symbol_count": 1, "size_bytes": 10, "stdout_excerpt": ""}],
                "top_file": "x.py",
                "top_file_symbol_count": 1,
                "prompt_ready": True,
            }
            prompt = _phase3_build_context_prompt(b)
            valid_bundle_produces_prompt = bool(prompt) and "foo" in prompt
            if not valid_bundle_produces_prompt:
                failures.append(f"valid_bundle_produces_prompt: prompt={prompt!r}")
        except Exception as exc:
            failures.append(f"valid_bundle_produces_prompt raised: {exc}")

        try:
            b = {
                "query": "q", "total_files": 1, "total_symbols": 1, "files_with_symbols": 1,
                "files": [{"path": "x.py", "classes": ["BarClass"], "functions": [],
                            "symbol_count": 1, "size_bytes": 10, "stdout_excerpt": ""}],
                "top_file": "x.py", "top_file_symbol_count": 1, "prompt_ready": True,
            }
            prompt = _phase3_build_context_prompt(b)
            classes_in_prompt = "BarClass" in prompt
            if not classes_in_prompt:
                failures.append(f"classes_in_prompt: 'BarClass' not found in prompt")
        except Exception as exc:
            failures.append(f"classes_in_prompt raised: {exc}")

        try:
            b = {
                "query": "q", "total_files": 1, "total_symbols": 1, "files_with_symbols": 1,
                "files": [{"path": "x.py", "classes": [], "functions": ["baz_func"],
                            "symbol_count": 1, "size_bytes": 10, "stdout_excerpt": ""}],
                "top_file": "x.py", "top_file_symbol_count": 1, "prompt_ready": True,
            }
            prompt = _phase3_build_context_prompt(b)
            functions_in_prompt = "baz_func" in prompt
            if not functions_in_prompt:
                failures.append(f"functions_in_prompt: 'baz_func' not found in prompt")
        except Exception as exc:
            failures.append(f"functions_in_prompt raised: {exc}")

    try:
        from bin.framework_control_plane import _load_context_bundle
        loader_importable = True
    except Exception as exc:
        failures.append(f"loader_importable: {exc}")

    if loader_importable:
        try:
            result = _load_context_bundle(Path("/tmp/__nonexistent_cb__.json"))
            loader_missing_returns_empty = result == {}
            if not loader_missing_returns_empty:
                failures.append(f"loader_missing_returns_empty: got {result!r}")
        except Exception as exc:
            failures.append(f"loader_missing_returns_empty raised: {exc}")

    try:
        from bin.framework_control_plane import _template_payload
        tp = _template_payload("context_bundle_probe")
        template_dispatches = isinstance(tp, dict) and "phase2_typed_tools" in tp
        if not template_dispatches:
            failures.append(f"template_dispatches: got {tp!r}")
    except Exception as exc:
        failures.append(f"template_dispatches raised: {exc}")

    try:
        import framework.framework_control_plane as m
        all_contains = "_phase3_build_context_prompt" in m.__all__
        if not all_contains:
            failures.append("all_contains: not in __all__")
    except Exception as exc:
        failures.append(f"all_contains raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        bin_wires_persistence = "phase3_context_bundle_persisted" in source
        if not bin_wires_persistence:
            failures.append("bin_wires_persistence: key not found in bin source")
    except Exception as exc:
        failures.append(f"bin_wires_persistence raised: {exc}")

    try:
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "bin/framework_control_plane.py",
             "--task-template", "context_bundle_probe", "--help"],
            capture_output=True, cwd=str(repo_root), timeout=15,
        )
        choices_ok = result.returncode == 0
        if not choices_ok:
            failures.append(f"choices_ok: returncode={result.returncode}, stderr={result.stderr[:200]!r}")
    except Exception as exc:
        failures.append(f"choices_ok raised: {exc}")

    all_checks_pass = (
        importable and empty_bundle_returns_empty and no_query_returns_empty
        and valid_bundle_produces_prompt and classes_in_prompt and functions_in_prompt
        and loader_importable and loader_missing_returns_empty and template_dispatches
        and all_contains and bin_wires_persistence and choices_ok
        and not failures
    )

    return {
        "phase3_context_inject_check": "phase3_context_inject",
        "importable": importable,
        "empty_bundle_returns_empty": empty_bundle_returns_empty,
        "no_query_returns_empty": no_query_returns_empty,
        "valid_bundle_produces_prompt": valid_bundle_produces_prompt,
        "classes_in_prompt": classes_in_prompt,
        "functions_in_prompt": functions_in_prompt,
        "loader_importable": loader_importable,
        "loader_missing_returns_empty": loader_missing_returns_empty,
        "template_dispatches": template_dispatches,
        "all_contains": all_contains,
        "bin_wires_persistence": bin_wires_persistence,
        "choices_ok": choices_ok,
        "failures": failures,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_context_inject_validation_report()
    import json as _json
    print(_json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
