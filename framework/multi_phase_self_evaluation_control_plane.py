from typing import Any


def build_self_evaluation_control_plane(
    self_evaluation_auditor: dict[str, Any],
    simulation_rollup: dict[str, Any],
    event_bus: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(self_evaluation_auditor, dict)
        or not isinstance(simulation_rollup, dict)
        or not isinstance(event_bus, dict)
    ):
        return {
            "self_eval_cp_status": "offline",
            "cp_phase": None,
            "message_count": 0,
        }

    sea_ok = self_evaluation_auditor.get("self_eval_audit_status") == "passed"
    sr_ok = simulation_rollup.get("simulation_rollup_status") == "rolled_up"
    eb_ok = event_bus.get("message_count", 0) >= 0
    all_ok = sea_ok and sr_ok and eb_ok

    if all_ok:
        return {
            "self_eval_cp_status": "operational",
            "cp_phase": self_evaluation_auditor.get("audit_phase"),
            "message_count": event_bus.get("message_count", 0),
        }

    if (sea_ok and sr_ok) or (sea_ok and eb_ok) or (sr_ok and eb_ok):
        return {
            "self_eval_cp_status": "degraded",
            "cp_phase": None,
            "message_count": 0,
        }

    return {
        "self_eval_cp_status": "offline",
        "cp_phase": None,
        "message_count": 0,
    }
