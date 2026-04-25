#!/usr/bin/env python3
"""Execution dashboard API server.

Serves index.html at / and live JSON metrics at /api/status.

Usage:
    python3 web/dashboard/server.py            # port 8080
    python3 web/dashboard/server.py --port 9090
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).parent.parent.parent
ITEMS_DIR = REPO_ROOT / "docs" / "roadmap" / "ITEMS"
DASHBOARD_DIR = Path(__file__).parent

LOG_CANDIDATES = [
    "/tmp/executor_longrun.log",
    "/tmp/executor_overnight.log",
    "/tmp/executor_clean_run.log",
    "/tmp/executor_3items.log",
]

# ── Data collectors ───────────────────────────────────────────────────────────

def _roadmap_stats() -> dict:
    if not ITEMS_DIR.exists():
        return {"total": 0, "completed": 0, "in_progress": 0, "pending": 0}
    counts: dict[str, int] = {"Completed": 0, "In progress": 0, "Accepted": 0}
    total = 0
    for md in ITEMS_DIR.glob("*.md"):
        total += 1
        text = md.read_text()
        m = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
        if m:
            counts[m.group(1)] = counts.get(m.group(1), 0) + 1
    pending = total - counts["Completed"] - counts["In progress"] - counts["Accepted"]
    return {
        "total": total,
        "completed": counts["Completed"],
        "accepted": counts["Accepted"],
        "in_progress": counts["In progress"],
        "pending": max(pending, 0),
    }


def _find_active_log() -> Path | None:
    newest = None
    newest_mtime = 0.0
    for path_str in LOG_CANDIDATES:
        p = Path(path_str)
        if p.exists():
            mtime = p.stat().st_mtime
            if mtime > newest_mtime:
                newest_mtime = mtime
                newest = p
    return newest


def _parse_log(log_path: Path) -> dict:
    text = log_path.read_text(errors="replace")
    lines = text.splitlines()

    completions = re.findall(r"✅ Completed: (\S+)", text)
    failures = [
        {"item": m.group(1), "error": m.group(2)[:80]}
        for m in re.finditer(r"❌ Failed.*?(\S+).*?error.*?:\s*(.+)", text, re.IGNORECASE)
    ]

    current_item = ""
    current_subtask = ""
    for line in reversed(lines):
        if "🚀" in line and "RM-" in line:
            m = re.search(r"(RM-\S+)", line)
            if m:
                current_item = m.group(1)
                break

    for line in reversed(lines):
        if "execute_subtask called with:" in line:
            m = re.search(r"with: (.+)", line)
            if m:
                current_subtask = m.group(1)[:70]
            break

    # Subtask durations
    durations = [float(x) for x in re.findall(r"duration=(\d+\.\d+)s", text)]
    avg_dur = sum(durations) / len(durations) if durations else 0

    # Running PIDs from log
    pids = re.findall(r"subprocess.Popen SUCCESS: PID=(\d+)", text)
    active_pids = list(set(pids[-5:])) if pids else []

    is_running = any(
        re.search(r"waiting for completion", text) and "Process completed" not in text
        for _ in [1]
    )

    # Simple running check: last line doesn't have SHUTDOWN
    last_lines = "\n".join(lines[-5:])
    is_running = "SHUTDOWN" not in last_lines and "Execution complete" not in last_lines

    return {
        "log_file": str(log_path),
        "log_size_kb": log_path.stat().st_size // 1024,
        "is_running": is_running,
        "current_item": current_item,
        "current_subtask": current_subtask,
        "completions": completions[-20:],
        "completion_count": len(completions),
        "failure_count": len(failures),
        "recent_failures": failures[-5:],
        "avg_subtask_seconds": round(avg_dur, 1),
        "subtask_count": len(durations),
    }


def _git_log() -> list[dict]:
    result = subprocess.run(
        ["git", "log", "--oneline", "--no-walk=unsorted",
         "--format=%h|%s|%ar|%an", "-15"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    commits = []
    for line in result.stdout.strip().splitlines():
        parts = line.split("|", 3)
        if len(parts) == 4:
            commits.append({
                "hash": parts[0],
                "message": parts[1][:72],
                "when": parts[2],
                "author": parts[3],
            })
    return commits


def _training_stats() -> dict:
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from framework.learning_analytics import analyze_training_data
        r = analyze_training_data()
        # r is a TrainingReadiness-like object or dict
        if hasattr(r, "__dict__"):
            r = r.__dict__
        return {
            "quality_examples": r.get("example_count", 0),
            "sft_threshold": 10,
            "lora_threshold": 50,
            "stable_threshold": 200,
            "sft_ready": r.get("sft_ready", False),
            "lora_ready": r.get("lora_ready", False),
            "diff_median_lines": r.get("diff_size_median", 0),
        }
    except Exception as exc:
        return {"error": str(exc), "quality_examples": 0,
                "sft_threshold": 10, "lora_threshold": 50, "stable_threshold": 200}


def _system_health() -> dict:
    # Ollama
    try:
        import urllib.request
        urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)
        ollama_ok = True
    except Exception:
        ollama_ok = False

    # Aider processes
    ps = subprocess.run(["pgrep", "-c", "aider"], capture_output=True, text=True)
    aider_count = int(ps.stdout.strip()) if ps.returncode == 0 else 0

    # Executor processes
    ps2 = subprocess.run(
        ["pgrep", "-f", "auto_execute_roadmap"],
        capture_output=True, text=True,
    )
    executor_pids = [p for p in ps2.stdout.strip().splitlines() if p]

    # Disk space on repo root
    df = subprocess.run(
        ["df", "-g", str(REPO_ROOT)],
        capture_output=True, text=True,
    )
    disk_free_gb = 0
    for line in df.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 4:
            try:
                disk_free_gb = int(parts[3])
            except ValueError:
                pass

    return {
        "ollama_available": ollama_ok,
        "aider_processes": aider_count,
        "executor_pids": executor_pids,
        "executor_running": len(executor_pids) > 0,
        "disk_free_gb": disk_free_gb,
    }


def _build_status() -> dict:
    log_path = _find_active_log()
    exec_data = _parse_log(log_path) if log_path else {"is_running": False, "completion_count": 0}

    return {
        "ts": time.time(),
        "roadmap": _roadmap_stats(),
        "execution": exec_data,
        "git": _git_log(),
        "training": _training_stats(),
        "system": _system_health(),
    }


# ── HTTP handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # suppress per-request noise
        pass

    def do_GET(self):
        path = urlparse(self.path).path

        if path in ("/", "/index.html"):
            self._serve_file(DASHBOARD_DIR / "index.html", "text/html")
        elif path == "/api/status":
            self._serve_json(_build_status())
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_file(self, fpath: Path, content_type: str):
        if not fpath.exists():
            self.send_response(404)
            self.end_headers()
            return
        data = fpath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def _serve_json(self, obj: dict):
        data = json.dumps(obj, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Execution dashboard server")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = HTTPServer((args.host, args.port), Handler)
    print(f"Dashboard: http://localhost:{args.port}/")
    print(f"API:       http://localhost:{args.port}/api/status")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
