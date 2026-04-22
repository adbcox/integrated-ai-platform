#!/usr/bin/env python3
"""Performance metrics UI: displays timing graphs, bottleneck analysis, and optimization suggestions."""

from typing import Dict, Any
from framework.ops_artifact_loader import OpsArtifactLoader


class PerformanceMetricsUI:
    """UI for displaying performance metrics, bottlenecks, and optimization suggestions."""

    def __init__(self):
        self.loader = OpsArtifactLoader()

    def get_metrics_data(self) -> Dict[str, Any]:
        """Get data for the performance metrics display."""
        executions = self.loader.discover_executions()

        # Find executions with performance profiles
        profiled_executions = [
            ex for ex in executions if ex.get("performance_profile") is not None
        ]

        if not profiled_executions:
            return {
                "status": "no_profiles",
                "message": "No performance profiles found",
                "executions": [],
            }

        # Analyze latest profile
        latest_exec = profiled_executions[0]
        profile = latest_exec.get("performance_profile", {})
        perf_details = self.loader.get_performance_details(profile)
        summary = self.loader.get_execution_summary(latest_exec)

        # Calculate statistics across all profiles
        all_durations = []
        stage_stats = {}

        for ex in profiled_executions:
            profile = ex.get("performance_profile", {})
            if profile:
                total_duration = profile.get("timing_breakdown", {}).get(
                    "total_duration_seconds", 0
                )
                all_durations.append(total_duration)

                for stage_name, duration in (
                    profile.get("timing_breakdown", {}).get("stages", {}).items()
                ):
                    if stage_name not in stage_stats:
                        stage_stats[stage_name] = {"durations": [], "count": 0}
                    stage_stats[stage_name]["durations"].append(duration)
                    stage_stats[stage_name]["count"] += 1

        # Calculate averages
        avg_duration = (
            sum(all_durations) / len(all_durations) if all_durations else 0
        )
        stage_averages = {
            stage: {
                "avg_duration": sum(stats["durations"]) / stats["count"],
                "count": stats["count"],
            }
            for stage, stats in stage_stats.items()
        }

        return {
            "status": "ok",
            "latest_execution": {
                "summary": summary,
                "performance": perf_details,
            },
            "statistics": {
                "total_profiles": len(profiled_executions),
                "avg_duration_seconds": round(avg_duration, 3),
                "latest_duration_seconds": perf_details.get("total_duration_ms", 0) / 1000,
                "stage_averages": {
                    stage: round(stats["avg_duration"], 3)
                    for stage, stats in stage_averages.items()
                },
            },
        }

    def render_html(self) -> str:
        """Render performance metrics as HTML."""
        data = self.get_metrics_data()

        if data["status"] == "no_profiles":
            return """
            <div class="panel">
                <h2>⚡ Performance Metrics</h2>
                <p style="color: #999;">No performance profiles found yet.</p>
            </div>
            """

        latest = data["latest_execution"]
        perf = latest["performance"]
        stats = data["statistics"]

        # Build stage timing display
        stages_html = ""
        stages = perf.get("stages", {})
        total_ms = perf.get("total_duration_ms", 1)  # Avoid division by zero

        for stage_name, duration_ms in sorted(
            stages.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (duration_ms / total_ms * 100) if total_ms > 0 else 0
            bar_width = percentage * 2  # Scale for visibility

            stages_html += f"""
            <div class="stage-timing">
                <div class="stage-label">{stage_name.replace('_', ' ').title()}</div>
                <div class="stage-bar-container">
                    <div class="stage-bar" style="width: {min(bar_width, 200)}px; background: #667eea;"></div>
                </div>
                <div class="stage-value">{duration_ms}ms ({percentage:.1f}%)</div>
            </div>
            """

        # Build optimization suggestions
        suggestions_html = ""
        for suggestion in perf.get("optimization_suggestions", []):
            suggestions_html += f"""
            <div class="suggestion-item">
                <div class="suggestion-text">{suggestion.get('suggestion', '')}</div>
                <div class="suggestion-impact">Potential impact: {suggestion.get('potential_impact', '')}</div>
            </div>
            """

        # Build stage averages table
        averages_html = ""
        for stage_name, avg_duration in sorted(
            stats.get("stage_averages", {}).items(), key=lambda x: x[1], reverse=True
        ):
            averages_html += f"""
            <tr>
                <td>{stage_name.replace('_', ' ').title()}</td>
                <td style="text-align: right; font-family: monospace;">{avg_duration * 1000:.1f}ms</td>
            </tr>
            """

        return f"""
        <div class="panel">
            <h2>⚡ Performance Metrics</h2>

            <div class="metrics-header">
                <div class="metric-box">
                    <div class="metric-label">Latest Duration</div>
                    <div class="metric-value">{perf.get('total_duration_ms', 0)}ms</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Average Duration</div>
                    <div class="metric-value">{int(stats.get("avg_duration_seconds", 0) * 1000)}ms</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Bottleneck</div>
                    <div class="metric-value">{perf.get('slowest_stage', 'N/A').replace('_', ' ').title()}</div>
                </div>
                <div class="metric-box">
                    <div class="metric-label">Bottleneck Impact</div>
                    <div class="metric-value">{perf.get('bottleneck_percentage', 0):.1f}%</div>
                </div>
            </div>

            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; font-size: 1rem; margin-bottom: 12px;">Execution Timing Breakdown</h3>
                <div class="timing-chart">
                    {stages_html}
                </div>
            </div>

            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; font-size: 1rem; margin-bottom: 12px;">Average Stage Durations</h3>
                <table class="metrics-table">
                    <thead>
                        <tr>
                            <th>Stage</th>
                            <th>Average Duration</th>
                        </tr>
                    </thead>
                    <tbody>
                        {averages_html}
                    </tbody>
                </table>
            </div>

            <div style="margin-top: 20px;">
                <h3 style="color: #667eea; font-size: 1rem; margin-bottom: 12px;">Optimization Suggestions</h3>
                <div class="suggestions-list">
                    {suggestions_html if suggestions_html else '<div style="color: #999;">No optimization suggestions</div>'}
                </div>
            </div>
        </div>
        """
