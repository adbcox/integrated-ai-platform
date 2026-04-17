from typing import Any


def build_job_batches(
    jobs: list[dict[str, Any]],
    batch_size: int,
) -> dict[str, Any]:
    if not isinstance(jobs, list) or batch_size <= 0:
        return {"batch_valid": False, "batches": [], "batch_count": 0}

    valid_jobs = [
        j for j in jobs if isinstance(j, dict) and j.get("job_id", "")
    ]

    batches = []
    for idx in range(0, len(valid_jobs), batch_size):
        chunk = valid_jobs[idx : idx + batch_size]
        batches.append({
            "batch_id": "batch-{}".format(len(batches) + 1),
            "job_ids": [j.get("job_id", "") for j in chunk],
            "batch_type": "default",
            "status": "pending",
        })

    return {
        "batch_valid": True,
        "batches": batches,
        "batch_count": len(batches),
    }


def summarize_batch_coordination(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"summary_valid": False, "batch_count": 0, "job_count": 0}

    batches = result.get("batches", [])
    job_count = sum(
        len(batch.get("job_ids", []))
        for batch in batches
        if isinstance(batch, dict)
    )

    return {
        "summary_valid": True,
        "batch_count": len(batches),
        "job_count": job_count,
    }
