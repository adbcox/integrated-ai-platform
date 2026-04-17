from typing import Any


def summarize_promotion(
    promo_cp: dict[str, Any],
    seal: dict[str, Any],
    promotion_attestation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(promo_cp, dict)
        or not isinstance(seal, dict)
        or not isinstance(promotion_attestation, dict)
    ):
        return {
            "promotion_summary_status": "invalid_input",
            "summary_phase": None,
            "summary_sections": 0,
        }

    cp_ok = promo_cp.get("promo_cp_status") == "operational"
    seal_ok = seal.get("seal_status") == "sealed"
    attest_ok = promotion_attestation.get("promotion_attestation_status") == "attested"

    if cp_ok and seal_ok and attest_ok:
        return {
            "promotion_summary_status": "complete",
            "summary_phase": promo_cp.get("cp_phase"),
            "summary_sections": 4,
        }

    return {
        "promotion_summary_status": "incomplete",
        "summary_phase": None,
        "summary_sections": 0,
    }
