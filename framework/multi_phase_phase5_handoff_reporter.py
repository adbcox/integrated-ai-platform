from typing import Any


def report_phase5_handoff(
    handoff_finalization: dict[str, Any],
    checklist: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(handoff_finalization, dict)
        or not isinstance(checklist, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "handoff_report_status": "failed",
            "report_phase": None,
            "report_items": 0,
        }

    final_ok = handoff_finalization.get("handoff_finalization_status") == "finalized"
    check_ok = checklist.get("checklist_status") == "built"

    if final_ok and check_ok:
        return {
            "handoff_report_status": "complete",
            "report_phase": handoff_finalization.get("finalization_phase"),
            "report_items": checklist.get("checklist_items", 0),
        }

    return {
        "handoff_report_status": "incomplete",
        "report_phase": None,
        "report_items": 0,
    }
