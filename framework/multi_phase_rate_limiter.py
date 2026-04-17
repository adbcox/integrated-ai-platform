from typing import Any


def rate_limit_batch(
    batch_size: int,
    time_window_ms: int,
    max_per_window: int,
    current_count: int,
) -> dict[str, Any]:
    if (
        not isinstance(batch_size, int)
        or not isinstance(time_window_ms, int)
        or not isinstance(max_per_window, int)
        or not isinstance(current_count, int)
    ):
        return {
            "rate_limit_status": "invalid_input",
            "allowed": False,
            "tokens_remaining": 0,
        }

    if time_window_ms <= 0 or max_per_window <= 0 or batch_size <= 0:
        return {
            "rate_limit_status": "invalid_input",
            "allowed": False,
            "tokens_remaining": 0,
        }

    tokens_available = max_per_window - current_count

    if tokens_available <= 0:
        return {
            "rate_limit_status": "limit_reached",
            "allowed": False,
            "tokens_remaining": 0,
        }

    if batch_size > tokens_available:
        return {
            "rate_limit_status": "insufficient_tokens",
            "allowed": False,
            "tokens_remaining": tokens_available,
        }

    remaining = tokens_available - batch_size

    return {
        "rate_limit_status": "allowed",
        "allowed": True,
        "tokens_remaining": remaining,
    }
