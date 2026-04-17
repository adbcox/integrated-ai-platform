from typing import Any


def record_signature(
    validation: dict[str, Any],
    certification_control_plane: dict[str, Any],
    signature_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(certification_control_plane, dict)
        or not isinstance(signature_config, dict)
    ):
        return {
            "signature_status": "invalid_input",
            "signature_phase": None,
            "signature_count": 0,
        }

    val_ok = validation.get("claim_validation_status") == "validated"
    cp_ok = certification_control_plane.get("cert_cp_status") == "operational"

    if val_ok and cp_ok:
        return {
            "signature_status": "recorded",
            "signature_phase": validation.get("validation_phase"),
            "signature_count": 1,
        }

    return {
        "signature_status": "failed",
        "signature_phase": None,
        "signature_count": 0,
    }
