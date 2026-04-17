from typing import Any


def record_phase_trace(
    coordinator: dict[str, Any],
    event_bus: dict[str, Any],
    trace_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(event_bus, dict)
        or not isinstance(trace_config, dict)
    ):
        return {
            "trace_status": "invalid_input",
            "trace_phase": None,
            "message_count": 0,
        }

    coord_ok = coordinator.get("coordinator_status") == "initialized"
    if not coord_ok:
        return {
            "trace_status": "coordinator_not_ready",
            "trace_phase": None,
            "message_count": 0,
        }

    bus_active = event_bus.get("message_count", -1) >= 0
    if coord_ok and bus_active:
        return {
            "trace_status": "recorded",
            "trace_phase": coordinator.get("phase_id"),
            "message_count": int(event_bus.get("message_count", 0)),
        }

    return {
        "trace_status": "invalid_input",
        "trace_phase": None,
        "message_count": 0,
    }
