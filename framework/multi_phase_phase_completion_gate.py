from typing import Any


def gate_phase_completion(
    stack_readiness: dict[str, Any],
    capability_summary: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(stack_readiness, dict)
        or not isinstance(capability_summary, dict)
        or not isinstance(gate_config, dict)
    ):
        return {
            "phase_completion_status": "blocked",
            "gate_phase": None,
            "completion_signal": None,
        }

    sr_ok = stack_readiness.get("stack_readiness_status") == "ready"
    cs_ok = capability_summary.get("capability_summary_status") == "complete"
    all_ok = sr_ok and cs_ok

    if all_ok:
        return {
            "phase_completion_status": "open",
            "gate_phase": stack_readiness.get("gate_phase"),
            "completion_signal": gate_config.get("signal", "phase_complete"),
        }

    if sr_ok or cs_ok:
        return {
            "phase_completion_status": "pending",
            "gate_phase": None,
            "completion_signal": None,
        }

    return {
        "phase_completion_status": "blocked",
        "gate_phase": None,
        "completion_signal": None,
    }
