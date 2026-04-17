from typing import Any


def gate_phase5_maturity(
    learning_finalization: dict[str, Any],
    intelligence_summary: dict[str, Any],
    cross_layer: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(learning_finalization, dict)
        or not isinstance(intelligence_summary, dict)
        or not isinstance(cross_layer, dict)
    ):
        return {
            "maturity_status": "invalid_input",
            "mature_phase": None,
            "maturity_level": "none",
        }

    finalized = learning_finalization.get("learning_finalization_status") == "finalized"
    summary_complete = intelligence_summary.get("intelligence_summary_status") == "complete"
    cps_aligned = cross_layer.get("cross_layer_status") == "aligned"
    all_mature = finalized and summary_complete and cps_aligned
    any_progress = finalized or summary_complete or cps_aligned

    if all_mature:
        return {
            "maturity_status": "mature",
            "mature_phase": learning_finalization.get("finalized_phase"),
            "maturity_level": "phase5_complete",
        }

    if any_progress:
        return {
            "maturity_status": "progressing",
            "mature_phase": None,
            "maturity_level": "partial",
        }

    return {
        "maturity_status": "nascent",
        "mature_phase": None,
        "maturity_level": "none",
    }
