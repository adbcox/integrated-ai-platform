from typing import Any


def gate_phase5_closure(
    transfer_finalizer: dict[str, Any],
    generalization_summary: dict[str, Any],
    cross_layer_learning_gate: dict[str, Any],
    gate_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_finalizer, dict)
        or not isinstance(generalization_summary, dict)
        or not isinstance(cross_layer_learning_gate, dict)
        or not isinstance(gate_config, dict)
    ):
        return {
            "phase5_closure_status": "blocked",
            "closure_phase": None,
            "closure_signal": None,
        }

    tf_ok = transfer_finalizer.get("transfer_finalization_status") == "finalized"
    gs_ok = generalization_summary.get("generalization_summary_status") == "complete"
    clg_ok = cross_layer_learning_gate.get("cross_layer_status") == "aligned"
    all_ok = tf_ok and gs_ok and clg_ok

    if all_ok:
        return {
            "phase5_closure_status": "closed",
            "closure_phase": transfer_finalizer.get("finalized_phase"),
            "closure_signal": gate_config.get("signal", "phase5_closed"),
        }

    if (tf_ok and gs_ok) or (tf_ok and clg_ok) or (gs_ok and clg_ok):
        return {
            "phase5_closure_status": "pending",
            "closure_phase": None,
            "closure_signal": None,
        }

    return {
        "phase5_closure_status": "blocked",
        "closure_phase": None,
        "closure_signal": None,
    }
