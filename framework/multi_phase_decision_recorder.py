from typing import Any


def record_decision(
    counterfactual: dict[str, Any],
    execution_arbitration: dict[str, Any],
    recording_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(counterfactual, dict)
        or not isinstance(execution_arbitration, dict)
        or not isinstance(recording_config, dict)
    ):
        return {
            "recording_status": "invalid_input",
            "decision_id": None,
            "recorded_phase": None,
            "outcome": 0,
        }

    cf_ok = counterfactual.get("counterfactual_status") == "evaluated"
    exec_ok = execution_arbitration.get("execution_arbitration_status") == "authorized"

    if cf_ok and exec_ok:
        return {
            "recording_status": "recorded",
            "decision_id": recording_config.get("decision_id", "dec-0001"),
            "recorded_phase": execution_arbitration.get("authorized_phase"),
            "outcome": int(counterfactual.get("projected_outcome", 0)),
        }

    if not exec_ok:
        return {
            "recording_status": "no_decision",
            "decision_id": None,
            "recorded_phase": None,
            "outcome": 0,
        }

    return {
        "recording_status": "no_evaluation",
        "decision_id": None,
        "recorded_phase": None,
        "outcome": 0,
    }
