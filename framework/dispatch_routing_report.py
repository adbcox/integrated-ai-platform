from typing import Any


def generate_dispatch_routing_report(routes: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(routes, list):
        return {
            "report_valid": False,
            "routed_count": 0,
            "success_rate": 0.0,
            "retry_rate": 0.0,
            "bottlenecks": [],
        }

    valid_routes = [r for r in routes if isinstance(r, dict)]
    routed_count = len(valid_routes)

    success_count = len(
        [r for r in valid_routes if r.get("route_reason") == "success"]
    )
    retry_count = len(
        [
            r
            for r in valid_routes
            if r.get("route_reason") in ["timeout", "failure"]
        ]
    )

    bottleneck_map = {}
    for route in valid_routes:
        reason = route.get("route_reason", "")
        if reason and reason not in ["success", "timeout", "failure", "cancelled"]:
            bottleneck_map[reason] = bottleneck_map.get(reason, 0) + 1

    success_rate = (
        round(success_count / float(routed_count), 3) if routed_count > 0 else 0.0
    )
    retry_rate = (
        round(retry_count / float(routed_count), 3) if routed_count > 0 else 0.0
    )

    return {
        "report_valid": True,
        "routed_count": routed_count,
        "success_rate": success_rate,
        "retry_rate": retry_rate,
        "bottlenecks": sorted(bottleneck_map.keys()),
    }
