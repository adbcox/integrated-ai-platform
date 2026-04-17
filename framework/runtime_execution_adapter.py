from typing import Any

def adapt_runtime_to_execution(
    job_config: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(job_config, dict):
        return {
            "execution_config": {},
            "adaptation_valid": False,
            "adaptation_errors": ["invalid_job_config"],
        }
    adaptation_errors = []
    execution_config = {
        "job_id": job_config.get("job_id", "unknown"),
        "task_class": job_config.get("task_class", "unknown"),
        "priority": job_config.get("priority", "p2"),
        "retry_budget": job_config.get("retry_budget", 0),
        "action": job_config.get("action", "shell_command"),
    }
    if "job_id" not in job_config:
        adaptation_errors.append("missing_job_id")
    return {
        "execution_config": execution_config,
        "adaptation_valid": len(adaptation_errors) == 0,
        "adaptation_errors": adaptation_errors,
    }
