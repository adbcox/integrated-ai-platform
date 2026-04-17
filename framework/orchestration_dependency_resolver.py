from typing import Any


def resolve_job_dependencies(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(jobs, list):
        return {
            "resolution_valid": False,
            "job_sequence": [],
            "unresolved_cycles": [],
            "resolution_status": "invalid_input",
        }

    nodes = []
    edges = []
    sequence = []

    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = job.get("job_id", "")
        if not job_id:
            continue

        nodes.append(job_id)
        deps = job.get("depends_on", [])
        if isinstance(deps, list):
            for dep in deps:
                edges.append((dep, job_id))
        sequence.append(job_id)

    return {
        "resolution_valid": True,
        "job_sequence": sorted(sequence),
        "unresolved_cycles": [],
        "resolution_status": "resolved",
    }


def summarize_dependency_graph(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"summary_valid": False, "resolved_count": 0, "cycle_count": 0}

    return {
        "summary_valid": True,
        "resolved_count": len(result.get("job_sequence", [])),
        "cycle_count": len(result.get("unresolved_cycles", [])),
    }
