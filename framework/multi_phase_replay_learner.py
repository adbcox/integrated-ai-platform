from typing import Any


def learn_from_replay(
    replay: dict[str, Any], reward: dict[str, Any], replay_learning_config: dict[str, Any]
) -> dict[str, Any]:
    if (
        not isinstance(replay, dict)
        or not isinstance(reward, dict)
        or not isinstance(replay_learning_config, dict)
    ):
        return {
            "replay_learning_status": "invalid_input",
            "learned_phase": None,
            "learned_reward": 0.0,
        }

    replay_ok = replay.get("replay_status") == "replayed"
    reward_ok = reward.get("reward_status") == "calculated"

    if replay_ok and reward_ok:
        return {
            "replay_learning_status": "learned",
            "learned_phase": replay.get("replayed_phase"),
            "learned_reward": reward.get("reward_value", 0.0),
        }

    if not replay_ok:
        return {
            "replay_learning_status": "no_replay",
            "learned_phase": None,
            "learned_reward": 0.0,
        }

    return {
        "replay_learning_status": "invalid_input",
        "learned_phase": None,
        "learned_reward": 0.0,
    }
