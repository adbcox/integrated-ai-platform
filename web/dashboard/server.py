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
TRAINING_LOG_PATH = "/tmp/training_cycle.log"
GITHUB_REPO_URL = "https://github.com/adbcox/integrated-ai-platform"

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

    # Subtask durations — keep full history for trend chart
    durations = [float(x) for x in re.findall(r"duration=(\d+\.\d+)s", text)]
    avg_dur = sum(durations) / len(durations) if durations else 0

    # Subtask N/M: count calls since last item start
    item_start_idx = 0
    for i, line in enumerate(lines):
        if "🚀" in line and "RM-" in line:
            item_start_idx = i
    subtask_index = 0
    subtask_total_guess = 0
    for line in lines[item_start_idx:]:
        if "duration=" in line:
            subtask_index += 1
        m = re.search(r"decomposed into (\d+) subtask", line, re.I)
        if m:
            subtask_total_guess = int(m.group(1))

    # Elapsed time since item start
    elapsed_seconds = 0
    for line in lines[item_start_idx:item_start_idx + 3]:
        tm = re.search(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})", line)
        if tm:
            try:
                import datetime
                ts = datetime.datetime.fromisoformat(tm.group(1).replace(" ", "T"))
                elapsed_seconds = int((datetime.datetime.now() - ts).total_seconds())
            except Exception:
                pass
            break

    # Status description from recent log lines
    live_status = "Running"
    for line in reversed(lines[-15:]):
        ll = line.lower()
        if "aider" in ll and ("running" in ll or "calling" in ll):
            live_status = "Running aider"
            break
        if "decompos" in ll:
            live_status = "Decomposing"
            break
        if "validat" in ll:
            live_status = "Validating"
            break
        if "waiting" in ll:
            live_status = "Waiting"
            break

    last_lines = "\n".join(lines[-5:])
    is_running = "SHUTDOWN" not in last_lines and "Execution complete" not in last_lines

    return {
        "log_file": str(log_path),
        "log_size_kb": log_path.stat().st_size // 1024,
        "is_running": is_running,
        "current_item": current_item,
        "current_subtask": current_subtask,
        "subtask_index": subtask_index,
        "subtask_total": subtask_total_guess,
        "elapsed_seconds": elapsed_seconds,
        "live_status": live_status,
        "completions": completions[-20:],
        "completion_count": len(completions),
        "failure_count": len(failures),
        "recent_failures": failures[-5:],
        "avg_subtask_seconds": round(avg_dur, 1),
        "subtask_count": len(durations),
        "subtask_history": durations[-50:],   # for time-trend chart
    }


