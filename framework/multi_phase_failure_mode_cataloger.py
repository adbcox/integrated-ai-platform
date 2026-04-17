from typing import Any


def catalog_failure_modes(
    adversarial_results: dict[str, Any],
    critique_extraction: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(adversarial_results, dict)
        or not isinstance(critique_extraction, dict)
        or not isinstance(config, dict)
    ):
        return {
            "failure_catalog_status": "invalid_input",
            "failure_count": 0,
            "failure_phase": None,
        }

    ar_ok = adversarial_results.get("adversarial_status") == "tested"
    ce_ok = critique_extraction.get("critique_status") == "extracted"
    all_ok = ar_ok and ce_ok

    if all_ok:
        return {
            "failure_catalog_status": "cataloged",
            "failure_count": adversarial_results.get("test_count", 0),
            "failure_phase": critique_extraction.get("critique_phase"),
        }

    return {
        "failure_catalog_status": "failed",
        "failure_count": 0,
        "failure_phase": None,
    }
