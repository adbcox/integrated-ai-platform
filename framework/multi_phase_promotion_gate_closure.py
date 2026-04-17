from typing import Any


def gate_promotion_closure(
    promotion_summary: dict[str, Any],
    seal: dict[str, Any],
    promotion_attestation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(promotion_summary, dict)
        or not isinstance(seal, dict)
        or not isinstance(promotion_attestation, dict)
    ):
        return {
            "promo_closure_gate_status": "blocked",
            "gate_phase": None,
            "gate_result": None,
        }

    promo_ok = promotion_summary.get("promotion_summary_status") == "complete"
    seal_ok = seal.get("seal_status") == "sealed"
    attest_ok = promotion_attestation.get("promotion_attestation_status") == "attested"

    if promo_ok and seal_ok and attest_ok:
        return {
            "promo_closure_gate_status": "open",
            "gate_phase": promotion_summary.get("summary_phase"),
            "gate_result": "promo_ready",
        }

    return {
        "promo_closure_gate_status": "blocked",
        "gate_phase": None,
        "gate_result": None,
    }
