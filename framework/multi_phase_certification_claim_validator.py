from typing import Any


def validate_certification_claim(
    claim: dict[str, Any],
    exit_readiness: dict[str, Any],
    validator_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(claim, dict)
        or not isinstance(exit_readiness, dict)
        or not isinstance(validator_config, dict)
    ):
        return {
            "claim_validation_status": "invalid_input",
            "validation_phase": None,
            "validation_result": None,
        }

    claim_ok = claim.get("claim_status") == "built"
    er_ok = exit_readiness.get("exit_readiness_status") == "valid"

    if claim_ok and er_ok:
        return {
            "claim_validation_status": "validated",
            "validation_phase": claim.get("claim_phase"),
            "validation_result": "claim_valid",
        }

    return {
        "claim_validation_status": "failed",
        "validation_phase": None,
        "validation_result": None,
    }
