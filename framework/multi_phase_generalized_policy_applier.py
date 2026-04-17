from typing import Any


def apply_generalized_policy(
    lookahead: dict[str, Any],
    refinement: dict[str, Any],
    policy_apply_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(lookahead, dict)
        or not isinstance(refinement, dict)
        or not isinstance(policy_apply_config, dict)
    ):
        return {
            "policy_apply_status": "invalid_input",
            "policy_phase": None,
            "policy_scope": None,
        }

    lookahead_ok = lookahead.get("lookahead_status") == "evaluated"
    refinement_ok = refinement.get("refinement_status") == "refined"

    if lookahead_ok and refinement_ok:
        return {
            "policy_apply_status": "applied",
            "policy_phase": lookahead.get("lookahead_phase"),
            "policy_scope": policy_apply_config.get("scope", "global"),
        }

    if not lookahead_ok:
        return {
            "policy_apply_status": "no_lookahead",
            "policy_phase": None,
            "policy_scope": None,
        }

    return {
        "policy_apply_status": "invalid_input",
        "policy_phase": None,
        "policy_scope": None,
    }
