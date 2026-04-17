from typing import Any


def rollup_promotion(
    packet_assembler: dict[str, Any],
    packet_validator: dict[str, Any],
    packet_sealer: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(packet_assembler, dict)
        or not isinstance(packet_validator, dict)
        or not isinstance(packet_sealer, dict)
    ):
        return {
            "promotion_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    pa_ok = packet_assembler.get("packet_assembly_status") == "assembled"
    pv_ok = packet_validator.get("packet_validation_status") == "validated"
    ps_ok = packet_sealer.get("seal_status") == "sealed"
    all_ok = pa_ok and pv_ok and ps_ok

    if all_ok:
        return {
            "promotion_rollup_status": "rolled_up",
            "rollup_phase": packet_assembler.get("assembly_phase"),
            "rollup_count": 1,
        }

    if (pa_ok and pv_ok) or (pa_ok and ps_ok) or (pv_ok and ps_ok):
        return {
            "promotion_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "promotion_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
