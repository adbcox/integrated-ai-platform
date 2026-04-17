from typing import Any


def validate_promotion_packet(
    packet: dict[str, Any],
    certification_summary: dict[str, Any],
    validator_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(packet, dict)
        or not isinstance(certification_summary, dict)
        or not isinstance(validator_config, dict)
    ):
        return {
            "packet_validation_status": "invalid_input",
            "validation_phase": None,
            "validation_result": None,
        }

    packet_ok = packet.get("packet_assembly_status") == "assembled"
    cs_ok = certification_summary.get("certification_summary_status") == "complete"

    if packet_ok and cs_ok:
        return {
            "packet_validation_status": "validated",
            "validation_phase": packet.get("assembly_phase"),
            "validation_result": "packet_valid",
        }

    return {
        "packet_validation_status": "failed",
        "validation_phase": None,
        "validation_result": None,
    }
