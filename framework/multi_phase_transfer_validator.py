from typing import Any


def validate_transfer(
    transfer_execution: dict[str, Any],
    mastery: dict[str, Any],
    validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_execution, dict)
        or not isinstance(mastery, dict)
        or not isinstance(validation_config, dict)
    ):
        return {
            "transfer_validation_status": "invalid_input",
            "validated_phase": None,
            "transfer_complete": False,
        }

    te_ok = transfer_execution.get("transfer_execution_status") == "executed"
    m_ok = mastery.get("mastery_status") == "assessed"
    all_ok = te_ok and m_ok
    any_ok = te_ok or m_ok

    if all_ok:
        return {
            "transfer_validation_status": "valid",
            "validated_phase": transfer_execution.get("executed_phase"),
            "transfer_complete": True,
        }

    if any_ok:
        return {
            "transfer_validation_status": "partial",
            "validated_phase": None,
            "transfer_complete": False,
        }

    return {
        "transfer_validation_status": "failed",
        "validated_phase": None,
        "transfer_complete": False,
    }
