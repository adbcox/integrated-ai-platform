from typing import Any


def build_operator_checklist(
    briefing: dict[str, Any],
    promotion_summary: dict[str, Any],
    checklist_config: dict[str, Any],
) -> dict[str, Any]:
    if (
        not isinstance(briefing, dict)
        or not isinstance(promotion_summary, dict)
        or not isinstance(checklist_config, dict)
    ):
        return {
            "checklist_status": "invalid_input",
            "checklist_phase": None,
            "checklist_items": 0,
        }

    briefing_ok = briefing.get("briefing_status") == "generated"
    promo_ok = promotion_summary.get("promotion_summary_status") == "complete"

    if briefing_ok and promo_ok:
        return {
            "checklist_status": "built",
            "checklist_phase": briefing.get("briefing_phase"),
            "checklist_items": 10,
        }

    return {
        "checklist_status": "failed",
        "checklist_phase": None,
        "checklist_items": 0,
    }
