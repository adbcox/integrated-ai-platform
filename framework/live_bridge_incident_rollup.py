from typing import Any

def rollup_incidents(lesson_recording: Any) -> dict[str, Any]:
    if not isinstance(lesson_recording, dict):
        return {"incident_rollup_status": "not_rolled_up"}
    lesson_ok = lesson_recording.get("lesson_recording_status") == "recorded"
    if not lesson_ok:
        return {"incident_rollup_status": "not_rolled_up"}
    return {
        "incident_rollup_status": "rolled_up",
    }
