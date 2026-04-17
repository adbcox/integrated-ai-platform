from typing import Any


def dispatch_phase_job(
    coordinator: dict[str, Any],
    job: dict[str, Any],
    control_plane: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(coordinator, dict)
        or not isinstance(job, dict)
        or not isinstance(control_plane, dict)
    ):
        return {
            "dispatch_status": "invalid_input",
            "dispatched_job_id": None,
            "target_phase": None,
        }

    dispatch_allowed = (
        coordinator.get("coordinator_status") == "initialized"
        and control_plane.get("control_plane_status") in ("operational", "degraded")
    )

    coordinator_status = coordinator.get("coordinator_status")
    control_plane_status = control_plane.get("control_plane_status")
    job_id = job.get("job_id")

    if not dispatch_allowed:
        if coordinator_status != "initialized":
            return {
                "dispatch_status": "coordinator_not_ready",
                "dispatched_job_id": None,
                "target_phase": coordinator.get("phase_id"),
            }
        if control_plane_status == "offline":
            return {
                "dispatch_status": "control_plane_offline",
                "dispatched_job_id": None,
                "target_phase": coordinator.get("phase_id"),
            }

    if dispatch_allowed and isinstance(job, dict) and job_id:
        return {
            "dispatch_status": "dispatched",
            "dispatched_job_id": job_id,
            "target_phase": coordinator.get("phase_id"),
        }

    return {
        "dispatch_status": "invalid_input",
        "dispatched_job_id": None,
        "target_phase": coordinator.get("phase_id"),
    }
