#!/usr/bin/env python3
"""Minimal Zabbix Prometheus exporter."""
import os
import sys
import time
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

ZABBIX_URL   = os.environ.get("ZABBIX_URL", "http://zabbix-web:8080")
ZABBIX_TOKEN = os.environ.get("ZABBIX_API_TOKEN", "")
PORT         = int(os.environ.get("PORT", "9224"))
SCRAPE_INTERVAL = 60

_metrics = {}
_last_collect = 0.0


def zbx_post(method: str, params: dict) -> dict:
    payload = json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode()
    req = urllib.request.Request(
        f"{ZABBIX_URL}/api_jsonrpc.php",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {ZABBIX_TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())


def collect():
    global _metrics, _last_collect
    out = {}
    try:
        # Active triggers by priority
        trigger_resp = zbx_post("trigger.get", {
            "only_true": 1,
            "output": ["triggerid", "priority"],
            "monitored": 1,
        })
        prio_counts = {}
        for t in trigger_resp.get("result", []):
            p = t.get("priority", "0")
            prio_counts[p] = prio_counts.get(p, 0) + 1

        prio_names = {"0": "not_classified", "1": "information", "2": "warning",
                      "3": "average", "4": "high", "5": "disaster"}
        for prio, count in prio_counts.items():
            label = prio_names.get(prio, prio)
            out[f'zabbix_triggers_active{{severity="{label}"}}'] = count

        # Ensure all severities have a 0 value
        for prio, label in prio_names.items():
            key = f'zabbix_triggers_active{{severity="{label}"}}'
            if key not in out:
                out[key] = 0

        # Host availability
        host_resp = zbx_post("host.get", {
            "output": ["hostid", "available", "status"],
            "monitored_hosts": 1,
        })
        avail_counts = {}
        for h in host_resp.get("result", []):
            a = h.get("available", "0")
            avail_counts[a] = avail_counts.get(a, 0) + 1

        avail_names = {"0": "unknown", "1": "available", "2": "unavailable"}
        for avail, count in avail_counts.items():
            label = avail_names.get(avail, avail)
            out[f'zabbix_hosts_available{{status="{label}"}}'] = count
        for avail, label in avail_names.items():
            key = f'zabbix_hosts_available{{status="{label}"}}'
            if key not in out:
                out[key] = 0

        out["zabbix_scrape_success"] = 1

    except Exception as exc:
        print(f"Collect error: {exc}", file=sys.stderr)
        out["zabbix_scrape_success"] = 0

    _metrics = out
    _last_collect = time.time()


class MetricsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        global _last_collect
        if self.path not in ("/metrics", "/"):
            self.send_response(404)
            self.end_headers()
            return

        if time.time() - _last_collect > SCRAPE_INTERVAL:
            collect()

        lines = ["# HELP zabbix_triggers_active Active Zabbix triggers by severity",
                 "# TYPE zabbix_triggers_active gauge"]
        for k, v in _metrics.items():
            if "triggers" in k:
                lines.append(f"{k} {v}")
        lines += ["# HELP zabbix_hosts_available Zabbix host availability count",
                  "# TYPE zabbix_hosts_available gauge"]
        for k, v in _metrics.items():
            if "hosts" in k:
                lines.append(f"{k} {v}")
        lines += ["# HELP zabbix_scrape_success Whether the last Zabbix scrape succeeded",
                  "# TYPE zabbix_scrape_success gauge"]
        if "zabbix_scrape_success" in _metrics:
            lines.append(f"zabbix_scrape_success {_metrics['zabbix_scrape_success']}")
        lines.append("")

        body = "\n".join(lines).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    collect()
    server = HTTPServer(("0.0.0.0", PORT), MetricsHandler)
    print(f"Serving on :{PORT}")
    server.serve_forever()
