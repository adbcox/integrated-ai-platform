#!/usr/bin/env python3
"""Flask control center web application."""

import json
from pathlib import Path
from flask import Flask, render_template_string, jsonify
from datetime import datetime

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Load integration artifacts
ARTIFACTS_DIR = Path(__file__).parent.parent / "artifacts" / "integration_demo"


def load_artifact(filename: str) -> dict:
    """Load and return artifact JSON."""
    artifact_path = ARTIFACTS_DIR / filename
    if artifact_path.exists():
        return json.loads(artifact_path.read_text())
    return {}


# HTML template for control center
CONTROL_CENTER_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Master Control Center - Integration Phase 1</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            background: white;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 {
            color: #667eea;
            margin-bottom: 10px;
        }
        header p {
            color: #666;
            font-size: 0.95rem;
        }
        .panels-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .panel {
            background: white;
            border-radius: 8px;
            padding: 24px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .panel:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 12px rgba(0,0,0,0.15);
        }
        .panel h2 {
            color: #667eea;
            margin-bottom: 16px;
            font-size: 1.3rem;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .panel h3 {
            color: #333;
            margin-top: 16px;
            margin-bottom: 8px;
            font-size: 1rem;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .metric:last-child {
            border-bottom: none;
        }
        .metric-label {
            font-weight: 500;
            color: #555;
        }
        .metric-value {
            color: #667eea;
            font-weight: 600;
            font-family: 'Monaco', monospace;
        }
        .cost-metric {
            color: #10b981;
            font-size: 1.2rem;
        }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            background: #dbeafe;
            color: #0369a1;
            margin: 4px 0;
        }
        .status-badge.success {
            background: #dcfce7;
            color: #166534;
        }
        .list-item {
            padding: 8px 0;
            color: #555;
            border-bottom: 1px solid #f0f0f0;
        }
        .list-item:last-child {
            border-bottom: none;
        }
        .feature-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        .feature-tag {
            background: #f0f4ff;
            color: #667eea;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85rem;
            border: 1px solid #d9e5ff;
        }
        .footer {
            background: white;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }
        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .spinner {
            display: inline-block;
            width: 16px;
            height: 16px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎛️ Master Control Center</h1>
            <p>Integration Phase 1 - Real-Time System Status Dashboard</p>
        </header>

        <!-- Hardware Design Panel -->
        <div class="panels-grid">
            <div class="panel">
                <h2>⚙️ Hardware Design</h2>
                {% if hardware %}
                    <div class="status-badge success">✓ Generated</div>
                    <div class="metric">
                        <span class="metric-label">Project</span>
                        <span class="metric-value">{{ hardware.project_id }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Platform</span>
                        <span class="metric-value">{{ hardware.hardware_project.target_platform }}</span>
                    </div>
                    <h3>BOM Summary</h3>
                    <div class="metric">
                        <span class="metric-label">Components</span>
                        <span class="metric-value">{{ hardware.bom.components|length }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Cost</span>
                        <span class="metric-value cost-metric">${{ hardware.bom.total_cost }}</span>
                    </div>
                {% else %}
                    <div class="error">Artifacts not found</div>
                {% endif %}
            </div>

            <!-- Procurement Panel -->
            <div class="panel">
                <h2>📦 Procurement</h2>
                {% if procurement %}
                    <div class="status-badge success">✓ Evaluated</div>
                    <h3>Evaluation Summary</h3>
                    <div class="metric">
                        <span class="metric-label">Parts Evaluated</span>
                        <span class="metric-value">{{ procurement.summary.total_parts }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Cost (BOM)</span>
                        <span class="metric-value cost-metric">${{ procurement.summary.total_bom_cost }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Procurement Cost</span>
                        <span class="metric-value cost-metric">${{ procurement.summary.total_procurement_cost }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Avg Lead Time</span>
                        <span class="metric-value">{{ procurement.summary.average_lead_time }} days</span>
                    </div>
                {% else %}
                    <div class="error">Artifacts not found</div>
                {% endif %}
            </div>

            <!-- Edition Panel -->
            <div class="panel">
                <h2>📋 Editions</h2>
                {% if editions %}
                    <div class="status-badge success">✓ Resolved</div>
                    <h3>Available Editions</h3>
                    {% for edition_data in editions.editions %}
                        <div class="list-item">
                            <strong>{{ edition_data.edition.name }}</strong><br>
                            <small style="color: #999;">{{ edition_data.edition.target_platform|title }}</small>
                        </div>
                    {% endfor %}
                    <h3 style="margin-top: 20px;">Features by Edition</h3>
                    {% for edition_data in editions.editions %}
                        <div style="margin: 10px 0;">
                            <strong style="color: #667eea;">{{ edition_data.edition.target_platform|title }}</strong>
                            <div class="feature-list">
                                {% for feature in edition_data.edition.feature_set %}
                                    <span class="feature-tag">{{ feature }}</span>
                                {% endfor %}
                            </div>
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="error">Artifacts not found</div>
                {% endif %}
            </div>

            <!-- Website Panel -->
            <div class="panel">
                <h2>🌐 Website</h2>
                {% if website %}
                    <div class="status-badge success">✓ Generated</div>
                    <h3>Generated Pages</h3>
                    <div class="metric">
                        <span class="metric-label">Pages</span>
                        <span class="metric-value">{{ website.generated_pages|length }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Sitemap</span>
                        <span class="metric-value">✓ sitemap.xml</span>
                    </div>
                    <h3>Page List</h3>
                    {% for page in website.generated_pages %}
                        <div class="list-item">
                            📄 {{ page.title|default(page.path.split('/')[-1]) }}
                        </div>
                    {% endfor %}
                {% else %}
                    <div class="error">Artifacts not found</div>
                {% endif %}
            </div>

            <!-- Integration Summary Panel -->
            <div class="panel">
                <h2>✅ Integration Status</h2>
                {% if summary %}
                    <div class="status-badge success">✓ Complete</div>
                    <h3>Chain Status</h3>
                    <div class="metric">
                        <span class="metric-label">Pipeline Stages</span>
                        <span class="metric-value">{{ summary.total_stages }}/{{ summary.total_stages }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Successful</span>
                        <span class="metric-value">{{ summary.successful_stages }}/{{ summary.total_stages }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Total Cost</span>
                        <span class="metric-value cost-metric">${{ summary.total_cost }}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Editions</span>
                        <span class="metric-value">{{ summary.editions_available }}</span>
                    </div>
                    <h3>Data Flow</h3>
                    {% for step in summary.hardware_to_website_flow %}
                        <div class="list-item">✓ {{ step }}</div>
                    {% endfor %}
                {% else %}
                    <div class="error">Summary not found</div>
                {% endif %}
            </div>

            <!-- API Panel -->
            <div class="panel">
                <h2>📡 API Endpoints</h2>
                <div class="list-item">📍 /api/hardware</div>
                <div class="list-item">📍 /api/procurement</div>
                <div class="list-item">📍 /api/editions</div>
                <div class="list-item">📍 /api/website</div>
                <div class="list-item">📍 /api/summary</div>
                <div class="list-item">📍 /api/status</div>
            </div>
        </div>

        <div class="footer">
            <p>Integration Phase 1 - Real-Time Control Center</p>
            <p>All systems operational • Last updated: {{ timestamp }}</p>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
    """Main control center dashboard."""
    hardware = load_artifact("01_hardware_design.json")
    procurement = load_artifact("02_procurement_evaluation.json")
    editions = load_artifact("03_editions_resolved.json")
    website = load_artifact("04_website_generated.json")

    summary = {}
    if all([hardware, procurement, editions, website]):
        summary = {
            "total_stages": 4,
            "successful_stages": 4,
            "hardware_to_website_flow": [
                "Hardware design (BOM)",
                "Procurement evaluation",
                "Edition resolution",
                "Website generation",
            ],
            "total_cost": procurement.get("summary", {}).get("total_procurement_cost", 0),
            "editions_available": len(editions.get("editions", [])),
        }

    return render_template_string(
        CONTROL_CENTER_TEMPLATE,
        hardware=hardware,
        procurement=procurement,
        editions=editions,
        website=website,
        summary=summary,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )


@app.route("/api/status")
def api_status():
    """API endpoint for system status."""
    hardware = load_artifact("01_hardware_design.json")
    procurement = load_artifact("02_procurement_evaluation.json")
    editions = load_artifact("03_editions_resolved.json")
    website = load_artifact("04_website_generated.json")

    return jsonify({
        "hardware": "ready" if hardware else "missing",
        "procurement": "ready" if procurement else "missing",
        "editions": "ready" if editions else "missing",
        "website": "ready" if website else "missing",
        "timestamp": datetime.now().isoformat(),
    })


@app.route("/api/hardware")
def api_hardware():
    """API endpoint for hardware design data."""
    return jsonify(load_artifact("01_hardware_design.json"))


@app.route("/api/procurement")
def api_procurement():
    """API endpoint for procurement data."""
    return jsonify(load_artifact("02_procurement_evaluation.json"))


@app.route("/api/editions")
def api_editions():
    """API endpoint for editions data."""
    return jsonify(load_artifact("03_editions_resolved.json"))


@app.route("/api/website")
def api_website():
    """API endpoint for website data."""
    return jsonify(load_artifact("04_website_generated.json"))


@app.route("/api/summary")
def api_summary():
    """API endpoint for integration summary."""
    return jsonify(load_artifact("INTEGRATION_SUMMARY.json"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
