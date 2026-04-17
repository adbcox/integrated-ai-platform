from typing import Any


def report_generalization(
    generalization_validation: dict[str, Any],
    report_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(generalization_validation, dict)
        or not isinstance(report_config, dict)
    ):
        return {
            "generalization_report_status": "invalid_input",
            "reported_phase": None,
            "report_detail": None,
        }

    gv_ok = generalization_validation.get("gen_validation_status") == "valid"

    if gv_ok:
        return {
            "generalization_report_status": "complete",
            "reported_phase": generalization_validation.get("validated_phase"),
            "report_detail": "generalization_validated",
        }

    return {
        "generalization_report_status": "incomplete",
        "reported_phase": None,
        "report_detail": "generalization_not_valid",
    }
