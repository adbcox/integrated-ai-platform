from typing import Any


def control_promotion(
    promotion_rollup: dict[str, Any],
    promotion_attestation: dict[str, Any],
    cp_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(promotion_rollup, dict)
        or not isinstance(promotion_attestation, dict)
        or not isinstance(cp_config, dict)
    ):
        return {
            "promo_cp_status": "offline",
            "cp_phase": None,
            "cp_health": "unknown",
        }

    promo_ok = promotion_rollup.get("promotion_rollup_status") == "rolled_up"
    attest_ok = promotion_attestation.get("promotion_attestation_status") == "attested"

    if promo_ok and attest_ok:
        return {
            "promo_cp_status": "operational",
            "cp_phase": promotion_rollup.get("rollup_phase"),
            "cp_health": "healthy",
        }

    if promo_ok or attest_ok:
        return {
            "promo_cp_status": "degraded",
            "cp_phase": None,
            "cp_health": "degraded",
        }

    return {
        "promo_cp_status": "offline",
        "cp_phase": None,
        "cp_health": "offline",
    }
