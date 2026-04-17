from typing import Any


def build_execution_context(
    jobs: list[dict[str, Any]],
    shared_params: dict[str, Any],
    environment: dict[str, Any],
    resources: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(jobs, list)
        or not isinstance(shared_params, dict)
        or not isinstance(environment, dict)
        or not isinstance(resources, dict)
    ):
        return {
            "context_valid": False,
            "context_id": "",
            "binding_count": 0,
            "job_bindings": {},
        }

    context_id = "ctx-{}".format(len(jobs))
    job_bindings = {}

    for job in jobs:
        if not isinstance(job, dict):
            continue
        job_id = job.get("job_id", "")
        if job_id:
            job_bindings[job_id] = {
                "context_id": context_id,
                "scoped_overrides": job.get("overrides", {}),
            }

    return {
        "context_valid": True,
        "context_id": context_id,
        "binding_count": len(job_bindings),
        "job_bindings": job_bindings,
    }


def lookup_job_context(
    context_result: dict[str, Any],
    job_id: str,
) -> dict[str, Any]:
    if not isinstance(context_result, dict):
        return {
            "lookup_valid": False,
            "context_id": "",
            "scoped_overrides": {},
        }

    bindings = context_result.get("job_bindings", {})
    binding = bindings.get(job_id, {})

    return {
        "lookup_valid": job_id in bindings,
        "context_id": binding.get("context_id", ""),
        "scoped_overrides": binding.get("scoped_overrides", {}),
    }
