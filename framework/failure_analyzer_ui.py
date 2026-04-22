#!/usr/bin/env python3
"""Failure analyzer UI: displays failure classification and recovery suggestions."""

from typing import Dict, Any, List
from framework.ops_artifact_loader import OpsArtifactLoader


class FailureAnalyzerUI:
    """UI for analyzing failures and displaying recovery suggestions."""

    def __init__(self):
        self.loader = OpsArtifactLoader()

    def get_analyzer_data(self) -> Dict[str, Any]:
        """Get data for the failure analyzer display."""
        executions = self.loader.discover_executions()

        # Find executions with failures
        failed_executions = [
            ex for ex in executions if ex.get("failure_record") is not None
        ]

        if not failed_executions:
            return {
                "status": "no_failures",
                "message": "No failures recorded",
                "total_executions": len(executions),
                "failures": [],
            }

        failures = []
        for ex in failed_executions:
            failure = ex.get("failure_record", {})
            trace = ex.get("execution_trace", {})

            failure_details = {
                "workspace_id": ex["workspace_id"],
                "summary": self.loader.get_execution_summary(ex),
                "failure": self.loader.get_failure_details(failure),
                "trace_events": self.loader.get_trace_events_display(trace),
            }
            failures.append(failure_details)

        return {
            "status": "ok",
            "total_executions": len(executions),
            "total_failures": len(failed_executions),
            "failure_rate": round((len(failed_executions) / len(executions) * 100), 1)
            if executions
            else 0,
            "failures": failures,
        }

    def _get_failure_type_description(self, failure_type: str) -> str:
        """Get human-readable description for failure type."""
        descriptions = {
            "command_not_allowed": "Command is not in whitelist",
            "command_failed": "Command execution failed",
            "command_timeout": "Command exceeded timeout",
            "workspace_init_failed": "Workspace initialization failed",
            "profile_selection_failed": "Profile selection failed",
            "artifact_emission_failed": "Artifact emission failed",
            "workspace_finalize_failed": "Workspace finalization failed",
            "gateway_error": "Gateway/inference error",
            "unknown_error": "Unknown error",
        }
        return descriptions.get(failure_type, failure_type)

    def render_html(self) -> str:
        """Render failure analyzer as HTML."""
        data = self.get_analyzer_data()

        if data["status"] == "no_failures":
            return f"""
            <div class="panel">
                <h2>🔍 Failure Analyzer</h2>
                <div style="padding: 20px; text-align: center; color: #999;">
                    <p style="font-size: 2rem; margin-bottom: 10px;">✓</p>
                    <p>No failures recorded</p>
                    <p style="font-size: 0.9rem; color: #bbb; margin-top: 10px;">
                        Total executions analyzed: {data['total_executions']}
                    </p>
                </div>
            </div>
            """

        failures_html = ""
        for idx, failure_item in enumerate(data["failures"][:5]):  # Show last 5 failures
            failure = failure_item["failure"]
            summary = failure_item["summary"]

            recovery_html = ""
            for suggestion in failure.get("recovery_suggestions", []):
                recovery_html += f"""
                <div class="recovery-suggestion">
                    <div class="recovery-action">{suggestion.get('action', 'unknown').replace('_', ' ').title()}</div>
                    <div class="recovery-reason">{suggestion.get('reason', '')}</div>
                </div>
                """

            command_str = " ".join(failure.get("command", []))[:80]

            failures_html += f"""
            <div class="failure-card">
                <div class="failure-header">
                    <span class="failure-type">{self._get_failure_type_description(failure.get('failure_type', 'unknown'))}</span>
                    <span class="failure-time">{summary.get('created_at', 'N/A')[-8:]}</span>
                </div>
                <div class="failure-body">
                    <div class="failure-detail">
                        <span class="detail-label">Root Cause:</span>
                        <span class="detail-value">{failure.get('root_cause', 'N/A')}</span>
                    </div>
                    <div class="failure-detail">
                        <span class="detail-label">Command:</span>
                        <span class="detail-value" style="font-family: monospace; font-size: 0.85rem;">{command_str}</span>
                    </div>
                    {f'<div class="failure-detail"><span class="detail-label">Exit Code:</span><span class="detail-value">{failure.get("exit_code", "N/A")}</span></div>' if failure.get('exit_code') else ''}
                </div>
                <div class="recovery-list">
                    <div style="font-weight: 600; color: #667eea; margin-bottom: 8px; font-size: 0.9rem;">Recovery Suggestions:</div>
                    {recovery_html if recovery_html else '<div style="color: #999;">No suggestions available</div>'}
                </div>
            </div>
            """

        return f"""
        <div class="panel">
            <h2>🔍 Failure Analyzer</h2>
            <div class="failure-stats">
                <div class="stat">
                    <div class="stat-label">Total Executions</div>
                    <div class="stat-value">{data['total_executions']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Failures</div>
                    <div class="stat-value">{data['total_failures']}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Failure Rate</div>
                    <div class="stat-value">{data['failure_rate']}%</div>
                </div>
            </div>

            <div style="margin-top: 20px;">
                {failures_html}
            </div>
        </div>
        """
