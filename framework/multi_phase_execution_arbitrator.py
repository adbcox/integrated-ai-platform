from typing import Any


def arbitrate_execution(
    arbitration: dict[str, Any],
    dispatch_result: dict[str, Any],
    execution_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(arbitration, dict)
        or not isinstance(dispatch_result, dict)
        or not isinstance(execution_config, dict)
    ):
        return {
            "execution_arbitration_status": "invalid_input",
            "authorized_phase": None,
            "authorized_action": None,
            "job_id": None,
        }

    arb_ok = arbitration.get("arbitration_status") == "arbitrated"
    dispatch_ok = dispatch_result.get("dispatch_status") == "dispatched"

    if arb_ok and dispatch_ok:
        return {
            "execution_arbitration_status": "authorized",
            "authorized_phase": arbitration.get("arbitrated_phase"),
            "authorized_action": arbitration.get("arbitrated_action"),
            "job_id": dispatch_result.get("dispatched_job_id"),
        }

    if arb_ok and not dispatch_ok:
        return {
            "execution_arbitration_status": "dispatch_blocked",
            "authorized_phase": None,
            "authorized_action": None,
            "job_id": None,
        }

    return {
        "execution_arbitration_status": "no_arbitration",
        "authorized_phase": None,
        "authorized_action": None,
        "job_id": None,
    }
