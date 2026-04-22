#!/usr/bin/env python3
"""Simple HTTP control center server using stdlib."""

import json
import sys
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import urlparse
from framework.ops_artifact_loader import OpsArtifactLoader
from framework.execution_dashboard_ui import ExecutionDashboardUI
from framework.failure_analyzer_ui import FailureAnalyzerUI
from framework.performance_metrics_ui import PerformanceMetricsUI

ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts" / "integration_demo"

# Initialize OPS UI modules
ops_loader = OpsArtifactLoader()
dashboard_ui = ExecutionDashboardUI()
failure_ui = FailureAnalyzerUI()
metrics_ui = PerformanceMetricsUI()


def load_artifact(filename: str) -> dict:
    """Load and return artifact JSON."""
    artifact_path = ARTIFACTS_DIR / filename
    if artifact_path.exists():
        return json.loads(artifact_path.read_text())
    return {}


class ControlCenterHandler(BaseHTTPRequestHandler):
    """HTTP request handler for control center."""

    def do_GET(self):
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index":
            self.serve_dashboard()
        elif path == "/api/status":
            self.serve_json(self.get_status())
        elif path == "/api/hardware":
            self.serve_json(load_artifact("01_hardware_design.json"))
        elif path == "/api/procurement":
            self.serve_json(load_artifact("02_procurement_evaluation.json"))
        elif path == "/api/editions":
            self.serve_json(load_artifact("03_editions_resolved.json"))
        elif path == "/api/website":
            self.serve_json(load_artifact("04_website_generated.json"))
        elif path == "/api/summary":
            self.serve_json(load_artifact("INTEGRATION_SUMMARY.json"))
        elif path == "/api/ops/executions":
            self.serve_json({"executions": ops_loader.discover_executions()})
        elif path == "/api/ops/dashboard":
            self.serve_json(dashboard_ui.get_dashboard_data())
        elif path == "/api/ops/failures":
            self.serve_json(failure_ui.get_analyzer_data())
        elif path == "/api/ops/metrics":
            self.serve_json(metrics_ui.get_metrics_data())
        else:
            self.send_error(404)

    def serve_json(self, data: dict):
        """Send JSON response."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, default=str).encode())

    def serve_dashboard(self):
        """Serve HTML dashboard."""
        hardware = load_artifact("01_hardware_design.json")
        procurement = load_artifact("02_procurement_evaluation.json")
        editions = load_artifact("03_editions_resolved.json")
        website = load_artifact("04_website_generated.json")

        # Get OPS UI HTML
        dashboard_html = dashboard_ui.render_html()
        failure_html = failure_ui.render_html()
        metrics_html = metrics_ui.render_html()

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Master Control Center - Integration Phase 1 + OPS Layer</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 1600px; margin: 0 auto; }}
        header {{ background: white; border-radius: 8px; padding: 30px; margin-bottom: 20px;
                  box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        header h1 {{ color: #667eea; margin-bottom: 10px; }}
        .section-title {{ color: white; font-size: 1.1rem; font-weight: 600; margin: 30px 0 15px 0;
                         padding-bottom: 10px; border-bottom: 2px solid rgba(255,255,255,0.3); }}
        .panels-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                       gap: 20px; margin-bottom: 20px; }}
        .panel {{ background: white; border-radius: 8px; padding: 24px;
                 box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .panel h2 {{ color: #667eea; margin-bottom: 16px; font-size: 1.3rem;
                    border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
        .metric {{ display: flex; justify-content: space-between; padding: 10px 0;
                  border-bottom: 1px solid #eee; }}
        .metric-label {{ font-weight: 500; color: #555; }}
        .metric-value {{ color: #667eea; font-weight: 600; font-family: 'Monaco', monospace; }}
        .cost-metric {{ color: #10b981; font-size: 1.2rem; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 20px;
                        font-size: 0.85rem; font-weight: 600; background: #dcfce7;
                        color: #166534; margin: 4px 0; }}

        /* OPS UI Styles */
        .execution-header {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .header-item {{ background: #f3f4f6; padding: 15px; border-radius: 6px; }}
        .header-label {{ font-size: 0.85rem; color: #999; font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }}
        .header-value {{ font-size: 1.2rem; color: #667eea; font-weight: 600; }}

        .stages-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; margin: 15px 0; }}
        .stage-card {{ background: #f3f4f6; padding: 12px; border-radius: 6px; text-align: center; }}
        .stage-name {{ font-size: 0.8rem; color: #555; font-weight: 500; }}
        .stage-duration {{ font-size: 1rem; color: #667eea; font-weight: 600; margin: 5px 0; }}
        .stage-status {{ font-size: 1.2rem; margin-top: 3px; }}

        .timeline {{ background: #f9fafb; border-left: 3px solid #667eea; padding: 15px; border-radius: 4px; max-height: 300px; overflow-y: auto; }}
        .timeline-event {{ padding: 8px 0; border-bottom: 1px solid #eee; font-size: 0.9rem; display: flex; gap: 12px; }}

        .failure-stats {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }}
        .stat {{ background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center; }}
        .stat-label {{ font-size: 0.85rem; color: #999; font-weight: 600; }}
        .stat-value {{ font-size: 1.5rem; color: #667eea; font-weight: 600; margin-top: 8px; }}

        .failure-card {{ background: #f9fafb; border-left: 3px solid #ef4444; padding: 15px; border-radius: 6px; margin-bottom: 12px; }}
        .failure-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
        .failure-type {{ font-weight: 600; color: #ef4444; font-size: 0.95rem; }}
        .failure-time {{ font-size: 0.85rem; color: #999; }}
        .failure-body {{ margin: 10px 0; }}
        .failure-detail {{ display: flex; gap: 10px; margin-bottom: 8px; font-size: 0.9rem; }}
        .detail-label {{ font-weight: 600; color: #555; min-width: 100px; }}
        .detail-value {{ color: #666; }}
        .recovery-list {{ margin-top: 10px; }}
        .recovery-suggestion {{ background: #f0f9ff; border-left: 2px solid #0ea5e9; padding: 10px; margin: 8px 0; border-radius: 4px; }}
        .recovery-action {{ font-weight: 600; color: #0284c7; font-size: 0.9rem; }}
        .recovery-reason {{ font-size: 0.85rem; color: #666; margin-top: 3px; }}

        .metrics-header {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }}
        .metric-box {{ background: #f3f4f6; padding: 15px; border-radius: 6px; text-align: center; }}
        .metric-label {{ font-size: 0.85rem; color: #999; font-weight: 600; }}
        .metric-value {{ font-size: 1.3rem; color: #667eea; font-weight: 600; margin-top: 8px; }}

        .timing-chart {{ background: #f9fafb; padding: 15px; border-radius: 6px; }}
        .stage-timing {{ display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }}
        .stage-label {{ min-width: 140px; font-size: 0.9rem; font-weight: 500; color: #555; }}
        .stage-bar-container {{ flex: 1; height: 24px; background: #e5e7eb; border-radius: 4px; }}
        .stage-bar {{ height: 100%; border-radius: 4px; }}
        .stage-value {{ min-width: 80px; text-align: right; font-size: 0.9rem; color: #667eea; font-weight: 600; font-family: monospace; }}

        .suggestions-list {{ background: #f9fafb; padding: 15px; border-radius: 6px; }}
        .suggestion-item {{ margin-bottom: 12px; padding: 12px; background: white; border-radius: 4px; }}
        .suggestion-text {{ font-weight: 600; color: #555; margin-bottom: 4px; }}
        .suggestion-impact {{ font-size: 0.85rem; color: #999; }}

        .metrics-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
        .metrics-table thead {{ background: #f3f4f6; }}
        .metrics-table th {{ padding: 10px; text-align: left; font-weight: 600; color: #555; border-bottom: 2px solid #e5e7eb; }}
        .metrics-table td {{ padding: 10px; border-bottom: 1px solid #e5e7eb; }}

        .footer {{ background: white; border-radius: 8px; padding: 20px; text-align: center; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎛️ Master Control Center</h1>
            <p>Integration Phase 1 + Phase 2 Operations Layer (Real-Time System Status)</p>
        </header>

        <div class="section-title">Integration Phase 1 - System Components</div>
        <div class="panels-grid">
            <div class="panel">
                <h2>⚙️ Hardware Design</h2>
                <div class="status-badge">✓ Generated</div>
                {"<div class='metric'><span class='metric-label'>Project</span><span class='metric-value'>" + hardware.get("project_id", "N/A") + "</span></div>" if hardware else "<p>Artifacts not found</p>"}
                {"<div class='metric'><span class='metric-label'>Total Cost</span><span class='metric-value cost-metric'>$" + str(hardware.get("bom", {}).get("total_cost", 0)) + "</span></div>" if hardware else ""}
            </div>

            <div class="panel">
                <h2>📦 Procurement</h2>
                <div class="status-badge">✓ Evaluated</div>
                {"<div class='metric'><span class='metric-label'>Parts</span><span class='metric-value'>" + str(len(procurement.get("procurement_decisions", []))) + "</span></div>" if procurement else "<p>Artifacts not found</p>"}
                {"<div class='metric'><span class='metric-label'>Cost</span><span class='metric-value cost-metric'>$" + str(procurement.get("summary", {}).get("total_procurement_cost", 0)) + "</span></div>" if procurement else ""}
            </div>

            <div class="panel">
                <h2>📋 Editions</h2>
                <div class="status-badge">✓ Resolved</div>
                {"<div class='metric'><span class='metric-label'>Editions</span><span class='metric-value'>" + str(len(editions.get("editions", []))) + "</span></div>" if editions else "<p>Artifacts not found</p>"}
                {"<div class='metric'><span class='metric-label'>Platforms</span><span class='metric-value'>" + ", ".join([e["edition"]["target_platform"].title() for e in editions.get("editions", [])]) + "</span></div>" if editions else ""}
            </div>

            <div class="panel">
                <h2>🌐 Website</h2>
                <div class="status-badge">✓ Generated</div>
                {"<div class='metric'><span class='metric-label'>Pages</span><span class='metric-value'>" + str(len(website.get("generated_pages", []))) + "</span></div>" if website else "<p>Artifacts not found</p>"}
            </div>
        </div>

        <div class="section-title">Phase 2 Operations Layer - Real-Time Monitoring</div>
        <div class="panels-grid" style="grid-template-columns: 1fr; gap: 20px;">
            {dashboard_html}
        </div>

        <div class="panels-grid" style="grid-template-columns: 1fr 1fr; gap: 20px;">
            {failure_html}
            {metrics_html}
        </div>

        <div class="footer">
            <p>All systems operational • Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
    </div>
</body>
</html>"""

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def get_status(self) -> dict:
        """Get system status."""
        hardware = load_artifact("01_hardware_design.json")
        procurement = load_artifact("02_procurement_evaluation.json")
        editions = load_artifact("03_editions_resolved.json")
        website = load_artifact("04_website_generated.json")

        return {
            "hardware": "ready" if hardware else "missing",
            "procurement": "ready" if procurement else "missing",
            "editions": "ready" if editions else "missing",
            "website": "ready" if website else "missing",
            "chain_complete": all([hardware, procurement, editions, website]),
            "timestamp": datetime.now().isoformat(),
        }

    def log_message(self, format, *args):
        """Suppress request logs."""
        pass


def run_server(port=5000):
    """Run the control center server."""
    server = HTTPServer(("0.0.0.0", port), ControlCenterHandler)
    print(f"✓ Control Center running on http://localhost:{port}")
    print(f"✓ Available endpoints:")
    print(f"  - http://localhost:{port}/ (Integrated Dashboard)")
    print(f"  - http://localhost:{port}/api/status")
    print(f"  Integration Phase 1:")
    print(f"  - http://localhost:{port}/api/hardware")
    print(f"  - http://localhost:{port}/api/procurement")
    print(f"  - http://localhost:{port}/api/editions")
    print(f"  - http://localhost:{port}/api/website")
    print(f"  - http://localhost:{port}/api/summary")
    print(f"  Phase 2 Operations Layer:")
    print(f"  - http://localhost:{port}/api/ops/executions (List all executions)")
    print(f"  - http://localhost:{port}/api/ops/dashboard (Execution traces)")
    print(f"  - http://localhost:{port}/api/ops/failures (Failure analysis)")
    print(f"  - http://localhost:{port}/api/ops/metrics (Performance metrics)")
    print(f"\nPress Ctrl+C to stop server")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        sys.exit(0)


if __name__ == "__main__":
    run_server()
