from typing import Any


def cluster_dispatch_failures(
    failures: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(failures, list):
        return {
            "clustering_valid": False,
            "cluster_count": 0,
            "clusters": {},
            "dominant_failure_mode": "",
        }

    clusters = {}
    for failure in failures:
        if not isinstance(failure, dict):
            continue
        failure_type = failure.get("failure_type", "unknown")
        clusters[failure_type] = clusters.get(failure_type, 0) + 1

    dominant = ""
    if clusters:
        dominant = sorted(
            clusters.items(), key=lambda item: (-item[1], item[0])
        )[0][0]

    return {
        "clustering_valid": True,
        "cluster_count": len(clusters),
        "clusters": {k: clusters[k] for k in sorted(clusters.keys())},
        "dominant_failure_mode": dominant,
    }
