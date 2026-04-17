from typing import Any


def build_phase_report(
    finalization_results: list[dict[str, Any]],
    archive_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(finalization_results, list) or not isinstance(
        archive_results, list
    ):
        return {
            "report_valid": False,
            "workflow_count": 0,
            "finalized_count": 0,
            "archived_count": 0,
            "incomplete_count": 0,
            "phase_completion_pct": 0.0,
            "phase_report_status": "invalid_input",
        }

    if len(finalization_results) == 0 and len(archive_results) == 0:
        return {
            "report_valid": True,
            "workflow_count": 0,
            "finalized_count": 0,
            "archived_count": 0,
            "incomplete_count": 0,
            "phase_completion_pct": 0.0,
            "phase_report_status": "empty",
        }

    workflow_count = len(finalization_results)
    finalized_count = len(
        [
            r
            for r in finalization_results
            if isinstance(r, dict) and r.get("finalization_status") == "finalized"
        ]
    )
    archived_count = len(
        [
            r
            for r in archive_results
            if isinstance(r, dict) and r.get("archive_status") == "archived"
        ]
    )
    incomplete_count = workflow_count - finalized_count
    pct = (
        round((finalized_count / float(workflow_count)) * 100.0, 3)
        if workflow_count > 0
        else 0.0
    )
    status = (
        "complete"
        if workflow_count > 0 and finalized_count == workflow_count
        else "partial"
    )

    return {
        "report_valid": True,
        "workflow_count": workflow_count,
        "finalized_count": finalized_count,
        "archived_count": archived_count,
        "incomplete_count": incomplete_count,
        "phase_completion_pct": pct,
        "phase_report_status": status,
    }


def summarize_phase_report(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("report_valid") is not True:
        return {
            "summary_valid": False,
            "phase_report_status": "invalid_input",
            "phase_completion_pct": 0.0,
            "workflow_count": 0,
        }

    return {
        "summary_valid": True,
        "phase_report_status": result.get("phase_report_status", "invalid_input"),
        "phase_completion_pct": float(result.get("phase_completion_pct", 0.0)),
        "workflow_count": int(result.get("workflow_count", 0)),
    }
