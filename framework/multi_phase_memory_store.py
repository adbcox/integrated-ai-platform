from typing import Any


def store_phase_memory(
    buffer: dict[str, Any], coordinator: dict[str, Any], memory_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(buffer, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(memory_config, dict)
    ):
        return {
            "memory_status": "invalid_input",
            "stored_count": 0,
            "memory_phase": None,
        }

    buffer_ok = buffer.get("buffer_status") == "buffered"
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if buffer_ok and coord_ok:
        return {
            "memory_status": "stored",
            "stored_count": buffer.get("buffer_size", 0),
            "memory_phase": coordinator.get("phase_id"),
        }

    if not buffer_ok:
        return {
            "memory_status": "no_buffer",
            "stored_count": 0,
            "memory_phase": None,
        }

    return {
        "memory_status": "coordinator_not_ready",
        "stored_count": 0,
        "memory_phase": None,
    }
