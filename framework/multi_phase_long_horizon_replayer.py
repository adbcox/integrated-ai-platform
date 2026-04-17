from typing import Any


def replay_long_horizon(
    memory_consolidation: dict[str, Any],
    coordinator: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(memory_consolidation, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(config, dict)
    ):
        return {
            "replay_status": "invalid_input",
            "replay_count": 0,
            "replay_phase": None,
        }

    mc_ok = memory_consolidation.get("consolidation_status") == "consolidated"
    c_ok = coordinator.get("coordinator_status") == "initialized"
    all_ok = mc_ok and c_ok

    if all_ok:
        return {
            "replay_status": "replayed",
            "replay_count": memory_consolidation.get("consolidated_count", 0),
            "replay_phase": memory_consolidation.get("consolidation_phase"),
        }

    return {
        "replay_status": "failed",
        "replay_count": 0,
        "replay_phase": None,
    }
