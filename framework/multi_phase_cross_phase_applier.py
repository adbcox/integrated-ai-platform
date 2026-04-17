from typing import Any


def apply_across_phases(
    transfer_execution: dict[str, Any],
    learning_cp: dict[str, Any],
    application_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_execution, dict)
        or not isinstance(learning_cp, dict)
        or not isinstance(application_config, dict)
    ):
        return {
            "application_status": "invalid_input",
            "applied_phase": None,
            "applied_count": 0,
        }

    transfer_ok = transfer_execution.get("transfer_execution_status") == "executed"
    learning_ok = learning_cp.get("learning_cp_status") == "operational"

    if transfer_ok and learning_ok:
        return {
            "application_status": "applied",
            "applied_phase": learning_cp.get("learning_phase"),
            "applied_count": transfer_execution.get("transferred_count", 0),
        }

    if transfer_ok and not learning_ok:
        return {
            "application_status": "learning_offline",
            "applied_phase": None,
            "applied_count": 0,
        }

    if not transfer_ok:
        return {
            "application_status": "no_transfer",
            "applied_phase": None,
            "applied_count": 0,
        }

    return {
        "application_status": "invalid_input",
        "applied_phase": None,
        "applied_count": 0,
    }
