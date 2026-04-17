from typing import Any


def report_phase5_promotion(
    promo_finalization: dict[str, Any],
    promotion_summary: dict[str, Any],
    phase_id: str,
) -> dict[str, Any]:
    if (
        not isinstance(promo_finalization, dict)
        or not isinstance(promotion_summary, dict)
        or not isinstance(phase_id, str)
    ):
        return {
            "promo_report_status": "failed",
            "report_phase": None,
            "report_sections": 0,
        }

    final_ok = promo_finalization.get("promo_finalization_status") == "finalized"
    sum_ok = promotion_summary.get("promotion_summary_status") == "complete"

    if final_ok and sum_ok:
        return {
            "promo_report_status": "complete",
            "report_phase": promo_finalization.get("finalization_phase"),
            "report_sections": promotion_summary.get("summary_sections", 0),
        }

    return {
        "promo_report_status": "incomplete",
        "report_phase": None,
        "report_sections": 0,
    }
