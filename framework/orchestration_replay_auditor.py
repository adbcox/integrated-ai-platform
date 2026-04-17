from typing import Any


def audit_replay(
    original_trail: dict[str, Any],
    replay_trail: dict[str, Any],
    replay_plan: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(original_trail, dict)
        or not isinstance(replay_trail, dict)
        or not isinstance(replay_plan, dict)
    ):
        return {
            "audit_valid": False,
            "original_event_count": 0,
            "replay_event_count": 0,
            "original_completed": [],
            "replay_completed": [],
            "jobs_missing_in_replay": [],
            "jobs_new_in_replay": [],
            "replay_coverage": 0.0,
            "audit_status": "invalid_input",
        }

    original_completed = original_trail.get("completed_via_trail", [])
    replay_completed = replay_trail.get("completed_via_trail", [])
    if not isinstance(original_completed, list):
        original_completed = []
    if not isinstance(replay_completed, list):
        replay_completed = []

    jobs_missing = sorted([j for j in original_completed if j not in replay_completed])
    jobs_new = sorted([j for j in replay_completed if j not in original_completed])

    if len(original_completed) == 0 and len(replay_completed) == 0:
        replay_coverage = 100.0
    elif len(original_completed) > 0 and len(replay_completed) == 0:
        replay_coverage = 0.0
    else:
        replay_coverage = (
            round((len(replay_completed) / float(len(original_completed))) * 100.0, 3)
            if len(original_completed) > 0
            else 100.0
        )

    if len(jobs_new) > 0:
        status = "diverged"
    elif len(jobs_missing) > 0:
        status = "partial"
    elif replay_coverage == 100.0:
        status = "matched"
    else:
        status = "partial"

    return {
        "audit_valid": True,
        "original_event_count": int(original_trail.get("event_count", 0)),
        "replay_event_count": int(replay_trail.get("event_count", 0)),
        "original_completed": original_completed,
        "replay_completed": replay_completed,
        "jobs_missing_in_replay": jobs_missing,
        "jobs_new_in_replay": jobs_new,
        "replay_coverage": replay_coverage,
        "audit_status": status,
    }


def summarize_replay_audit(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("audit_valid") is not True:
        return {
            "summary_valid": False,
            "audit_status": "invalid_input",
            "replay_coverage": 0.0,
            "jobs_missing_count": 0,
        }

    return {
        "summary_valid": True,
        "audit_status": result.get("audit_status", "invalid_input"),
        "replay_coverage": float(result.get("replay_coverage", 0.0)),
        "jobs_missing_count": (
            len(result.get("jobs_missing_in_replay", []))
            if isinstance(result.get("jobs_missing_in_replay", []), list)
            else 0
        ),
    }
