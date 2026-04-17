from typing import Any


def gate_phase5_promotion(
    phase5_exit_gate: dict[str, Any],
    promotion_readiness: dict[str, Any],
    stack_readiness: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(phase5_exit_gate, dict)
        or not isinstance(promotion_readiness, dict)
        or not isinstance(stack_readiness, dict)
    ):
        return {
            "promotion_gate_status": "blocked",
            "promotion_phase": None,
            "promotion_signal": None,
        }

    peg_ok = phase5_exit_gate.get("exit_gate_status") == "open"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"
    sr_ok = stack_readiness.get("stack_readiness_status") == "ready"
    all_ok = peg_ok and pr_ok and sr_ok

    if all_ok:
        return {
            "promotion_gate_status": "promoted",
            "promotion_phase": phase5_exit_gate.get("gate_phase"),
            "promotion_signal": "ready_for_promotion",
        }

    if (peg_ok and pr_ok) or (peg_ok and sr_ok) or (pr_ok and sr_ok):
        return {
            "promotion_gate_status": "pending",
            "promotion_phase": None,
            "promotion_signal": None,
        }

    return {
        "promotion_gate_status": "blocked",
        "promotion_phase": None,
        "promotion_signal": None,
    }
