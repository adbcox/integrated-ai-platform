from typing import Any


def gate_phase5_exit(
    exit_readiness_summary: dict[str, Any],
    phase5_closure: dict[str, Any],
    phase5_completion: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(exit_readiness_summary, dict)
        or not isinstance(phase5_closure, dict)
        or not isinstance(phase5_completion, dict)
    ):
        return {
            "exit_gate_status": "blocked",
            "gate_phase": None,
            "gate_signal": None,
        }

    ers_ok = exit_readiness_summary.get("exit_readiness_summary_status") == "complete"
    pc_ok = phase5_closure.get("closure_status") == "closed"
    p5c_ok = phase5_completion.get("phase5_completion_status") == "complete"
    all_ok = ers_ok and pc_ok and p5c_ok

    if all_ok:
        return {
            "exit_gate_status": "open",
            "gate_phase": exit_readiness_summary.get("summary_phase"),
            "gate_signal": "phase5_exit_ready",
        }

    if (ers_ok and pc_ok) or (ers_ok and p5c_ok) or (pc_ok and p5c_ok):
        return {
            "exit_gate_status": "pending",
            "gate_phase": None,
            "gate_signal": None,
        }

    return {
        "exit_gate_status": "blocked",
        "gate_phase": None,
        "gate_signal": None,
    }
