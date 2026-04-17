from typing import Any


def validate_orchestration_integration(
    plan_result: dict[str, Any],
    dependency_result: dict[str, Any],
    batch_result: dict[str, Any],
    advance_result: dict[str, Any],
    completion_result: dict[str, Any],
    report_result: dict[str, Any],
    reconcile_result: dict[str, Any],
    checkpoint_result: dict[str, Any],
    trail_result: dict[str, Any],
    end_state_result: dict[str, Any],
    archive_result: dict[str, Any],
) -> dict[str, Any]:
    args = [
        plan_result,
        dependency_result,
        batch_result,
        advance_result,
        completion_result,
        report_result,
        reconcile_result,
        checkpoint_result,
        trail_result,
        end_state_result,
        archive_result,
    ]

    if not all(isinstance(arg, dict) for arg in args):
        return {
            "integration_valid": False,
            "layer_checks": {},
            "passed_count": 0,
            "failed_count": 0,
            "failed_layers": [],
            "integration_status": "invalid_input",
        }

    layer_checks = {
        "plan": plan_result.get("plan_valid", False),
        "dependency": dependency_result.get("resolution_valid", False),
        "batch": batch_result.get("batch_valid", False),
        "advance": advance_result.get("advance_valid", False),
        "completion": completion_result.get("detection_valid", False),
        "report": report_result.get("report_valid", False),
        "reconcile": reconcile_result.get("reconcile_valid", False),
        "checkpoint": checkpoint_result.get("checkpoint_valid", False),
        "trail": trail_result.get("trail_valid", False),
        "end_state": end_state_result.get("validation_valid", False),
        "archive": archive_result.get("archive_valid", False),
    }

    failed_layers = sorted([name for name, ok in layer_checks.items() if not ok])
    passed_count = len(layer_checks) - len(failed_layers)
    failed_count = len(failed_layers)

    if failed_count == 0:
        status = "integrated"
    elif failed_count <= 3:
        status = "degraded"
    else:
        status = "failed"

    return {
        "integration_valid": True,
        "layer_checks": layer_checks,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "failed_layers": failed_layers,
        "integration_status": status,
    }


def summarize_integration_validation(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or result.get("integration_valid") is not True:
        return {
            "summary_valid": False,
            "integration_status": "invalid_input",
            "passed_count": 0,
            "failed_count": 0,
        }

    return {
        "summary_valid": True,
        "integration_status": result.get("integration_status", "invalid_input"),
        "passed_count": int(result.get("passed_count", 0)),
        "failed_count": int(result.get("failed_count", 0)),
    }
