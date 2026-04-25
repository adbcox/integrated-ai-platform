#!/usr/bin/env python3
"""Prometheus metrics HTTP server for the integrated-AI-platform.

Exposes /metrics on port 8080 (default) in Prometheus text format so that
vmagent can scrape it and push to VictoriaMetrics.

Usage:
    python3 bin/metrics_server.py            # port 8080
    python3 bin/metrics_server.py --port 9091

Endpoints:
    GET /metrics   — Prometheus text exposition
    GET /health    — {"status": "ok", "metrics": N}
    GET /          — Human-readable status page
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

# Allow running from repo root or bin/
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from framework.metrics_system import MetricsRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [metrics-server] %(levelname)s %(message)s",
)
log = logging.getLogger(__name__)

_START_TIME = time.time()


class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: object) -> None:  # silence access log spam
        if self.path == "/metrics":
            return
        log.info(fmt, *args)

    def do_GET(self) -> None:
        path = self.path.split("?")[0]
        if path == "/metrics":
            self._serve_metrics()
        elif path == "/health":
            self._serve_health()
        else:
            self._serve_index()

    def _serve_metrics(self) -> None:
        body = MetricsRegistry.instance().to_prometheus_text().encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_health(self) -> None:
        reg = MetricsRegistry.instance()
        payload = json.dumps({
            "status": "ok",
            "uptime_seconds": round(time.time() - _START_TIME, 1),
            "metrics": len(reg.get_all()),
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _serve_index(self) -> None:
        reg = MetricsRegistry.instance()
        rows = "".join(
            f"<tr><td>{name}</td><td>{type(m).__name__}</td>"
            f"<td>{m.get():.4g}</td></tr>"
            for name, m in sorted(reg.get_all().items())
        )
        body = f"""<!DOCTYPE html>
<html><head><title>IAP Metrics</title></head><body>
<h1>Integrated AI Platform — Metrics</h1>
<p>Uptime: {round(time.time() - _START_TIME)}s &nbsp;|&nbsp;
   <a href="/metrics">/metrics</a> &nbsp;|&nbsp;
   <a href="/health">/health</a></p>
<table border=1 cellpadding=4>
<tr><th>Name</th><th>Type</th><th>Value</th></tr>
{rows}
</table></body></html>""".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    parser = argparse.ArgumentParser(description="Prometheus metrics server")
    parser.add_argument("--port", type=int, default=int(os.getenv("METRICS_PORT", "8080")))
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    # Seed demo metrics so the /metrics endpoint is never empty on first scrape
    _register_demo_metrics()

    server = HTTPServer((args.host, args.port), MetricsHandler)
    log.info("Metrics server listening on %s:%s", args.host, args.port)
    log.info("Endpoints: /metrics  /health  /")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Shutting down")


def _register_demo_metrics() -> None:
    """Pre-register all platform metric names so they appear in /metrics from boot."""
    from framework.platform_metrics import (  # noqa: PLC0415
        record_aider_task, record_executor_task,
        record_pipeline_stage, record_rag_hit,
        record_learning_event, task_started, task_finished,
    )
    # Zero-value registrations (no observations, just name presence)
    reg = MetricsRegistry.instance()
    from framework.metrics_system import Counter, Gauge, Histogram  # noqa: PLC0415
    _ensure(reg, "aider_tasks_total", Counter)
    _ensure(reg, "aider_task_duration_seconds", Histogram)
    _ensure(reg, "executor_tasks_total", Counter)
    _ensure(reg, "pipeline_stage_duration_seconds", Histogram)
    _ensure(reg, "rag_retrieval_hits_total", Counter)
    _ensure(reg, "active_tasks", Gauge)
    _ensure(reg, "learning_events_total", Counter)
    log.info("Pre-registered %d platform metrics", len(reg.get_all()))


def _ensure(reg: MetricsRegistry, name: str, cls: type) -> None:
    try:
        reg.get(name)
    except KeyError:
        reg.register(cls(name))


if __name__ == "__main__":
    main()
