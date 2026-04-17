from typing import Any


def validate_decision(
    recording: dict[str, Any],
    guardrail: dict[str, Any],
    validation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(recording, dict)
        or not isinstance(guardrail, dict)
        or not isinstance(validation_config, dict)
    ):
        return {
            "decision_validation_status": "invalid_input",
            "validated_decision": None,
            "validated_phase": None,
            "decision_complete": False,
        }

    record_ok = recording.get("recording_status") == "recorded"
    guardrail_clear = guardrail.get("guardrail_status") == "clear"
    guardrail_blocked = guardrail.get("guardrail_status") == "blocked"

    if record_ok and guardrail_clear:
        return {
            "decision_validation_status": "valid",
            "validated_decision": recording.get("decision_id"),
            "validated_phase": recording.get("recorded_phase"),
            "decision_complete": True,
        }

    if record_ok and guardrail.get("guardrail_status") == "no_arbitration":
        return {
            "decision_validation_status": "partial",
            "validated_decision": None,
            "validated_phase": None,
            "decision_complete": False,
        }

    if guardrail_blocked:
        return {
            "decision_validation_status": "blocked",
            "validated_decision": None,
            "validated_phase": None,
            "decision_complete": False,
        }

    return {
        "decision_validation_status": "invalid_input",
        "validated_decision": None,
        "validated_phase": None,
        "decision_complete": False,
    }
