from typing import Any


def validate_diagnostics(
    dashboard: dict[str, Any],
    forensic: dict[str, Any],
    fusion: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(dashboard, dict)
        or not isinstance(forensic, dict)
        or not isinstance(fusion, dict)
    ):
        return {
            "diagnostic_validation_status": "invalid_input",
            "validated_phase": None,
            "diagnostics_complete": False,
        }

    if dashboard.get("dashboard_status") != "built":
        return {
            "diagnostic_validation_status": "failed",
            "validated_phase": None,
            "diagnostics_complete": False,
        }

    if (
        forensic.get("forensic_status") in ("complete", "partial", "nominal")
        and fusion.get("fusion_status") in ("fused", "partial")
    ):
        return {
            "diagnostic_validation_status": "valid",
            "validated_phase": dashboard.get("dashboard_phase"),
            "diagnostics_complete": True,
        }

    return {
        "diagnostic_validation_status": "partial",
        "validated_phase": None,
        "diagnostics_complete": False,
    }
