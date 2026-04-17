from typing import Any


def check_archival_integrity(
    checkpoint_results: list[dict[str, Any]],
    archive_results: list[dict[str, Any]],
    trail_results: list[dict[str, Any]],
) -> dict[str, Any]:
    if (
        not isinstance(checkpoint_results, list)
        or not isinstance(archive_results, list)
        or not isinstance(trail_results, list)
    ):
        return {
            "integrity_valid": False,
            "workflow_count": 0,
            "checkpoints_valid": 0,
            "archives_valid": 0,
            "trails_valid": 0,
            "length_mismatch": False,
            "integrity_score": 0.0,
            "integrity_status": "invalid_input",
        }

    workflow_count = max(
        len(checkpoint_results), len(archive_results), len(trail_results)
    )
    checkpoints_valid = len(
        [
            r
            for r in checkpoint_results
            if isinstance(r, dict)
            and any(key.endswith("_valid") and r.get(key) is True for key in r.keys())
        ]
    )
    archives_valid = len(
        [
            r
            for r in archive_results
            if isinstance(r, dict)
            and any(key.endswith("_valid") and r.get(key) is True for key in r.keys())
        ]
    )
    trails_valid = len(
        [
            r
            for r in trail_results
            if isinstance(r, dict)
            and any(key.endswith("_valid") and r.get(key) is True for key in r.keys())
        ]
    )

    length_mismatch = not (
        len(checkpoint_results) == len(archive_results) == len(trail_results)
    )

    integrity_score = (
        round(
            (
                (checkpoints_valid + archives_valid + trails_valid)
                / float(workflow_count * 3)
            )
            * 100.0,
            3,
        )
        if workflow_count > 0
        else 0.0
    )

    if integrity_score == 100.0:
        status = "intact"
    elif integrity_score >= 66.0:
        status = "degraded"
    else:
        status = "compromised"

    return {
        "integrity_valid": True,
        "workflow_count": workflow_count,
        "checkpoints_valid": checkpoints_valid,
        "archives_valid": archives_valid,
        "trails_valid": trails_valid,
        "length_mismatch": length_mismatch,
        "integrity_score": integrity_score,
        "integrity_status": status,
    }


def summarize_archival_integrity(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("integrity_valid") is not True:
        return {
            "summary_valid": False,
            "integrity_status": "invalid_input",
            "integrity_score": 0.0,
            "length_mismatch": False,
        }

    return {
        "summary_valid": True,
        "integrity_status": result.get("integrity_status", "invalid_input"),
        "integrity_score": float(result.get("integrity_score", 0.0)),
        "length_mismatch": bool(result.get("length_mismatch", False)),
    }
