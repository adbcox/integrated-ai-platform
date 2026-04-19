"""Introspection-only validation report for phase3_inference_response."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_inference_response_validation_report() -> dict:
    failures: list[str] = []
    importable = False
    empty_payload_ok = False
    output_text_ok = False
    has_content_false_ok = False
    output_chars_ok = False
    non_dict_safe = False
    all_contains = False
    template_dispatches = False
    bin_wires_inference_response = False
    choices_ok = False

    _REQUIRED_KEYS = {"output_text", "backend", "inference_metadata", "output_chars", "has_content"}

    try:
        from framework.framework_control_plane import _phase3_extract_inference_response
        importable = True
    except Exception as exc:
        failures.append(f"importable: {exc}")

    if importable:
        try:
            r = _phase3_extract_inference_response({})
            empty_payload_ok = (
                set(r.keys()) == _REQUIRED_KEYS
                and r["output_text"] == ""
                and r["output_chars"] == 0
                and r["has_content"] is False
                and r["inference_metadata"] == {}
            )
            if not empty_payload_ok:
                failures.append(f"empty_payload_ok: got {r!r}")
        except Exception as exc:
            failures.append(f"empty_payload_ok raised: {exc}")

        try:
            r = _phase3_extract_inference_response({"output": "hello"})
            output_text_ok = r["output_text"] == "hello" and r["has_content"] is True
            if not output_text_ok:
                failures.append(f"output_text_ok: got {r!r}")
        except Exception as exc:
            failures.append(f"output_text_ok raised: {exc}")

        try:
            r = _phase3_extract_inference_response({"output": ""})
            has_content_false_ok = r["has_content"] is False
            if not has_content_false_ok:
                failures.append(f"has_content_false_ok: got {r!r}")
        except Exception as exc:
            failures.append(f"has_content_false_ok raised: {exc}")

        try:
            r = _phase3_extract_inference_response({"output": "abc"})
            output_chars_ok = r["output_chars"] == 3
            if not output_chars_ok:
                failures.append(f"output_chars_ok: got {r['output_chars']}")
        except Exception as exc:
            failures.append(f"output_chars_ok raised: {exc}")

        try:
            r = _phase3_extract_inference_response(None)  # type: ignore[arg-type]
            non_dict_safe = set(r.keys()) == _REQUIRED_KEYS and r["has_content"] is False
            if not non_dict_safe:
                failures.append(f"non_dict_safe: got {r!r}")
        except Exception as exc:
            failures.append(f"non_dict_safe raised: {exc}")

    try:
        import framework.framework_control_plane as m
        all_contains = "_phase3_extract_inference_response" in m.__all__
        if not all_contains:
            failures.append("all_contains: not in __all__")
    except Exception as exc:
        failures.append(f"all_contains raised: {exc}")

    try:
        from bin.framework_control_plane import _template_payload
        t = _template_payload("context_bundle_inference_probe")
        template_dispatches = (
            isinstance(t, dict)
            and "inference_prompt" in t
            and "phase2_typed_tools" not in t
        )
        if not template_dispatches:
            failures.append(f"template_dispatches: keys={list(t.keys())!r}")
    except Exception as exc:
        failures.append(f"template_dispatches raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        bin_wires_inference_response = "phase3_inference_response" in source
        if not bin_wires_inference_response:
            failures.append("bin_wires_inference_response: key not found in bin source")
    except Exception as exc:
        failures.append(f"bin_wires_inference_response raised: {exc}")

    try:
        repo_root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "bin/framework_control_plane.py",
             "--task-template", "context_bundle_inference_probe", "--help"],
            capture_output=True, cwd=str(repo_root), timeout=15,
        )
        choices_ok = result.returncode == 0
        if not choices_ok:
            failures.append(f"choices_ok: returncode={result.returncode}")
    except Exception as exc:
        failures.append(f"choices_ok raised: {exc}")

    all_checks_pass = (
        importable and empty_payload_ok and output_text_ok and has_content_false_ok
        and output_chars_ok and non_dict_safe and all_contains and template_dispatches
        and bin_wires_inference_response and choices_ok
        and not failures
    )

    return {
        "phase3_inference_response_check": "phase3_inference_response",
        "importable": importable,
        "empty_payload_ok": empty_payload_ok,
        "output_text_ok": output_text_ok,
        "has_content_false_ok": has_content_false_ok,
        "output_chars_ok": output_chars_ok,
        "non_dict_safe": non_dict_safe,
        "all_contains": all_contains,
        "template_dispatches": template_dispatches,
        "bin_wires_inference_response": bin_wires_inference_response,
        "choices_ok": choices_ok,
        "failures": failures,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_inference_response_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
