from typing import Any


def rollup_curriculum(
    curriculum_shaper: dict[str, Any],
    difficulty_scheduler: dict[str, Any],
    progression_tracker: dict[str, Any],
    rollup_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(curriculum_shaper, dict)
        or not isinstance(difficulty_scheduler, dict)
        or not isinstance(progression_tracker, dict)
        or not isinstance(rollup_config, dict)
    ):
        return {
            "curriculum_rollup_status": "invalid_input",
            "rollup_phase": None,
            "curriculum_maturity": None,
        }

    cs_ok = curriculum_shaper.get("curriculum_status") == "shaped"
    ds_ok = difficulty_scheduler.get("difficulty_status") == "scheduled"
    pt_ok = progression_tracker.get("progression_status") == "tracked"
    all_ok = cs_ok and ds_ok and pt_ok

    if all_ok:
        return {
            "curriculum_rollup_status": "rolled_up",
            "rollup_phase": curriculum_shaper.get("curriculum_phase"),
            "curriculum_maturity": rollup_config.get("maturity_level", "standard"),
        }

    if (cs_ok and ds_ok) or (cs_ok and pt_ok) or (ds_ok and pt_ok):
        return {
            "curriculum_rollup_status": "degraded",
            "rollup_phase": None,
            "curriculum_maturity": None,
        }

    return {
        "curriculum_rollup_status": "offline",
        "rollup_phase": None,
        "curriculum_maturity": None,
    }
