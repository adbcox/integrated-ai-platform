from typing import Any


def analyze_phase_trends(
    profile: dict[str, Any],
    metrics_rollup: dict[str, Any],
    window_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(profile, dict)
        or not isinstance(metrics_rollup, dict)
        or not isinstance(window_config, dict)
    ):
        return {
            "trend_status": "invalid_input",
            "trend_phase": None,
            "sample_count": 0,
            "window_size": 0,
        }

    profile_ok = profile.get("profile_status") == "profiled"
    rollup_ok = metrics_rollup.get("metrics_rollup_status") == "rolled_up"

    if profile_ok and rollup_ok:
        return {
            "trend_status": "analyzed",
            "trend_phase": profile.get("profiled_phase"),
            "sample_count": int(profile.get("sample_count", 0)),
            "window_size": int(window_config.get("window", 10)),
        }

    return {
        "trend_status": "insufficient_data",
        "trend_phase": None,
        "sample_count": 0,
        "window_size": 0,
    }
