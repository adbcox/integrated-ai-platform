from typing import Any


def report_transfer(
    transfer_validation: dict[str, Any],
    report_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_validation, dict)
        or not isinstance(report_config, dict)
    ):
        return {
            "transfer_report_status": "invalid_input",
            "reported_phase": None,
            "report_detail": None,
        }

    tv_ok = transfer_validation.get("transfer_validation_status") == "valid"

    if tv_ok:
        return {
            "transfer_report_status": "complete",
            "reported_phase": transfer_validation.get("validated_phase"),
            "report_detail": "transfer_validated",
        }

    return {
        "transfer_report_status": "incomplete",
        "reported_phase": None,
        "report_detail": "transfer_not_valid",
    }
