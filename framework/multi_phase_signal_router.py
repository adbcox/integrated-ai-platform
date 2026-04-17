from typing import Any


def route_phase_signal(
    signal: dict[str, Any],
    control_plane: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(signal, dict)
        or not isinstance(control_plane, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "signal_status": "invalid_input",
            "signal_type": None,
            "routed_to_phase": None,
        }

    control_plane_status = control_plane.get("control_plane_status")
    message_count = event_bus.get("message_count", -1)

    route_ok = (
        control_plane_status in ("operational", "degraded")
        and isinstance(message_count, int)
        and message_count >= 0
    )

    if control_plane_status == "offline":
        return {
            "signal_status": "control_plane_offline",
            "signal_type": None,
            "routed_to_phase": None,
        }

    if not route_ok:
        return {
            "signal_status": "invalid_input",
            "signal_type": None,
            "routed_to_phase": None,
        }

    signal_type = signal.get("signal_type")
    if not signal_type:
        return {
            "signal_status": "invalid_input",
            "signal_type": None,
            "routed_to_phase": None,
        }

    return {
        "signal_status": "routed",
        "signal_type": signal_type,
        "routed_to_phase": control_plane.get("active_phase"),
    }
