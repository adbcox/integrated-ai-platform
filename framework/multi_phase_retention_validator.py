from typing import Any


def validate_retention(
    memory_consolidation: dict[str, Any],
    long_horizon_replay: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(memory_consolidation, dict)
        or not isinstance(long_horizon_replay, dict)
        or not isinstance(config, dict)
    ):
        return {
            "retention_status": "invalid_input",
            "retention_count": 0,
            "retention_phase": None,
        }

    mc_ok = memory_consolidation.get("consolidation_status") == "consolidated"
    lhr_ok = long_horizon_replay.get("replay_status") == "replayed"
    all_ok = mc_ok and lhr_ok

    if all_ok:
        return {
            "retention_status": "valid",
            "retention_count": memory_consolidation.get("consolidated_count", 0),
            "retention_phase": memory_consolidation.get("consolidation_phase"),
        }

    return {
        "retention_status": "failed",
        "retention_count": 0,
        "retention_phase": None,
    }
