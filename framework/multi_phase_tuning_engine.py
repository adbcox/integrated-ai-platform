from typing import Any


def tune_parameters(
    profile: dict[str, Any],
    trend: dict[str, Any],
    tuning_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(profile, dict)
        or not isinstance(trend, dict)
        or not isinstance(tuning_config, dict)
    ):
        return {
            "tuning_status": "invalid_input",
            "tuned_phase": None,
            "tuning_strategy": None,
        }

    profile_ok = profile.get("profile_status") == "profiled"
    trend_ok = trend.get("trend_status") == "analyzed"

    if not profile_ok:
        return {
            "tuning_status": "no_profile",
            "tuned_phase": None,
            "tuning_strategy": None,
        }

    if profile_ok and trend_ok:
        return {
            "tuning_status": "tuned",
            "tuned_phase": profile.get("profiled_phase"),
            "tuning_strategy": tuning_config.get("strategy", "gradient"),
        }

    return {
        "tuning_status": "invalid_input",
        "tuned_phase": None,
        "tuning_strategy": None,
    }
