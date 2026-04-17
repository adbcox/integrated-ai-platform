from typing import Any


def extract_self_critique(
    quality_assessment: dict[str, Any],
    decision_recording: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(quality_assessment, dict)
        or not isinstance(decision_recording, dict)
        or not isinstance(config, dict)
    ):
        return {
            "critique_status": "invalid_input",
            "critique_phase": None,
            "critique_count": 0,
        }

    qa_ok = quality_assessment.get("quality_status") == "scored"
    dr_ok = decision_recording.get("recording_status") == "recorded"
    all_ok = qa_ok and dr_ok

    if all_ok:
        return {
            "critique_status": "extracted",
            "critique_phase": decision_recording.get("recorded_phase"),
            "critique_count": 1,
        }

    return {
        "critique_status": "failed",
        "critique_phase": None,
        "critique_count": 0,
    }
