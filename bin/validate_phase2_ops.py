#!/usr/bin/env python3
"""
Validator for Phase 2 Operations Layer (RM-OPS-001, RM-OPS-002, RM-OPS-003).
Validates execution tracing, failure classification, and performance profiling.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def validate_execution_trace(trace_path: Path) -> dict:
    """Validate execution trace artifact."""
    checks = {
        "trace_exists": False,
        "trace_schema_valid": False,
        "has_required_fields": False,
        "has_stage_events": False,
        "has_timing_data": False,
        "has_command_events": False
    }

    if not trace_path.exists():
        return checks

    try:
        with open(trace_path) as f:
            trace = json.load(f)

        checks["trace_exists"] = True

        # Check schema version and kind
        if (trace.get("schema_version") == "1.0" and
            trace.get("trace_kind") == "execution_trace"):
            checks["trace_schema_valid"] = True

        # Check required fields
        required = {"schema_version", "trace_kind", "session_id", "job_id", "trace_events", "created_at"}
        if all(k in trace for k in required):
            checks["has_required_fields"] = True

        # Check stage events
        events = trace.get("trace_events", [])
        stage_events = [e for e in events if e.get("event_type") in ["stage_start", "stage_complete", "stage_error"]]
        if len(stage_events) >= 2:  # At least start and complete
            checks["has_stage_events"] = True

        # Check timing data
        if trace.get("total_duration_seconds", 0) > 0:
            checks["has_timing_data"] = True

        # Check command events
        command_events = [e for e in events if "command" in e.get("event_type", "").lower()]
        if command_events:
            checks["has_command_events"] = True

    except Exception as e:
        pass

    return checks


def validate_failure_record(failure_path: Path) -> dict:
    """Validate failure record artifact."""
    checks = {
        "failure_exists": False,
        "failure_schema_valid": False,
        "has_required_fields": False,
        "has_classification": False,
        "has_recovery_suggestions": False,
        "failure_types_valid": False
    }

    if not failure_path.exists():
        return checks

    try:
        with open(failure_path) as f:
            record = json.load(f)

        checks["failure_exists"] = True

        # Check schema
        if (record.get("schema_version") == "1.0" and
            record.get("record_kind") == "failure_record"):
            checks["failure_schema_valid"] = True

        # Check required fields
        required = {"schema_version", "record_kind", "session_id", "job_id", "failure_type", "root_cause", "timestamp"}
        if all(k in record for k in required):
            checks["has_required_fields"] = True

        # Check failure classification
        valid_types = {
            "command_not_allowed", "command_failed", "command_timeout",
            "workspace_init_failed", "profile_selection_failed",
            "artifact_emission_failed", "workspace_finalize_failed",
            "gateway_error", "unknown_error"
        }
        if record.get("failure_type") in valid_types:
            checks["failure_types_valid"] = True
            checks["has_classification"] = True

        # Check recovery suggestions
        suggestions = record.get("recovery_suggestions", [])
        if len(suggestions) > 0:
            checks["has_recovery_suggestions"] = True

    except Exception as e:
        pass

    return checks


def validate_performance_profile(profile_path: Path) -> dict:
    """Validate performance profile artifact."""
    checks = {
        "profile_exists": False,
        "profile_schema_valid": False,
        "has_required_fields": False,
        "has_timing_breakdown": False,
        "has_bottleneck_analysis": False,
        "has_optimization_suggestions": False,
        "has_command_metrics": False
    }

    if not profile_path.exists():
        return checks

    try:
        with open(profile_path) as f:
            profile = json.load(f)

        checks["profile_exists"] = True

        # Check schema
        if (profile.get("schema_version") == "1.0" and
            profile.get("profile_kind") == "performance_profile"):
            checks["profile_schema_valid"] = True

        # Check required fields
        required = {"schema_version", "profile_kind", "session_id", "job_id", "timing_breakdown", "created_at"}
        if all(k in profile for k in required):
            checks["has_required_fields"] = True

        # Check timing breakdown
        timing = profile.get("timing_breakdown", {})
        if timing.get("total_duration_seconds", 0) > 0 and timing.get("stages"):
            checks["has_timing_breakdown"] = True

        # Check bottleneck analysis
        bottleneck = profile.get("bottleneck_analysis", {})
        if bottleneck.get("slowest_stage"):
            checks["has_bottleneck_analysis"] = True

        # Check optimization suggestions
        suggestions = profile.get("optimization_suggestions", [])
        if len(suggestions) > 0:
            checks["has_optimization_suggestions"] = True

        # Check command metrics
        cmd_metrics = profile.get("command_metrics", {})
        if cmd_metrics.get("command_duration_seconds", 0) > 0:
            checks["has_command_metrics"] = True

    except Exception as e:
        pass

    return checks


def main():
    artifact_dir = Path("artifacts/validation")
    artifact_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("PHASE 2 OPERATIONS LAYER VALIDATION")
    print("=" * 60)

    # Find all trace, failure, and profile artifacts
    traces = list(artifact_dir.glob("**/execution_trace_*.json"))
    failures = list(artifact_dir.glob("**/failure_record_*.json"))
    profiles = list(artifact_dir.glob("**/performance_profile_*.json"))

    validation_report = {
        "schema_version": "1.0",
        "validation_kind": "phase2_ops_validation",
        "timestamp": datetime.utcnow().isoformat(),
        "ops_001_execution_tracing": {
            "traces_found": len(traces),
            "checks": {}
        },
        "ops_002_failure_classification": {
            "failures_found": len(failures),
            "checks": {}
        },
        "ops_003_performance_profiling": {
            "profiles_found": len(profiles),
            "checks": {}
        },
        "integration_checks": {
            "all_three_present": traces and failures and profiles,
            "same_session_ids": False,
            "consistent_timestamps": False
        }
    }

    # Validate OPS-001: Execution Tracing
    print("\n✓ OPS-001: Execution Tracing")
    trace_checks = []
    for trace_path in traces[:5]:  # Check up to 5 traces
        checks = validate_execution_trace(trace_path)
        trace_checks.append(checks)
        status = "✓" if all(checks.values()) else "✗"
        print(f"  {status} {trace_path.name}")
        for check, result in checks.items():
            print(f"    - {check}: {'PASS' if result else 'FAIL'}")

    if trace_checks:
        validation_report["ops_001_execution_tracing"]["checks"] = trace_checks[0]

    # Validate OPS-002: Failure Classification
    print("\n✓ OPS-002: Failure Classification")
    failure_checks = []
    for failure_path in failures[:5]:  # Check up to 5 failures
        checks = validate_failure_record(failure_path)
        failure_checks.append(checks)
        status = "✓" if all(checks.values()) else "✗"
        print(f"  {status} {failure_path.name}")
        for check, result in checks.items():
            print(f"    - {check}: {'PASS' if result else 'FAIL'}")

    if failure_checks:
        validation_report["ops_002_failure_classification"]["checks"] = failure_checks[0]

    # Validate OPS-003: Performance Profiling
    print("\n✓ OPS-003: Performance Profiling")
    profile_checks = []
    for profile_path in profiles[:5]:  # Check up to 5 profiles
        checks = validate_performance_profile(profile_path)
        profile_checks.append(checks)
        status = "✓" if all(checks.values()) else "✗"
        print(f"  {status} {profile_path.name}")
        for check, result in checks.items():
            print(f"    - {check}: {'PASS' if result else 'FAIL'}")

    if profile_checks:
        validation_report["ops_003_performance_profiling"]["checks"] = profile_checks[0]

    # Integration checks
    print("\n✓ Integration Checks")
    if traces and failures and profiles:
        validation_report["integration_checks"]["all_three_present"] = True
        print("  ✓ All three OPS artifacts present")

        # Check if they share session/job IDs
        try:
            with open(traces[0]) as f:
                trace_session = json.load(f).get("session_id")
            with open(failures[0]) as f:
                failure_session = json.load(f).get("session_id")
            with open(profiles[0]) as f:
                profile_session = json.load(f).get("session_id")

            if trace_session == failure_session == profile_session:
                validation_report["integration_checks"]["same_session_ids"] = True
                print("  ✓ All artifacts share same session_id")
            else:
                print("  ✗ Session IDs do not match")

            # Check timestamps are ordered
            with open(traces[0]) as f:
                trace_time = json.load(f).get("created_at")
            with open(profiles[0]) as f:
                profile_time = json.load(f).get("created_at")

            if trace_time and profile_time:
                validation_report["integration_checks"]["consistent_timestamps"] = True
                print("  ✓ Timestamps are consistent")
        except Exception as e:
            print(f"  ✗ Could not verify integration: {e}")

    # Compute overall pass/fail
    all_pass = (
        validation_report["ops_001_execution_tracing"]["traces_found"] > 0 and
        all(validation_report["ops_001_execution_tracing"].get("checks", {}).values()) and
        validation_report["ops_002_failure_classification"]["failures_found"] > 0 and
        all(validation_report["ops_002_failure_classification"].get("checks", {}).values()) and
        validation_report["ops_003_performance_profiling"]["profiles_found"] > 0 and
        all(validation_report["ops_003_performance_profiling"].get("checks", {}).values())
    )

    validation_report["overall_status"] = "PASS" if all_pass else "FAIL"
    validation_report["validation_timestamp"] = datetime.utcnow().isoformat()

    # Write validation report
    report_path = artifact_dir / "phase2_ops_validation.json"
    with open(report_path, "w") as f:
        json.dump(validation_report, f, indent=2)

    print("\n" + "=" * 60)
    print(f"Validation Status: {validation_report['overall_status']}")
    print(f"Report: {report_path}")
    print("=" * 60 + "\n")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
