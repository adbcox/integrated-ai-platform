from typing import Any


def schedule_milestones(
    trajectory: dict[str, Any],
    curriculum: dict[str, Any],
    milestone_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(trajectory, dict)
        or not isinstance(curriculum, dict)
        or not isinstance(milestone_config, dict)
    ):
        return {
            "milestone_status": "invalid_input",
            "milestone_phase": None,
            "milestone_count": 0,
        }

    trajectory_ok = trajectory.get("trajectory_status") == "optimized"
    curriculum_ok = curriculum.get("curriculum_status") == "shaped"

    if trajectory_ok and curriculum_ok:
        return {
            "milestone_status": "scheduled",
            "milestone_phase": trajectory.get("trajectory_phase"),
            "milestone_count": milestone_config.get("count", 5),
        }

    if not trajectory_ok:
        return {
            "milestone_status": "no_trajectory",
            "milestone_phase": None,
            "milestone_count": 0,
        }

    return {
        "milestone_status": "invalid_input",
        "milestone_phase": None,
        "milestone_count": 0,
    }
