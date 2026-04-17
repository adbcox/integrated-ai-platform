from typing import Any


def finalize_phase5_promotion(
    promo_closure_gate: dict[str, Any],
    promo_cp: dict[str, Any],
    promotion_summary: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(promo_closure_gate, dict)
        or not isinstance(promo_cp, dict)
        or not isinstance(promotion_summary, dict)
    ):
        return {
            "promo_finalization_status": "failed",
            "finalization_phase": None,
            "finalization_result": None,
        }

    gate_ok = promo_closure_gate.get("promo_closure_gate_status") == "open"
    cp_ok = promo_cp.get("promo_cp_status") == "operational"
    sum_ok = promotion_summary.get("promotion_summary_status") == "complete"

    if gate_ok and cp_ok and sum_ok:
        return {
            "promo_finalization_status": "finalized",
            "finalization_phase": promo_closure_gate.get("gate_phase"),
            "finalization_result": "promo_finalized",
        }

    return {
        "promo_finalization_status": "failed",
        "finalization_phase": None,
        "finalization_result": None,
    }
