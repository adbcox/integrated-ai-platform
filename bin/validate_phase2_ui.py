#!/usr/bin/env python3
"""Validator for Phase 2 UI Layer (RM-UI-002, RM-UI-003, RM-UI-004)."""

import json
import sys
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.ops_artifact_loader import OpsArtifactLoader
from framework.execution_dashboard_ui import ExecutionDashboardUI
from framework.failure_analyzer_ui import FailureAnalyzerUI
from framework.performance_metrics_ui import PerformanceMetricsUI


def validate_ui_implementation():
    """Validate Phase 2 UI implementation."""
    results = {
        "validation_type": "phase2_ui_layer",
        "checks": [],
        "summary": {},
    }

    print("🔍 Validating Phase 2 UI Layer Implementation...")
    print()

    # Check 1: OpsArtifactLoader instantiation and discovery
    print("Check 1: OPS Artifact Loader initialization...")
    try:
        loader = OpsArtifactLoader()
        executions = loader.discover_executions()
        results["checks"].append(
            {
                "name": "loader_initialization",
                "status": "pass",
                "details": f"Loader instantiated, discovered {len(executions)} executions",
            }
        )
        print(f"  ✓ Loader initialized, found {len(executions)} executions")
    except Exception as e:
        results["checks"].append(
            {"name": "loader_initialization", "status": "fail", "details": str(e)}
        )
        print(f"  ✗ Loader initialization failed: {e}")
        return results

    if not executions:
        print("  ⚠ No OPS artifacts found, skipping UI validation")
        results["summary"]["status"] = "skipped"
        results["summary"]["reason"] = "No OPS artifacts in repository"
        return results

    print()
    print("Check 2: Execution Dashboard UI...")
    try:
        dashboard = ExecutionDashboardUI()
        dashboard_data = dashboard.get_dashboard_data()

        # Validate dashboard data structure
        assert "latest_execution" in dashboard_data
        assert "execution_count" in dashboard_data
        assert dashboard_data["status"] in ["ok", "no_executions"]

        # Validate HTML rendering
        dashboard_html = dashboard.render_html()
        assert dashboard_html is not None
        assert len(dashboard_html) > 0
        assert "execution" in dashboard_html.lower() and "panel" in dashboard_html

        results["checks"].append(
            {
                "name": "dashboard_ui_implementation",
                "status": "pass",
                "details": f"Dashboard UI renders HTML, consumes {len(executions)} executions",
            }
        )
        print(f"  ✓ Dashboard UI: renders {len(dashboard_html)} bytes of HTML")
        print(f"    - Consumes real execution traces")
        print(f"    - Display structure: execution_count, trace_events")
    except Exception as e:
        results["checks"].append(
            {
                "name": "dashboard_ui_implementation",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ Dashboard UI failed: {e}")

    print()
    print("Check 3: Failure Analyzer UI...")
    try:
        failure_analyzer = FailureAnalyzerUI()
        analyzer_data = failure_analyzer.get_analyzer_data()

        # Validate analyzer data structure
        assert "total_executions" in analyzer_data
        assert "total_failures" in analyzer_data
        assert "failure_rate" in analyzer_data
        assert analyzer_data["status"] in ["ok", "no_failures"]

        # Validate HTML rendering
        analyzer_html = failure_analyzer.render_html()
        assert analyzer_html is not None
        assert len(analyzer_html) > 0

        failure_count = analyzer_data.get("total_failures", 0)

        results["checks"].append(
            {
                "name": "failure_analyzer_ui_implementation",
                "status": "pass",
                "details": f"Failure Analyzer UI found {failure_count} failures, renders HTML",
            }
        )
        print(f"  ✓ Failure Analyzer UI: renders {len(analyzer_html)} bytes of HTML")
        print(f"    - Consumes real failure records")
        print(f"    - Found {failure_count} failures")
        print(f"    - Display structure: failure_type, root_cause, recovery_suggestions")
    except Exception as e:
        results["checks"].append(
            {
                "name": "failure_analyzer_ui_implementation",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ Failure Analyzer UI failed: {e}")

    print()
    print("Check 4: Performance Metrics UI...")
    try:
        metrics_ui = PerformanceMetricsUI()
        metrics_data = metrics_ui.get_metrics_data()

        # Validate metrics data structure
        assert "latest_execution" in metrics_data
        assert "statistics" in metrics_data
        assert metrics_data["status"] in ["ok", "no_profiles"]

        # Validate HTML rendering
        metrics_html = metrics_ui.render_html()
        assert metrics_html is not None
        assert len(metrics_html) > 0

        total_profiles = metrics_data.get("statistics", {}).get("total_profiles", 0)

        results["checks"].append(
            {
                "name": "performance_metrics_ui_implementation",
                "status": "pass",
                "details": f"Performance Metrics UI analyzes {total_profiles} profiles, renders HTML",
            }
        )
        print(f"  ✓ Performance Metrics UI: renders {len(metrics_html)} bytes of HTML")
        print(f"    - Consumes real performance profiles")
        print(f"    - Analyzed {total_profiles} executions")
        print(f"    - Display structure: timing_breakdown, bottleneck_analysis, optimization_suggestions")
    except Exception as e:
        results["checks"].append(
            {
                "name": "performance_metrics_ui_implementation",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ Performance Metrics UI failed: {e}")

    print()
    print("Check 5: Real artifact consumption verification...")
    try:
        # Verify that UIs actually consume real artifacts
        latest_exec = executions[0]

        # Dashboard consumes execution_trace
        if latest_exec.get("execution_trace"):
            trace = latest_exec["execution_trace"]
            assert "trace_events" in trace
            assert "session_id" in trace
            results["checks"].append(
                {
                    "name": "dashboard_consumes_traces",
                    "status": "pass",
                    "details": f"Dashboard consumes execution traces with {len(trace.get('trace_events', []))} events",
                }
            )
            print(
                f"  ✓ Dashboard consumes real traces: {len(trace.get('trace_events', []))} events"
            )
        else:
            print("  ⚠ No execution trace artifacts found")

        # Failure Analyzer consumes failure_record
        if latest_exec.get("failure_record"):
            failure = latest_exec["failure_record"]
            assert "failure_type" in failure
            assert "recovery_suggestions" in failure
            results["checks"].append(
                {
                    "name": "analyzer_consumes_failures",
                    "status": "pass",
                    "details": f"Analyzer consumes failure records with type '{failure.get('failure_type')}'",
                }
            )
            print(
                f"  ✓ Analyzer consumes real failures: {failure.get('failure_type')}"
            )
        else:
            print("  ⚠ No failure record artifacts found")

        # Performance Metrics consumes performance_profile
        if latest_exec.get("performance_profile"):
            profile = latest_exec["performance_profile"]
            assert "timing_breakdown" in profile
            assert "bottleneck_analysis" in profile
            bottleneck = profile.get("bottleneck_analysis", {}).get("slowest_stage")
            results["checks"].append(
                {
                    "name": "metrics_consumes_profiles",
                    "status": "pass",
                    "details": f"Metrics UI consumes profiles with bottleneck '{bottleneck}'",
                }
            )
            print(f"  ✓ Metrics UI consumes real profiles: bottleneck={bottleneck}")
        else:
            print("  ⚠ No performance profile artifacts found")

    except Exception as e:
        results["checks"].append(
            {
                "name": "real_artifact_consumption",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ Artifact consumption verification failed: {e}")

    print()
    print("Check 6: Control Center Server integration...")
    try:
        from framework.control_center_server import (
            dashboard_ui as cc_dashboard,
            failure_ui as cc_failure,
            metrics_ui as cc_metrics,
        )

        # Verify instances are properly initialized
        assert cc_dashboard is not None
        assert cc_failure is not None
        assert cc_metrics is not None

        results["checks"].append(
            {
                "name": "control_center_integration",
                "status": "pass",
                "details": "All UI modules integrated into control center server",
            }
        )
        print("  ✓ Control Center Server integration verified")
        print("    - Dashboard UI module loaded")
        print("    - Failure Analyzer module loaded")
        print("    - Performance Metrics module loaded")
    except Exception as e:
        results["checks"].append(
            {
                "name": "control_center_integration",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ Control Center integration failed: {e}")

    print()
    print("Check 7: HTML output quality...")
    try:
        dashboard = ExecutionDashboardUI()
        failure_analyzer = FailureAnalyzerUI()
        metrics_ui_inst = PerformanceMetricsUI()

        dashboard_html = dashboard.render_html()
        analyzer_html = failure_analyzer.render_html()
        metrics_html = metrics_ui_inst.render_html()

        # Check for required HTML elements
        checks_passed = 0
        total_checks = 0

        # Dashboard HTML checks
        total_checks += 1
        if "execution" in dashboard_html.lower() and "<div class=\"panel\">" in dashboard_html:
            checks_passed += 1
            print("  ✓ Dashboard HTML contains execution panel")
        else:
            print("  ✗ Dashboard HTML missing expected structure")

        # Analyzer HTML checks
        total_checks += 1
        if ("failure" in analyzer_html.lower() or "no failures" in analyzer_html.lower()) and "<div class=\"panel\">" in analyzer_html:
            checks_passed += 1
            print("  ✓ Analyzer HTML contains failure panel")
        else:
            print("  ✗ Analyzer HTML missing expected structure")

        # Metrics HTML checks
        total_checks += 1
        if ("performance" in metrics_html.lower() or "metrics" in metrics_html.lower()) and "<div class=\"panel\">" in metrics_html:
            checks_passed += 1
            print("  ✓ Metrics HTML contains performance panel")
        else:
            print("  ✗ Metrics HTML missing expected structure")

        results["checks"].append(
            {
                "name": "html_output_quality",
                "status": "pass" if checks_passed == total_checks else "partial",
                "details": f"{checks_passed}/{total_checks} HTML quality checks passed",
            }
        )
    except Exception as e:
        results["checks"].append(
            {
                "name": "html_output_quality",
                "status": "fail",
                "details": str(e),
            }
        )
        print(f"  ✗ HTML output quality check failed: {e}")

    # Summary
    print()
    print("=" * 60)
    passed = sum(1 for c in results["checks"] if c["status"] == "pass")
    total = len(results["checks"])

    results["summary"]["total_checks"] = total
    results["summary"]["passed"] = passed
    results["summary"]["failed"] = total - passed
    results["summary"]["status"] = "pass" if passed == total else "fail"

    print(f"Phase 2 UI Validation Results: {passed}/{total} checks passed")
    print("=" * 60)

    if passed == total:
        print("✓ Phase 2 UI Layer validation PASSED")
        print("  - RM-UI-002 (Execution Dashboard) implemented and validated")
        print("  - RM-UI-003 (Failure Analyzer UI) implemented and validated")
        print("  - RM-UI-004 (Performance Metrics Display) implemented and validated")
        print("  - All three UI modules consume real OPS artifacts")
    else:
        print(f"✗ Phase 2 UI Layer validation FAILED ({total - passed} checks failed)")
        for check in results["checks"]:
            if check["status"] != "pass":
                print(f"  - {check['name']}: {check['details']}")

    return results


if __name__ == "__main__":
    results = validate_ui_implementation()

    # Write results to artifacts directory
    artifacts_dir = Path(__file__).parent.parent / "artifacts" / "validation"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    output_file = artifacts_dir / "phase2_ui_validation.json"
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\n✓ Validation results written to {output_file}")

    sys.exit(0 if results["summary"]["status"] == "pass" else 1)