def _git_log() -> list[dict]:
    # Get commit metadata
    result = subprocess.run(
        ["git", "log", "--format=COMMIT %h|%s|%ar|%an", "--name-only", "-15"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    commits = []
    cur: dict | None = None
    for line in result.stdout.splitlines():
        if line.startswith("COMMIT "):
            if cur:
                commits.append(cur)
            parts = line[7:].split("|", 3)
            if len(parts) == 4:
                cur = {
                    "hash": parts[0],
                    "message": parts[1][:72],
                    "when": parts[2],
                    "author": parts[3],
                    "files": [],
                }
        elif line.strip() and cur is not None:
            if len(cur["files"]) < 12:
                cur["files"].append(line.strip())
    if cur:
        commits.append(cur)
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
    import urllib.request as _req
    import json as _json

    # Ollama availability + loaded models
    ollama_ok = False
    ollama_queue = 0
    try:
        _req.urlopen("http://127.0.0.1:11434/api/tags", timeout=2)
        ollama_ok = True
        with _req.urlopen("http://127.0.0.1:11434/api/ps", timeout=1) as r:
            ollama_queue = len(_json.loads(r.read()).get("models", []))
    except Exception:
        pass

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
    df = subprocess.run(["df", "-g", str(REPO_ROOT)], capture_output=True, text=True)
    disk_free_gb = 0
    for line in df.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 4:
            try:
                disk_free_gb = int(parts[3])
            except ValueError:
                pass

    # CPU usage (macOS top)
    cpu_pct = 0
    try:
        top_r = subprocess.run(["top", "-l", "1", "-n", "0"], capture_output=True, text=True, timeout=5)
        m = re.search(r"CPU usage:\s*([\d.]+)%\s*user,\s*([\d.]+)%\s*sys", top_r.stdout)
        if m:
            cpu_pct = round(float(m.group(1)) + float(m.group(2)), 1)
    except Exception:
        pass

    # RAM (macOS vm_stat + sysctl)
    ram_total_gb = 0
    ram_used_pct = 0
    try:
        total_r = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
        ram_total_bytes = int(total_r.stdout.strip())
        ram_total_gb = ram_total_bytes // (1024 ** 3)
        vm_r = subprocess.run(["vm_stat"], capture_output=True, text=True)
        page_size = 16384
        pages_free = 0
        for ln in vm_r.stdout.splitlines():
            if "page size of" in ln:
                pm = re.search(r"page size of (\d+)", ln)
                if pm:
                    page_size = int(pm.group(1))
            fm = re.search(r"Pages free:\s+(\d+)", ln)
            if fm:
                pages_free = int(fm.group(1))
        free_bytes = pages_free * page_size
        ram_used_pct = round((1 - free_bytes / ram_total_bytes) * 100) if ram_total_bytes else 0
    except Exception:
        pass

    return {
        "ollama_available": ollama_ok,
        "ollama_queue": ollama_queue,
        "aider_processes": aider_count,
        "executor_pids": executor_pids,
        "executor_running": len(executor_pids) > 0,
        "disk_free_gb": disk_free_gb,
        "cpu_pct": cpu_pct,
        "ram_used_pct": ram_used_pct,
        "ram_total_gb": ram_total_gb,
    }


def _category_stats() -> list[dict]:
    """Return per-category completion breakdown, sorted by total desc."""
    if not ITEMS_DIR.exists():
        return []
    from collections import Counter
    totals: Counter = Counter()
    done: Counter = Counter()
    for md in ITEMS_DIR.glob("*.md"):
        text = md.read_text()
        cat_m = re.search(r"\*\*Category:\*\*\s*`([^`]+)`", text)
        stat_m = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
        cat = cat_m.group(1) if cat_m else "?"
        stat = stat_m.group(1) if stat_m else "?"
        totals[cat] += 1
        if stat in ("Completed", "Accepted"):
            done[cat] += 1
    result = []
    for cat, total in totals.most_common(15):
        d = done.get(cat, 0)
        result.append({
            "category": cat,
            "total": total,
            "done": d,
            "pct": round(d / total * 100) if total else 0,
        })
    return result


def _kanban_items() -> dict:
    """Return items grouped by status (trimmed for payload size)."""
    if not ITEMS_DIR.exists():
        return {}
    buckets: dict[str, list] = {
        "In progress": [], "Pending": [], "Completed": [], "Accepted": [],
    }
    for md in sorted(ITEMS_DIR.glob("*.md")):
        text = md.read_text()
        id_m = re.search(r"\*\*ID:\*\*\s*`([^`]+)`", text)
        title_m = re.search(r"\*\*Title:\*\*\s*(.+)", text)
        stat_m = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
        cat_m = re.search(r"\*\*Category:\*\*\s*`([^`]+)`", text)
        item_id = id_m.group(1) if id_m else md.stem
        title = (title_m.group(1).strip() if title_m else item_id)[:60]
        stat = stat_m.group(1) if stat_m else "Pending"
        cat = cat_m.group(1) if cat_m else "?"
        bucket = stat if stat in buckets else "Pending"
        # Limit payload: only keep first 40 per bucket
        if len(buckets[bucket]) < 40:
            buckets[bucket].append({"id": item_id, "title": title, "category": cat})
    return buckets


def _executor_action(action: str) -> dict:
    """Start or stop the autonomous executor. Returns {ok, message}."""
    if action == "start":
        r = subprocess.run(
            ["pgrep", "-f", "auto_execute_roadmap"],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            return {"ok": False, "message": f"Already running (PID {r.stdout.strip().split()[0]})"}
        log_path = "/tmp/executor_longrun.log"
        proc = subprocess.Popen(
            [sys.executable, str(REPO_ROOT / "bin" / "auto_execute_roadmap.py"),
             "--max-items", "10"],
            cwd=REPO_ROOT,
            stdout=open(log_path, "w"),
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        return {"ok": True, "message": f"Started PID {proc.pid}", "pid": proc.pid,
                "log": log_path}

    elif action == "stop":
        r = subprocess.run(
            ["pgrep", "-f", "auto_execute_roadmap"],
            capture_output=True, text=True,
        )
        pids = [p for p in r.stdout.strip().splitlines() if p]
        if not pids:
            return {"ok": False, "message": "No executor running"}
        for pid in pids:
            subprocess.run(["kill", "-TERM", pid], capture_output=True)
        return {"ok": True, "message": f"Sent SIGTERM to PID(s) {', '.join(pids)}"}

    return {"ok": False, "message": f"Unknown action: {action}"}


def _executor_live_status() -> dict:
    """Lightweight status for 2-second polling — reads only what changed."""
    log_path = _find_active_log()
    if not log_path:
        return {"running": False, "current_item": "", "subtask_index": 0,
                "subtask_total": 0, "elapsed_seconds": 0, "live_status": "Idle",
                "current_subtask": "", "avg_subtask_seconds": 0}
    d = _parse_log(log_path)
    return {
        "running":            d["is_running"],
        "current_item":       d["current_item"],
        "current_subtask":    d["current_subtask"],
        "subtask_index":      d["subtask_index"],
        "subtask_total":      d["subtask_total"],
        "elapsed_seconds":    d["elapsed_seconds"],
        "live_status":        d["live_status"],
        "avg_subtask_seconds": d["avg_subtask_seconds"],
        "completion_count":   d["completion_count"],
        "failure_count":      d["failure_count"],
    }


def _get_recommendations() -> list:
    """Top 5 quick-win items from the roadmap analyzer (no pending deps)."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "analyze_roadmap", str(REPO_ROOT / "bin" / "analyze_roadmap.py")
        )
        ar = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ar)

        items = ar.load_items()
        ar.annotate_unlocks(items)
        pending_ids = {it.id for it in items}
        no_dep = [it for it in items if not any(d in pending_ids for d in it.deps)]
        ranked = sorted(no_dep, key=lambda x: x.easiness, reverse=True)[:5]
        return [
            {
                "id":       it.id,
                "title":    it.title,
                "category": it.category,
                "loe":      it.loe,
                "risk":     it.risk,
                "easiness": it.easiness,
                "unlocks":  it.unlocks_count,
                "filter":   it.id,
            }
            for it in ranked
        ]
    except Exception as exc:
        return [{"error": str(exc), "id": "", "title": str(exc), "category": "",
                 "loe": "?", "risk": 3, "easiness": 0, "unlocks": 0, "filter": ""}]


def _validate_training_prereqs() -> dict | None:
    """Return error dict if training can't start, else None."""
    # Check training data
    data_path = REPO_ROOT / "artifacts" / "training_data" / "alpaca.jsonl"
    if not data_path.exists():
        return {"ok": False, "message": "No training data at artifacts/training_data/alpaca.jsonl — run bin/collect_training_data.py first"}
    # Check quality examples count
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from framework.learning_analytics import analyze_training_data
        r = analyze_training_data()
        count = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
        if count < 10:
            return {"ok": False, "message": f"Only {count}/10 quality examples — collect more before training"}
    except Exception:
        pass
    # Check venv
    venv = Path.home() / "training-env" / "bin" / "python"
    if not venv.exists():
        return {"ok": False, "message": "~/training-env not found — run bin/run_training_cycle.py once to set it up"}
    return None


def _start_training() -> dict:
    """Spawn run_training_cycle.py inside ~/training-env."""
    r = subprocess.run(["pgrep", "-f", "run_training_cycle"], capture_output=True, text=True)
    if r.stdout.strip():
        pid = r.stdout.strip().split()[0]
        return {"ok": False, "message": f"Already running (PID {pid})", "pid": int(pid)}

    script = REPO_ROOT / "bin" / "run_training_cycle.py"
    if not script.exists():
        return {"ok": False, "message": "bin/run_training_cycle.py not found"}

    err = _validate_training_prereqs()
    if err:
        return err

    venv_python = Path.home() / "training-env" / "bin" / "python"
    data_path   = REPO_ROOT / "artifacts" / "training_data" / "alpaca.jsonl"
    cmd = [
        "/bin/bash", "-c",
        f"source {Path.home()}/training-env/bin/activate && "
        f"python3 {script} --data {data_path} "
        f"> {TRAINING_LOG_PATH} 2>&1"
    ]
    proc = subprocess.Popen(cmd, cwd=REPO_ROOT, start_new_session=True)
    return {
        "ok": True,
        "message": f"Training started (PID {proc.pid})",
        "pid": proc.pid,
        "log": TRAINING_LOG_PATH,
        "estimated_minutes": 45,
        "status": "started",
    }


def _training_cycle_status() -> dict:
    """Parse TRAINING_LOG_PATH for step progress and status."""
    log = Path(TRAINING_LOG_PATH)
    if not log.exists():
        return {"is_running": False, "lines": [], "step": 0, "total_steps": 0,
                "progress_percent": 0, "current_step": "", "eta_minutes": 0}
    text  = log.read_text(errors="replace")
    lines = text.splitlines()

    r = subprocess.run(["pgrep", "-f", "run_training_cycle"], capture_output=True, text=True)
    running = bool(r.stdout.strip())

    step = total = 0
    current_step = "Preparing"
    for line in reversed(lines):
        # "Step 15/500" or "step 15 of 500"
        m = re.search(r"[Ss]tep[s]?\s+(\d+)\s*[/of]+\s*(\d+)", line)
        if m:
            step, total = int(m.group(1)), int(m.group(2))
            break
    for line in reversed(lines[-20:]):
        ll = line.lower()
        if "collect" in ll or "gathering" in ll:
            current_step = "Collecting training data"
        elif "tokeniz" in ll or "preprocess" in ll:
            current_step = "Preprocessing data"
        elif "train" in ll and "lora" in ll:
            current_step = "Training LoRA adapter"
        elif "save" in ll or "export" in ll:
            current_step = "Saving adapter"
        elif "gguf" in ll:
            current_step = "Exporting GGUF"

    pct = round(step / total * 100) if total > 0 else 0
    done = not running and any(kw in text for kw in ("Training complete", "Saved adapter", "Done", "adapter_model"))
    eta_minutes = 0
    if running and total > 0 and step > 0:
        # Estimate from log timestamps if possible, else rough guess
        eta_minutes = max(1, round((total - step) * 0.5))

    return {
        "is_running":       running,
        "done":             done,
        "step":             step,
        "total_steps":      total,
        "progress_percent": pct,
        "current_step":     current_step,
        "eta_minutes":      eta_minutes,
        "log_tail":         lines[-15:],
        "log_file":         TRAINING_LOG_PATH,
    }


def _deploy_model() -> dict:
    """Load trained LoRA adapter into Ollama as qwen2.5-coder:custom."""
    adapter = REPO_ROOT / "artifacts" / "lora_adapter"
    if not adapter.exists():
        return {"ok": False, "message": "No trained adapter at artifacts/lora_adapter — train first"}
    modelfile = Path("/tmp/Modelfile_custom")
    modelfile.write_text(
        "FROM qwen2.5-coder:14b\n"
        f"ADAPTER {adapter}\n"
        'PARAMETER system "You are an expert coding assistant fine-tuned on this codebase."\n'
    )
    r = subprocess.run(
        ["ollama", "create", "qwen2.5-coder:custom", "-f", str(modelfile)],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        return {"ok": False, "message": f"ollama create failed: {r.stderr[:200]}"}
    return {"ok": True, "message": "qwen2.5-coder:custom deployed to Ollama"}


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
        "categories": _category_stats(),
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
        elif path == "/api/kanban":
            self._serve_json(_kanban_items())
        elif path == "/api/log":
            log = _find_active_log()
            if log:
                lines = log.read_text(errors="replace").splitlines()
                self._serve_json({"lines": lines[-200:], "file": str(log)})
            else:
                self._serve_json({"lines": [], "file": None})
        elif path.startswith("/api/diff/"):
            hash_ = path[len("/api/diff/"):]
            if re.match(r"^[0-9a-f]{7,40}$", hash_):
                stat_r = subprocess.run(
                    ["git", "show", "--stat", "--format=format:", hash_],
                    capture_output=True, text=True, cwd=REPO_ROOT,
                )
                diff_r = subprocess.run(
                    ["git", "show", "--format=format:", hash_],
                    capture_output=True, text=True, cwd=REPO_ROOT,
                )
                self._serve_json({
                    "stat": stat_r.stdout[:2000],
                    "diff": diff_r.stdout[:10000],
                    "hash": hash_,
                })
            else:
                self.send_response(400)
                self.end_headers()
        elif path == "/api/executor/status":
            self._serve_json(_executor_live_status())
        elif path == "/api/recommendations":
            self._serve_json({"items": _get_recommendations()})
        elif path == "/api/train/status":
            self._serve_json(_training_cycle_status())
        elif path == "/api/training/status":
            self._serve_json(_training_cycle_status())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")

        if path == "/api/executor":
            action = body.get("action", "")
            self._serve_json(_executor_action(action))
        elif path in ("/api/train", "/api/training/start"):
            self._serve_json(_start_training())
        elif path == "/api/model/deploy":
            self._serve_json(_deploy_model())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
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
