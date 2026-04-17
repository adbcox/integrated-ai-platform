from typing import Any


def verify_signature(
    signature: dict[str, Any],
    claim: dict[str, Any],
    verifier_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(signature, dict)
        or not isinstance(claim, dict)
        or not isinstance(verifier_config, dict)
    ):
        return {
            "verification_status": "invalid_input",
            "verification_phase": None,
            "verification_result": None,
        }

    sig_ok = signature.get("signature_status") == "recorded"
    claim_ok = claim.get("claim_status") == "built"

    if sig_ok and claim_ok:
        return {
            "verification_status": "verified",
            "verification_phase": signature.get("signature_phase"),
            "verification_result": "signature_valid",
        }

    return {
        "verification_status": "failed",
        "verification_phase": None,
        "verification_result": None,
    }
