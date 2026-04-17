from typing import Any


def build_dispatch_scenario(
    job_count: int,
    failure_mode: str,
) -> dict[str, Any]:
    if job_count < 0:
        return {
            "scenario_valid": False,
            "jobs": [],
            "failure_mode": "",
            "job_count": 0,
        }

    jobs = []
    for idx in range(job_count):
        jobs.append({
            "job_id": "job-{}".format(idx + 1),
            "lifecycle": "accepted",
            "priority": "p2",
            "failure_mode": failure_mode if idx == job_count - 1 and failure_mode else "",
        })

    return {
        "scenario_valid": True,
        "jobs": jobs,
        "failure_mode": failure_mode,
        "job_count": len(jobs),
    }


def playback_dispatch_scenario(
    scenario: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(scenario, dict):
        return {
            "playback_valid": False,
            "jobs_played": 0,
            "failure_injected": False,
        }

    jobs = scenario.get("jobs", [])
    failure_mode = scenario.get("failure_mode", "")

    return {
        "playback_valid": True,
        "jobs_played": len(jobs) if isinstance(jobs, list) else 0,
        "failure_injected": failure_mode != "",
    }
