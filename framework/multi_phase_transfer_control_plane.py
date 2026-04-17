from typing import Any


def build_transfer_control_plane(
    transfer_validation: dict[str, Any],
    transfer_rollup: dict[str, Any],
    event_bus: dict[str, Any],
    cp_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(transfer_validation, dict)
        or not isinstance(transfer_rollup, dict)
        or not isinstance(event_bus, dict)
        or not isinstance(cp_config, dict)
    ):
        return {
            "transfer_cp_status": "offline",
            "cp_phase": None,
            "message_count": 0,
        }

    tv_ok = transfer_validation.get("transfer_validation_status") == "valid"
    tr_ok = transfer_rollup.get("transfer_rollup_status") == "rolled_up"
    msg_ok = event_bus.get("message_count", 0) >= 0

    if tv_ok and tr_ok and msg_ok:
        return {
            "transfer_cp_status": "operational",
            "cp_phase": transfer_validation.get("validated_phase"),
            "message_count": event_bus.get("message_count", 0),
        }

    if (tv_ok and tr_ok) or (tv_ok and msg_ok) or (tr_ok and msg_ok):
        return {
            "transfer_cp_status": "degraded",
            "cp_phase": None,
            "message_count": 0,
        }

    return {
        "transfer_cp_status": "offline",
        "cp_phase": None,
        "message_count": 0,
    }
