from typing import Any


def track_stage_progress(
    plan_id: str,
    current_stage: str,
    completed_stages: int,
    total_stages: int,
) -> dict[str, Any]:
    if not plan_id or completed_stages < 0 or total_stages < 0:
        return {
            "tracking_valid": False,
            "current_stage": "",
            "progress_pct": 0.0,
            "overall_status": "invalid",
        }

    progress_pct = 0.0
    if total_stages > 0:
        progress_pct = round((completed_stages / float(total_stages)) * 100.0, 3)

    overall_status = (
        "completed"
        if total_stages > 0 and completed_stages >= total_stages
        else "running"
    )

    return {
        "tracking_valid": True,
        "current_stage": current_stage,
        "progress_pct": progress_pct,
        "overall_status": overall_status,
    }


def validate_stage_transition(from_status: str, to_status: str) -> dict[str, Any]:
    valid = {
        "pending": ["running"],
        "running": ["completed", "failed"],
        "completed": [],
        "failed": [],
    }

    allowed = valid.get(from_status, [])
    is_valid = to_status in allowed

    return {
        "transition_valid": is_valid,
        "from_status": from_status,
        "to_status": to_status,
    }
