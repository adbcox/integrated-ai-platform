from typing import Any


def attest_phase5_promotion(
    seal: dict[str, Any],
    promotion_readiness: dict[str, Any],
    attestation_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(seal, dict)
        or not isinstance(promotion_readiness, dict)
        or not isinstance(attestation_config, dict)
    ):
        return {
            "promotion_attestation_status": "invalid_input",
            "promotion_attestation_phase": None,
            "promotion_attestation_result": None,
        }

    seal_ok = seal.get("seal_status") == "sealed"
    pr_ok = promotion_readiness.get("promotion_readiness_status") == "ready"

    if seal_ok and pr_ok:
        return {
            "promotion_attestation_status": "attested",
            "promotion_attestation_phase": seal.get("seal_phase"),
            "promotion_attestation_result": "promotion_valid",
        }

    return {
        "promotion_attestation_status": "failed",
        "promotion_attestation_phase": None,
        "promotion_attestation_result": None,
    }
