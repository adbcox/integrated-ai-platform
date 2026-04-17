from typing import Any


def rollup_adversarial(
    adversarial_tester: dict[str, Any],
    policy_stress_tester: dict[str, Any],
    failure_mode_cataloger: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(adversarial_tester, dict)
        or not isinstance(policy_stress_tester, dict)
        or not isinstance(failure_mode_cataloger, dict)
    ):
        return {
            "adversarial_rollup_status": "invalid_input",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    at_ok = adversarial_tester.get("adversarial_status") == "tested"
    pst_ok = policy_stress_tester.get("stress_status") == "stressed"
    fmc_ok = failure_mode_cataloger.get("failure_catalog_status") == "cataloged"
    all_ok = at_ok and pst_ok and fmc_ok

    if all_ok:
        return {
            "adversarial_rollup_status": "rolled_up",
            "rollup_phase": adversarial_tester.get("test_count"),
            "rollup_count": failure_mode_cataloger.get("failure_count", 0),
        }

    if (at_ok and pst_ok) or (at_ok and fmc_ok) or (pst_ok and fmc_ok):
        return {
            "adversarial_rollup_status": "degraded",
            "rollup_phase": None,
            "rollup_count": 0,
        }

    return {
        "adversarial_rollup_status": "offline",
        "rollup_phase": None,
        "rollup_count": 0,
    }
