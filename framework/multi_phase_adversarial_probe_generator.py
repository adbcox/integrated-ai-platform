from typing import Any


def generate_adversarial_probes(
    scenarios: dict[str, Any],
    baseline: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scenarios, dict)
        or not isinstance(baseline, dict)
        or not isinstance(config, dict)
    ):
        return {
            "probe_status": "invalid_input",
            "probe_count": 0,
            "probe_phase": None,
        }

    s_ok = scenarios.get("scenario_status") == "generated"

    if s_ok:
        return {
            "probe_status": "generated",
            "probe_count": config.get("probes", 3),
            "probe_phase": scenarios.get("scenario_phase"),
        }

    return {
        "probe_status": "failed",
        "probe_count": 0,
        "probe_phase": None,
    }
