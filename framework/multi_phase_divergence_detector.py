from typing import Any


def detect_phase_divergence(
    snapshot_a: dict[str, Any],
    snapshot_b: dict[str, Any],
    tolerance: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(snapshot_a, dict)
        or not isinstance(snapshot_b, dict)
        or not isinstance(tolerance, dict)
    ):
        return {
            "divergence_status": "invalid_input",
            "delta": None,
        }

    read_status_a = snapshot_a.get("read_status")
    read_status_b = snapshot_b.get("read_status")

    both_read = read_status_a == "read" and read_status_b == "read"

    if not both_read:
        if read_status_a == "read" or read_status_b == "read":
            return {
                "divergence_status": "partial_data",
                "delta": None,
            }
        return {
            "divergence_status": "invalid_input",
            "delta": None,
        }

    resource_count_a = snapshot_a.get("resource_count", 0)
    resource_count_b = snapshot_b.get("resource_count", 0)
    delta = abs(resource_count_a - resource_count_b)

    max_delta = tolerance.get("max_delta", 0)
    if not isinstance(max_delta, int):
        max_delta = 0

    if delta <= max_delta:
        return {
            "divergence_status": "no_divergence",
            "delta": delta,
        }
    else:
        return {
            "divergence_status": "diverged",
            "delta": delta,
        }
