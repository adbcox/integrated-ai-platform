#!/usr/bin/env python3
"""Execution dashboard UI: monitors execution traces and displays session/job linkage."""

from typing import Dict, Any
from framework.ops_artifact_loader import OpsArtifactLoader


class ExecutionDashboardUI:
    """UI for monitoring execution traces and session/job linkage."""

    def __init__(self):
        self.loader = OpsArtifactLoader()

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for the execution dashboard display."""
        executions = self.loader.discover_executions()

        if not executions:
            return {
                "status": "no_executions",
                "message": "No execution traces found",
                "executions": [],
            }

        # Get latest execution details
        latest_exec = executions[0]
        summary = self.loader.get_execution_summary(latest_exec)
        trace = latest_exec.get("execution_trace", {})
        trace_events = self.loader.get_trace_events_display(trace)

        return {
            "status": "ok",
            "execution_count": len(executions),
            "latest_execution": {
                "summary": summary,
                "trace_events": trace_events,
                "total_events": len(trace_events),
            },
            "all_executions": [
                {
                    "workspace_id": ex["workspace_id"],
                    "summary": self.loader.get_execution_summary(ex),
                }
                for ex in executions[:10]  # Last 10 executions
            ],
        }

    def render_html(self) -> str:
        """Render execution dashboard as HTML."""
        data = self.get_dashboard_data()

        if data["status"] == "no_executions":
            return """
            <div class="panel">
                <h2>📊 Execution Dashboard</h2>
                <p style="color: #999;">No execution traces found yet.</p>
            </div>
            """

        latest = data["latest_execution"]
        summary = latest["summary"]
        events = latest["trace_events"]

        # Build stage summary
        stages_html = ""
        for stage_name, stage_info in summary["stages"].items():
            status_color = (
                "#10b981"
                if stage_info["status"] == "complete"
                else "#ef4444"
                if stage_info["status"] == "failed"
                else "#999"
            )
            stages_html += f"""
            <div class="stage-card">
                <div class="stage-name">{stage_name.replace('_', ' ').title()}</div>
                <div class="stage-duration">{stage_info['duration_seconds']:.3f}s</div>
                <div class="stage-status" style="color: {status_color};">●</div>
            </div>
            """

        # Build event timeline
        timeline_html = ""
        for event in events[-15:]:  # Last 15 events
            event_color = "#667eea" if "command" in event["event_type"] else "#999"
            timeline_html += f"""
            <div class="timeline-event">
                <span style="color: {event_color}; font-weight: 600;">{event['event_type']}</span>
                <span>{event['stage']}</span>
                <span style="font-family: monospace; color: #999;">{event['duration_ms']}ms</span>
            </div>
            """

        return f"""
        <div class="panel">
            <h2>📊 Execution Dashboard</h2>
            <div class="execution-header">
                <div class="header-item">
                    <div class="header-label">Session</div>
                    <div class="header-value" style="font-family: monospace; font-size: 0.9rem;">{summary['session_id'][:12]}...</div>
                </div>
                <div class="header-item">
                    <div class="header-label">Duration</div>
                    <div class="header-value">{summary['total_duration_seconds']:.3f}s</div>
                </div>
                <div class="header-item">
                    <div class="header-label">Stages</div>
                    <div class="header-value">{summary['stage_count']}</div>
                </div>
                <div class="header-item">
                    <div class="header-label">Status</div>
                    <div class="header-value">{'✓ Complete' if not summary['has_failure'] else '✗ Failed'}</div>
                </div>
            </div>

            <div class="stages-grid">
                {stages_html}
            </div>

            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; font-size: 1rem; margin-bottom: 10px;">Event Timeline</h3>
                <div class="timeline">
                    {timeline_html}
                </div>
            </div>

            <div style="margin-top: 10px; padding: 10px; background: #f3f4f6; border-radius: 4px; font-size: 0.9rem; color: #666;">
                Total events: {latest['total_events']} | Objective: {summary.get('objective', 'N/A')[:60]}...
            </div>
        </div>
        """
