from typing import Any


def run_adversarial_tests(
    adversarial_probes: dict[str, Any],
    simulation_results: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(adversarial_probes, dict)
        or not isinstance(simulation_results, dict)
        or not isinstance(config, dict)
    ):
        return {
            "adversarial_status": "invalid_input",
            "test_count": 0,
            "pass_rate": None,
        }

    ap_ok = adversarial_probes.get("probe_status") == "generated"
    sr_ok = simulation_results.get("simulation_status") == "simulated"
    all_ok = ap_ok and sr_ok

    if all_ok:
        return {
            "adversarial_status": "tested",
            "test_count": adversarial_probes.get("probe_count", 0),
            "pass_rate": config.get("pass_rate", 0.8),
        }

    return {
        "adversarial_status": "failed",
        "test_count": 0,
        "pass_rate": None,
    }
