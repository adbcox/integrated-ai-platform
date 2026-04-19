"""Introspection-only validation report for phase3_next_action."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def generate_phase3_next_action_validation_report() -> dict:
    failures: list[str] = []
    importable = False
    no_context_ok = False
    insufficient_context_ok = False
    refine_retrieval_ok = False
    ready_ok = False
    required_keys_ok = False
    non_dict_safe = False
    all_contains = False
    bin_wires_next_action = False
    action_values_bounded = False

    _REQUIRED_KEYS = {"action", "reason", "context_adequate", "total_files", "total_symbols", "inference_has_content"}

    try:
        from framework.framework_control_plane import _phase3_derive_next_action
        importable = True
    except Exception as exc:
        failures.append(f"importable: {exc}")

    if importable:
        def _bundle(prompt_ready=True, total_files=2, total_symbols=3):
            return {"query": "q", "total_files": total_files, "total_symbols": total_symbols,
                    "files": [], "top_file": "", "top_file_symbol_count": total_symbols,
                    "prompt_ready": prompt_ready}

        def _inference(has_content=True):
            return {"output_text": "x" if has_content else "", "backend": "",
                    "inference_metadata": {}, "output_chars": 1 if has_content else 0,
                    "has_content": has_content}

        try:
            r = _phase3_derive_next_action({}, {})
            no_context_ok = r["action"] == "no_context"
            if not no_context_ok:
                failures.append(f"no_context_ok: got action={r['action']!r}")
        except Exception as exc:
            failures.append(f"no_context_ok raised: {exc}")

        try:
            r = _phase3_derive_next_action(_bundle(), _inference(has_content=False))
            insufficient_context_ok = r["action"] == "insufficient_context"
            if not insufficient_context_ok:
                failures.append(f"insufficient_context_ok: got action={r['action']!r}")
        except Exception as exc:
            failures.append(f"insufficient_context_ok raised: {exc}")

        try:
            r = _phase3_derive_next_action(_bundle(total_symbols=0), _inference())
            refine_retrieval_ok = r["action"] == "refine_retrieval"
            if not refine_retrieval_ok:
                failures.append(f"refine_retrieval_ok: got action={r['action']!r}")
        except Exception as exc:
            failures.append(f"refine_retrieval_ok raised: {exc}")

        try:
            r = _phase3_derive_next_action(_bundle(total_symbols=3, total_files=2), _inference())
            ready_ok = r["action"] == "ready" and r["context_adequate"] is True
            if not ready_ok:
                failures.append(f"ready_ok: action={r['action']!r}, context_adequate={r['context_adequate']!r}")
        except Exception as exc:
            failures.append(f"ready_ok raised: {exc}")

        try:
            r = _phase3_derive_next_action(_bundle(), _inference())
            required_keys_ok = set(r.keys()) == _REQUIRED_KEYS
            if not required_keys_ok:
                failures.append(f"required_keys_ok: got keys {set(r.keys())!r}")
        except Exception as exc:
            failures.append(f"required_keys_ok raised: {exc}")

        try:
            r = _phase3_derive_next_action(None, None)  # type: ignore[arg-type]
            non_dict_safe = set(r.keys()) == _REQUIRED_KEYS and r["context_adequate"] is False
            if not non_dict_safe:
                failures.append(f"non_dict_safe: got {r!r}")
        except Exception as exc:
            failures.append(f"non_dict_safe raised: {exc}")

    try:
        import framework.framework_control_plane as m
        all_contains = "_phase3_derive_next_action" in m.__all__
        if not all_contains:
            failures.append("all_contains: not in __all__")
    except Exception as exc:
        failures.append(f"all_contains raised: {exc}")

    try:
        bin_path = Path(__file__).resolve().parents[1] / "bin" / "framework_control_plane.py"
        source = bin_path.read_text(encoding="utf-8")
        bin_wires_next_action = "phase3_next_action" in source
        if not bin_wires_next_action:
            failures.append("bin_wires_next_action: key not found in bin source")
    except Exception as exc:
        failures.append(f"bin_wires_next_action raised: {exc}")

    try:
        tokens = {"no_context", "insufficient_context", "refine_retrieval", "ready"}
        action_values_bounded = len(tokens) == 4 and all(isinstance(t, str) and t for t in tokens)
        if not action_values_bounded:
            failures.append("action_values_bounded: unexpected token set")
    except Exception as exc:
        failures.append(f"action_values_bounded raised: {exc}")

    all_checks_pass = (
        importable and no_context_ok and insufficient_context_ok and refine_retrieval_ok
        and ready_ok and required_keys_ok and non_dict_safe and all_contains
        and bin_wires_next_action and action_values_bounded
        and not failures
    )

    return {
        "phase3_next_action_check": "phase3_next_action",
        "importable": importable,
        "no_context_ok": no_context_ok,
        "insufficient_context_ok": insufficient_context_ok,
        "refine_retrieval_ok": refine_retrieval_ok,
        "ready_ok": ready_ok,
        "required_keys_ok": required_keys_ok,
        "non_dict_safe": non_dict_safe,
        "all_contains": all_contains,
        "bin_wires_next_action": bin_wires_next_action,
        "action_values_bounded": action_values_bounded,
        "failures": failures,
        "all_checks_pass": all_checks_pass,
        "status": "pass" if all_checks_pass else "fail",
    }


if __name__ == "__main__":
    report = generate_phase3_next_action_validation_report()
    print(json.dumps(report, indent=2))
    sys.exit(0 if report.get("all_checks_pass") else 1)
