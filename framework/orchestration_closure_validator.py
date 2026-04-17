from typing import Any


def validate_orchestration_closure(
    archive_result: dict[str, Any],
    telemetry_result: dict[str, Any],
    phase_report: dict[str, Any],
    audit_result: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(archive_result, dict)
        or not isinstance(telemetry_result, dict)
        or not isinstance(phase_report, dict)
        or not isinstance(audit_result, dict)
    ):
        return {
            "closure_valid": False,
            "archive_closed": False,
            "telemetry_emitted": False,
            "phase_complete": False,
            "audit_passed": False,
            "fully_closed": False,
            "open_items": [],
            "closure_status": "invalid_input",
        }

    archive_closed = archive_result.get("archive_status") == "archived"
    telemetry_emitted = telemetry_result.get("emit_status") == "emitted"
    phase_complete = phase_report.get("phase_report_status") == "complete"
    audit_passed = audit_result.get("audit_status") == "passed"

    open_items = []
    if not archive_closed:
        open_items.append("archive_closed")
    if not telemetry_emitted:
        open_items.append("telemetry_emitted")
    if not phase_complete:
        open_items.append("phase_complete")
    if not audit_passed:
        open_items.append("audit_passed")

    fully_closed = len(open_items) == 0

    return {
        "closure_valid": True,
        "archive_closed": archive_closed,
        "telemetry_emitted": telemetry_emitted,
        "phase_complete": phase_complete,
        "audit_passed": audit_passed,
        "fully_closed": fully_closed,
        "open_items": open_items,
        "closure_status": "closed" if fully_closed else "open",
    }


def summarize_closure(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("closure_valid") is not True:
        return {
            "summary_valid": False,
            "closure_status": "invalid_input",
            "open_item_count": 0,
        }

    return {
        "summary_valid": True,
        "closure_status": result.get("closure_status", "invalid_input"),
        "open_item_count": (
            len(result.get("open_items", []))
            if isinstance(result.get("open_items", []), list)
            else 0
        ),
    }
