from typing import Any

def classify_execution_outcome(exit_code: int, lifecycle_state: str, attempts_used: int, retry_budget: int) -> dict[str, Any]:
    if exit_code == 0 and lifecycle_state == "completed":
        return {
            "outcome_class": "success",
            "confidence": "high",
            "reasoning": "Exit code 0 and lifecycle completed"
        }
    if lifecycle_state == "failed" and attempts_used < retry_budget:
        return {
            "outcome_class": "retry_eligible",
            "confidence": "high",
            "reasoning": "Job failed but retry budget available"
        }
    if lifecycle_state == "escalated":
        return {
            "outcome_class": "escalated",
            "confidence": "high",
            "reasoning": "Job escalated to manual review"
        }
    if lifecycle_state == "failed" and attempts_used >= retry_budget:
        return {
            "outcome_class": "terminal_failure",
            "confidence": "high",
            "reasoning": "Job failed and retry budget exhausted"
        }
    return {
        "outcome_class": "unknown",
        "confidence": "low",
        "reasoning": "Unable to classify: exit_code={}, state={}".format(exit_code, lifecycle_state)
    }

def classify_by_task_class_pattern(task_class: str, success: bool) -> dict[str, Any]:
    if task_class and isinstance(task_class, str):
        lower_class = task_class.lower()
        if "learning" in lower_class:
            return {
                "outcome_class": "success" if success else "retry_eligible",
                "confidence": "medium",
                "reasoning": "Learning task classification for {}".format(task_class)
            }
        if "validation" in lower_class:
            return {
                "outcome_class": "success" if success else "escalated",
                "confidence": "medium",
                "reasoning": "Validation task classification for {}".format(task_class)
            }
    return {
        "outcome_class": "success" if success else "terminal_failure",
        "confidence": "medium",
        "reasoning": "Default outcome classification"
    }

def compute_outcome_confidence(metadata: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    base_confidence = classification.get("confidence", "low")
    if not isinstance(metadata, dict):
        return dict(classification, confidence=base_confidence)
    has_context = bool(metadata.get("execution_context_id"))
    has_metadata = len(metadata) > 2
    if has_context and has_metadata:
        final_confidence = "high"
    elif has_context or has_metadata:
        final_confidence = "medium"
    else:
        final_confidence = "low"
    return dict(classification, confidence=final_confidence)
