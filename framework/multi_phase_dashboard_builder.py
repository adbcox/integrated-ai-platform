from typing import Any


def build_dashboard(
    metrics: dict[str, Any],
    fusion: dict[str, Any],
    correlation: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(metrics, dict)
        or not isinstance(fusion, dict)
        or not isinstance(correlation, dict)
    ):
        return {
            "dashboard_status": "invalid_input",
            "dashboard_phase": None,
            "signal_count": 0,
        }

    metrics_ok = metrics.get("metrics_status") == "collected"
    fusion_ok = fusion.get("fusion_status") in ("fused", "partial")
    correlation_ok = correlation.get("correlation_status") in ("correlated", "no_alerts")

    all_ok = metrics_ok and fusion_ok and correlation_ok
    any_ok = metrics_ok or fusion_ok or correlation_ok

    if all_ok:
        return {
            "dashboard_status": "built",
            "dashboard_phase": metrics.get("collected_phase"),
            "signal_count": int(fusion.get("signal_count", 0)),
        }

    if any_ok:
        return {
            "dashboard_status": "partial",
            "dashboard_phase": None,
            "signal_count": 0,
        }

    return {
        "dashboard_status": "invalid_input",
        "dashboard_phase": None,
        "signal_count": 0,
    }
