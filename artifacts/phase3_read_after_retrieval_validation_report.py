#!/usr/bin/env python3
"""Standalone validation report for PHASE3-READ-AFTER-RETRIEVAL-1.

Introspection-only: no live runtime required.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def generate_phase3_read_after_retrieval_validation_report() -> dict:
    failures: list[str] = []

    # 1. _load_retrieval_targets importable
    loader_importable = False
    try:
        from bin.framework_control_plane import _load_retrieval_targets
        loader_importable = True
    except ImportError as exc:
        failures.append(f"loader_import_failed: {exc}")

    # 2. _read_after_retrieval_template importable
    template_importable = False
    try:
        from bin.framework_control_plane import _read_after_retrieval_template
        template_importable = True
    except ImportError as exc:
        failures.append(f"template_import_failed: {exc}")

    # 3. load_missing_file_returns_empty
    load_missing_ok = False
    if loader_importable:
        try:
            result = _load_retrieval_targets(Path("/tmp/__nonexistent_phase3_rar__.json"))
            load_missing_ok = result == []
            if not load_missing_ok:
                failures.append(f"load_missing: expected [] got {result!r}")
        except Exception as exc:
            failures.append(f"load_missing_raised: {exc}")

    # 4. load_valid_file_returns_specs
    load_valid_ok = False
    if loader_importable:
        try:
            specs = [{"contract_name": "read_file", "arguments": {"path": "/x.py"}}]
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
                json.dump(specs, f)
                p = Path(f.name)
            result = _load_retrieval_targets(p)
            load_valid_ok = result == specs
            if not load_valid_ok:
                failures.append(f"load_valid: expected {specs!r} got {result!r}")
        except Exception as exc:
            failures.append(f"load_valid_raised: {exc}")

    # 5. template_with_no_targets_has_apply_patch_only
    template_no_targets_ok = False
    if template_importable:
        try:
            tmpl = _read_after_retrieval_template(
                targets_path=Path("/tmp/__nonexistent_phase3_tmpl__.json")
            )
            tools = tmpl.get("phase2_typed_tools") or []
            template_no_targets_ok = (
                len(tools) == 1 and tools[0].get("contract_name") == "apply_patch"
            )
            if not template_no_targets_ok:
                failures.append(f"template_no_targets: unexpected tools={tools!r}")
        except Exception as exc:
            failures.append(f"template_no_targets_raised: {exc}")

    # 6. template_with_targets_prepends_read_specs
    template_with_targets_ok = False
    if template_importable and loader_importable:
        try:
            specs = [{"contract_name": "read_file", "arguments": {"path": "/a.py"}}]
            with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
                json.dump(specs, f)
                p = Path(f.name)
            tmpl = _read_after_retrieval_template(targets_path=p)
            tools = tmpl.get("phase2_typed_tools") or []
            template_with_targets_ok = (
                len(tools) == 2
                and tools[0].get("contract_name") == "read_file"
                and tools[-1].get("contract_name") == "apply_patch"
            )
            if not template_with_targets_ok:
                failures.append(f"template_with_targets: unexpected tools={tools!r}")
        except Exception as exc:
            failures.append(f"template_with_targets_raised: {exc}")

    # 7. _template_payload dispatches read_after_retrieval
    dispatch_ok = False
    try:
        from bin.framework_control_plane import _template_payload
        payload = _template_payload("read_after_retrieval")
        dispatch_ok = "phase2_typed_tools" in payload and isinstance(payload["phase2_typed_tools"], list)
        if not dispatch_ok:
            failures.append(f"dispatch: payload={payload!r}")
    except Exception as exc:
        failures.append(f"dispatch_raised: {exc}")

    # 8. read_after_retrieval in argparse choices
    choices_ok = False
    try:
        import subprocess
        result_proc = subprocess.run(
            [sys.executable, "bin/framework_control_plane.py", "--task-template", "read_after_retrieval", "--help"],
            capture_output=True,
            text=True,
            cwd=str(Path(__file__).resolve().parents[1]),
        )
        choices_ok = result_proc.returncode == 0
        if not choices_ok:
            failures.append(f"choices: returncode={result_proc.returncode} stderr={result_proc.stderr[:200]}")
    except Exception as exc:
        failures.append(f"choices_raised: {exc}")

    all_checks_pass = len(failures) == 0
    return {
        "status": "pass" if all_checks_pass else "fail",
        "all_checks_pass": all_checks_pass,
        "loader_importable": loader_importable,
        "template_importable": template_importable,
        "load_missing_ok": load_missing_ok,
        "load_valid_ok": load_valid_ok,
        "template_no_targets_ok": template_no_targets_ok,
        "template_with_targets_ok": template_with_targets_ok,
        "dispatch_ok": dispatch_ok,
        "choices_ok": choices_ok,
        "failures": failures,
    }


if __name__ == "__main__":
    report = generate_phase3_read_after_retrieval_validation_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["all_checks_pass"]:
        sys.exit(1)
