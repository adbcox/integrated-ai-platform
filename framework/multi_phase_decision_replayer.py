from typing import Any


def replay_decision(
    decision_record: dict[str, Any],
    coordinator: dict[str, Any],
    replay_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(decision_record, dict)
        or not isinstance(coordinator, dict)
        or not isinstance(replay_config, dict)
    ):
        return {
            "replay_status": "invalid_input",
            "replayed_id": None,
            "replayed_phase": None,
        }

    record_ok = decision_record.get("recording_status") == "recorded"
    coord_ok = coordinator.get("coordinator_status") == "initialized"

    if record_ok and coord_ok:
        return {
            "replay_status": "replayed",
            "replayed_id": decision_record.get("decision_id"),
            "replayed_phase": coordinator.get("phase_id"),
        }

    if not record_ok:
        return {
            "replay_status": "no_record",
            "replayed_id": None,
            "replayed_phase": None,
        }

    return {
        "replay_status": "coordinator_not_ready",
        "replayed_id": None,
        "replayed_phase": None,
    }
