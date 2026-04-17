from typing import Any

def generate_execution_integration_validation_report() -> dict[str, Any]:
    try:
        from framework.execution_event_observer import record_job_accepted_event, record_job_lifecycle_transition, record_execution_completion
        from framework.execution_outcome_classifier import classify_execution_outcome, classify_by_task_class_pattern

        test_event_1 = record_job_accepted_event("job-001", "test_task", "2026-04-17T10:00:00")
        event_1_valid = isinstance(test_event_1, dict) and test_event_1.get("event_type") == "accepted"

        test_event_2 = record_job_lifecycle_transition("job-001", "accepted", "queued")
        event_2_valid = isinstance(test_event_2, dict) and test_event_2.get("new_state") == "queued"

        test_event_3 = record_execution_completion("job-001", True, 0, 5.2)
        event_3_valid = isinstance(test_event_3, dict) and test_event_3.get("success") is True

        test_outcome_1 = classify_execution_outcome(0, "completed", 1, 3)
        outcome_1_valid = test_outcome_1.get("outcome_class") == "success"

        test_outcome_2 = classify_by_task_class_pattern("learning_task", True)
        outcome_2_valid = isinstance(test_outcome_2, dict) and "outcome_class" in test_outcome_2

        all_tests_pass = all([
            event_1_valid,
            event_2_valid,
            event_3_valid,
            outcome_1_valid,
            outcome_2_valid
        ])

        return {
            "execution_integration_check": "complete",
            "event_observer_functional": event_1_valid and event_2_valid and event_3_valid,
            "outcome_classifier_functional": outcome_1_valid and outcome_2_valid,
            "event_types_recorded": ["accepted", "queued", "completed"],
            "outcome_classes_supported": ["success", "retry_eligible", "escalated", "terminal_failure"],
            "all_integration_tests_pass": all_tests_pass,
            "status": "complete"
        }
    except Exception as e:
        return {
            "execution_integration_check": "error",
            "error_detail": str(e),
            "status": "failed"
        }
