from typing import Any


def seal_promotion_packet(
    validation: dict[str, Any],
    promotion_control_plane: dict[str, Any],
    sealer_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(validation, dict)
        or not isinstance(promotion_control_plane, dict)
        or not isinstance(sealer_config, dict)
    ):
        return {
            "seal_status": "invalid_input",
            "seal_phase": None,
            "seal_count": 0,
        }

    val_ok = validation.get("packet_validation_status") == "validated"
    cp_ok = promotion_control_plane.get("promo_cp_status") == "operational"

    if val_ok and cp_ok:
        return {
            "seal_status": "sealed",
            "seal_phase": validation.get("validation_phase"),
            "seal_count": 1,
        }

    return {
        "seal_status": "failed",
        "seal_phase": None,
        "seal_count": 0,
    }
