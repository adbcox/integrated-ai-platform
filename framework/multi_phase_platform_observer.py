from typing import Any


def observe_platform(
    observability_cp: dict[str, Any],
    governance_cp: dict[str, Any],
    finalization: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(observability_cp, dict)
        or not isinstance(governance_cp, dict)
        or not isinstance(finalization, dict)
    ):
        return {
            "platform_status": "invalid_input",
            "observed_phase": None,
            "active_planes": 0,
        }

    obs_op = observability_cp.get("observability_cp_status") == "operational"
    gov_op = governance_cp.get("governance_cp_status") == "operational"
    fin_ok = finalization.get("finalization_status") in ("finalized", "pending")

    all_active = obs_op and gov_op and fin_ok
    any_active = obs_op or gov_op or fin_ok
    active_planes = sum([obs_op, gov_op, fin_ok])

    if all_active:
        return {
            "platform_status": "observed",
            "observed_phase": observability_cp.get("observability_phase"),
            "active_planes": active_planes,
        }

    if any_active:
        return {
            "platform_status": "partial",
            "observed_phase": None,
            "active_planes": active_planes,
        }

    return {
        "platform_status": "blind",
        "observed_phase": None,
        "active_planes": active_planes,
    }
