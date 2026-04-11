from __future__ import annotations

import os

BAD_MARKERS = [
    "REPLACE_",
    "change-me",
    "CHANGE_ME",
    "your-",
    "YOUR_",
]


def _is_bad(value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return True
    lower_v = v.lower()
    for marker in BAD_MARKERS:
        if marker.lower() in lower_v:
            return True
    return False


def require_valid_env() -> None:
    required = {
        "API_TOKEN": os.environ.get("API_TOKEN", ""),
    }
    bad = [key for key, value in required.items() if _is_bad(value)]
    if bad:
        joined = ", ".join(bad)
        raise RuntimeError(
            f"Invalid configuration. Replace placeholder or empty values for: {joined}"
        )
