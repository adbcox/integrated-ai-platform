from typing import Any


def feedback_action(
    summary: dict[str, Any],
    recording: dict[str, Any],
    feedback_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(summary, dict)
        or not isinstance(recording, dict)
        or not isinstance(feedback_config, dict)
    ):
        return {
            "feedback_status": "invalid_input",
            "feedback_phase": None,
            "feedback_decision": None,
        }

    summary_ok = summary.get("autonomy_summary_status") in ("complete", "partial")
    record_ok = recording.get("recording_status") == "recorded"

    if summary_ok and record_ok:
        return {
            "feedback_status": "fed_back",
            "feedback_phase": summary.get("summary_phase"),
            "feedback_decision": recording.get("decision_id"),
        }

    if not summary_ok:
        return {
            "feedback_status": "no_summary",
            "feedback_phase": None,
            "feedback_decision": None,
        }

    return {
        "feedback_status": "invalid_input",
        "feedback_phase": None,
        "feedback_decision": None,
    }
