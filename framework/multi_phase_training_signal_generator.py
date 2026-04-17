from typing import Any


def generate_training_signals(
    refinement: dict[str, Any],
    replay_learning: dict[str, Any],
    signal_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(refinement, dict)
        or not isinstance(replay_learning, dict)
        or not isinstance(signal_config, dict)
    ):
        return {
            "signal_status": "invalid_input",
            "signal_phase": None,
            "signal_count": 0,
        }

    ref_ok = refinement.get("refinement_status") == "refined"
    replay_ok = replay_learning.get("replay_learning_status") == "learned"

    if ref_ok and replay_ok:
        return {
            "signal_status": "generated",
            "signal_phase": refinement.get("refined_phase"),
            "signal_count": 2,
        }

    if not ref_ok:
        return {
            "signal_status": "no_refinement",
            "signal_phase": None,
            "signal_count": 0,
        }

    return {
        "signal_status": "invalid_input",
        "signal_phase": None,
        "signal_count": 0,
    }
