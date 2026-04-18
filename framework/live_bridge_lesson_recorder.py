from typing import Any

def record_lesson(postmortem_building: Any, lesson_config: Any) -> dict[str, Any]:
    if not isinstance(postmortem_building, dict):
        return {"lesson_recording_status": "not_recorded"}
    post_ok = postmortem_building.get("postmortem_building_status") == "built"
    if not post_ok:
        return {"lesson_recording_status": "not_recorded"}
    return {
        "lesson_recording_status": "recorded",
        "lesson_id": lesson_config.get("lesson_id", "LESSON_0"),
    }
