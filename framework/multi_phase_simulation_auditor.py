from typing import Any


def audit_simulation(
    scenario_simulator: dict[str, Any],
    adversarial_tester: dict[str, Any],
    policy_stress_tester: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(scenario_simulator, dict)
        or not isinstance(adversarial_tester, dict)
        or not isinstance(policy_stress_tester, dict)
    ):
        return {
            "simulation_audit_status": "invalid_input",
            "audit_phase": None,
            "audit_result": None,
        }

    ss_ok = scenario_simulator.get("simulation_status") == "simulated"
    at_ok = adversarial_tester.get("adversarial_status") == "tested"
    pst_ok = policy_stress_tester.get("stress_status") == "stressed"
    all_ok = ss_ok and at_ok and pst_ok

    if all_ok:
        return {
            "simulation_audit_status": "passed",
            "audit_phase": scenario_simulator.get("simulation_phase"),
            "audit_result": "simulation_valid",
        }

    if (ss_ok and at_ok) or (ss_ok and pst_ok) or (at_ok and pst_ok):
        return {
            "simulation_audit_status": "degraded",
            "audit_phase": None,
            "audit_result": None,
        }

    return {
        "simulation_audit_status": "failed",
        "audit_phase": None,
        "audit_result": None,
    }
