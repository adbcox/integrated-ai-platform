#!/usr/bin/env python3
"""RM-UI-005 local execution control window server."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.rm_ui005_control_window import (  # noqa: E402
    build_aider_packet,
    build_control_window_state,
    classify_lane,
    emit_control_window_state,
    render_html,
    run_repo_validations,
)


class RMUI005Handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2).encode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        task = query.get("task", ["Implement RM-UI-005 local execution control window"])[0]
        objective = query.get("objective", [task])[0]
        mode = query.get("mode", ["docker_web"])[0]

        if path == "/" or path == "/index":
            state = build_control_window_state(task_input=task, objective=objective, openhands_mode=mode)
            emit_control_window_state(state)
            html = render_html(state)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if path == "/api/rmui005/state":
            state = build_control_window_state(task_input=task, objective=objective, openhands_mode=mode)
            out = emit_control_window_state(state)
            self._json({"state": state, "artifact": str(out.relative_to(REPO_ROOT))})
            return

        if path == "/api/rmui005/route":
            decision = classify_lane(task)
            self._json({"route_decision": decision.to_dict()})
            return

        if path == "/api/rmui005/packet":
            decision = classify_lane(task)
            packet = build_aider_packet(task_input=objective, decision=decision)
            self._json({"aider_run_packet": packet, "route_decision": decision.to_dict()})
            return

        if path == "/api/rmui005/validate":
            result = run_repo_validations()
            self._json({"validation_run": result})
            return

        if path == "/api/rmui005/openhands/launch":
            state = build_control_window_state(task_input=task, objective=objective, openhands_mode=mode)
            openhands = state["openhands"]
            plan = openhands.get("selected_plan", {})
            dry_run = query.get("dry_run", ["1"])[0] != "0"
            if dry_run:
                self._json({"dry_run": True, "plan": plan, "openhands": openhands})
                return
            cmd = plan.get("command", [])
            if not cmd:
                self._json({"dry_run": False, "started": False, "reason": "no_command"}, status=400)
                return
            proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT))
            self._json({"dry_run": False, "started": True, "pid": proc.pid, "plan": plan, "openhands": openhands})
            return

        self.send_error(404)

    def log_message(self, format, *args):
        return


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RM-UI-005 control window server")
    parser.add_argument("--port", type=int, default=5010)
    args = parser.parse_args()

    server = HTTPServer(("0.0.0.0", args.port), RMUI005Handler)
    print(f"RM-UI-005 control window running on http://localhost:{args.port}")
    print(f"Endpoints:")
    print(f"  / (dashboard)")
    print(f"  /api/rmui005/state")
    print(f"  /api/rmui005/route?task=...")
    print(f"  /api/rmui005/packet?task=...")
    print(f"  /api/rmui005/validate")
    print(f"  /api/rmui005/openhands/launch?mode=docker_web&dry_run=1")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
