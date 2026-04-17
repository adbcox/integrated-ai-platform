from typing import Any


def collect_phase_outcome(
    recording: dict[str, Any], replay: dict[str, Any], outcome_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(recording, dict)
        or not isinstance(replay, dict)
        or not isinstance(outcome_config, dict)
    ):
        return {
            "outcome_status": "invalid_input",
            "outcome_phase": None,
            "decision_id": None,
            "observed_outcome": 0,
        }

    record_ok = recording.get("recording_status") == "recorded"
    replay_ok = replay.get("replay_status") == "replayed"

    if record_ok and replay_ok:
        return {
            "outcome_status": "collected",
            "outcome_phase": recording.get("recorded_phase"),
            "decision_id": recording.get("decision_id"),
            "observed_outcome": recording.get("outcome", 0),
        }

    if not record_ok:
        return {
            "outcome_status": "no_record",
            "outcome_phase": None,
            "decision_id": None,
            "observed_outcome": 0,
        }

    return {
        "outcome_status": "invalid_input",
        "outcome_phase": None,
        "decision_id": None,
        "observed_outcome": 0,
    }
