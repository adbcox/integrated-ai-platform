from typing import Any


def report_observability(
    validation: dict[str, Any],
    dashboard: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(dashboard, dict)
        or not isinstance(phase_id, str)
        or not phase_id
    ):
        return {
            "observability_report_status": "invalid_input",
            "report_phase": None,
            "dashboard_status": None,
            "diagnostics_complete": False,
        }

    if validation.get("diagnostic_validation_status") != "valid":
        return {
            "observability_report_status": "incomplete",
            "report_phase": None,
            "dashboard_status": None,
            "diagnostics_complete": False,
        }

    return {
        "observability_report_status": "complete",
        "report_phase": phase_id,
        "dashboard_status": dashboard.get("dashboard_status"),
        "diagnostics_complete": validation.get("diagnostics_complete", False),
    }
