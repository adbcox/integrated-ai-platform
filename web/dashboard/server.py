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
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import urlparse

_env_repo = os.environ.get("REPO_ROOT", "")
REPO_ROOT = Path(_env_repo) if _env_repo else Path(__file__).parent.parent.parent
_env_items = os.environ.get("ITEMS_DIR", "")
ITEMS_DIR = Path(_env_items) if _env_items else REPO_ROOT / "docs" / "roadmap" / "ITEMS"
DASHBOARD_DIR = Path(__file__).parent

# ── Load docker/.env into environment (only sets vars not already set) ─────────
_dotenv = REPO_ROOT / "docker" / ".env"
if _dotenv.exists():
    for _line in _dotenv.read_text(errors="replace").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _, _v = _line.partition("=")
            _k = _k.strip()
            if _k and _k not in os.environ:
                os.environ[_k] = _v.strip()

_LOG_DIR = Path(os.environ.get("LOG_DIR", "/tmp"))
EXECUTOR_HOST = os.environ.get("EXECUTOR_HOST", "")
REMOTE_REPO_ROOT = os.environ.get("REMOTE_REPO_ROOT", "~/repos/integrated-ai-platform")

LOG_CANDIDATES = [
    str(_LOG_DIR / "executor_longrun.log"),
    str(_LOG_DIR / "executor_overnight.log"),
    str(_LOG_DIR / "executor_clean_run.log"),
    str(_LOG_DIR / "executor_3items.log"),
    # repo-root execution.log written by some executor invocations
    str(Path(__file__).parent.parent.parent / "execution.log"),
]
TRAINING_LOG_PATH = str(_LOG_DIR / "training_cycle.log")
GITHUB_REPO_URL = "https://github.com/adbcox/integrated-ai-platform"

# ── Circuit breakers (one per external service) ───────────────────────────────
sys.path.insert(0, str(REPO_ROOT))
from framework.circuit_breaker import CircuitBreaker as _CB  # noqa: E402

_breakers: dict[str, _CB] = {
    "sonarr":   _CB("sonarr",   failures_to_open=5, timeout_seconds=30),
    "radarr":   _CB("radarr",   failures_to_open=5, timeout_seconds=30),
    "prowlarr": _CB("prowlarr", failures_to_open=5, timeout_seconds=30),
    "plex":     _CB("plex",     failures_to_open=5, timeout_seconds=30),
    "qnap":     _CB("qnap",     failures_to_open=3, timeout_seconds=60),
    "seedbox":  _CB("seedbox",  failures_to_open=3, timeout_seconds=60),
    "ollama":   _CB("ollama",   failures_to_open=5, timeout_seconds=30),
}

# ── TTL response cache ────────────────────────────────────────────────────────
# Structure: key → (value, expires_at_monotonic, stored_at_wallclock)
_resp_cache: dict[str, tuple[object, float, float]] = {}
_cache_lock = threading.Lock()

_CACHE_TTL = {
    "media_pipeline":   30,
    "media_issues":     30,
    "media_queue":      15,
    "media_rclone":     20,
    "media_missing":    300,
    "media_downloads":  20,
    "seedbox_status":   25,
    "seedbox_queue":    15,
    "media_recent":     60,
    "media_upcoming":   120,
    "infra_status":     10,
    "system_stats":     5,
    "roadmap_stats":    60,
    "selfheal_status":  30,
    "plane_stats":       30,
    "analytics_deps":    120,
    "analytics_effort":  300,
    "analytics_priorities": 120,
    "analytics_progress": 60,
    "media_quality":     300,
    "media_recs_ai":     600,
    "training_viz":      30,
}

# ── Self-healing daemon integration ──────────────────────────────────────────
from bin.selfheal import (  # noqa: E402
    run_heal_cycle as _run_heal_cycle,
    start_daemon_thread as _start_heal_daemon,
    stop_daemon as _stop_heal_daemon,
    ai_diagnose as _ai_diagnose,
    _daemon_state as _heal_state,
)
from framework.heal_log import recent_fixes as _recent_fixes, tail as _heal_tail

_heal_thread = None


def _cached(key: str, fn, ttl: float | None = None) -> tuple[object, bool, int]:
    """
    Return (result, from_cache, cache_age_seconds).
    Calls fn() on cache miss; returns stale on cache hit.
    """
    effective_ttl = ttl if ttl is not None else _CACHE_TTL.get(key, 30)
    now_mono = time.monotonic()
    now_wall = time.time()
    with _cache_lock:
        if key in _resp_cache:
            value, expires, stored_wall = _resp_cache[key]
            if now_mono < expires:
                age = round(now_wall - stored_wall)
                return value, True, age
    result = fn()
    with _cache_lock:
        _resp_cache[key] = (result, now_mono + effective_ttl, now_wall)
    return result, False, 0

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
    """Return the newest non-empty executor log file."""
    newest = None
    newest_mtime = 0.0
    for path_str in LOG_CANDIDATES:
        p = Path(path_str)
        try:
            st = p.stat()
        except OSError:
            continue
        if st.st_size == 0:
            continue  # skip empty files — they cause false "running" detection
        if st.st_mtime > newest_mtime:
            newest_mtime = st.st_mtime
            newest = p
    return newest


def _parse_log(log_path: Path) -> dict:
    import datetime as _dt
    text  = log_path.read_text(errors="replace")
    lines = text.splitlines()

    # ── Process existence check (authoritative for is_running) ───────────────
    r = subprocess.run(
        ["pgrep", "-f", "auto_execute_roadmap"],
        capture_output=True, text=True,
    )
    proc_running = bool(r.stdout.strip())
    # Log-based fallback: if pgrep misses it (e.g. subprocess wrapper), check log
    last5 = "\n".join(lines[-5:])
    log_done = "SHUTDOWN" in last5 or "Execution complete" in last5 or "🏁" in last5
    is_running = proc_running or (not log_done and log_path.stat().st_size > 0
                                  and (_dt.datetime.now().timestamp() - log_path.stat().st_mtime) < 300)

    # ── Current item (most recent 🚀 RM-XXX line) ─────────────────────────────
    current_item = ""
    item_start_idx = 0
    for i, line in enumerate(lines):
        if "🚀" in line and "RM-" in line:
            m = re.search(r"(RM-[A-Z0-9]+-\d+)", line)
            if m:
                current_item = m.group(1)
                item_start_idx = i

    # ── Current subtask text ──────────────────────────────────────────────────
    # Log format: [DEBUG] execute_subtask called with: dry_run=False, subtask='TEXT HERE'
    current_subtask = ""
    for line in reversed(lines):
        if "execute_subtask called with:" in line:
            # Extract subtask='...' value
            sm = re.search(r"subtask='([^']+)'", line)
            if sm:
                current_subtask = sm.group(1)[:80]
            else:
                # Fallback: grab everything after "with: "
                fm = re.search(r"with:\s*(.+)", line)
                if fm:
                    current_subtask = fm.group(1)[:80]
            break
        # Also catch: [DEBUG] Calling execute_subtask with: TEXT
        if "Calling execute_subtask with:" in line:
            fm = re.search(r"with:\s*(.+)", line)
            if fm:
                current_subtask = fm.group(1)[:80]
            break

    # ── Subtask N/M progress ──────────────────────────────────────────────────
    # Log format: "   [1/4] " or "   [N/M]" lines, one per subtask start
    subtask_index = 0
    subtask_total = 0
    for line in lines[item_start_idx:]:
        nm = re.search(r"\[(\d+)/(\d+)\]", line)
        if nm:
            subtask_index = int(nm.group(1))
            subtask_total = int(nm.group(2))
        # Also accept "Generated N subtasks:" format
        gm = re.search(r"Generated (\d+) subtask", line, re.I)
        if gm and subtask_total == 0:
            subtask_total = int(gm.group(1))

    # Count completed subtasks since item start (duration= lines = subtask finished)
    durations = [float(x) for x in re.findall(r"duration=([\d.]+)s", text)]
    item_durations = [float(x) for x in re.findall(r"duration=([\d.]+)s",
                                                    "\n".join(lines[item_start_idx:]))]
    avg_dur = sum(durations) / len(durations) if durations else 0

    # ── Elapsed since item start ──────────────────────────────────────────────
    elapsed_seconds = 0
    for line in lines[item_start_idx:item_start_idx + 5]:
        tm = re.search(r"(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})", line)
        if tm:
            try:
                ts = _dt.datetime.fromisoformat(tm.group(1).replace(" ", "T"))
                elapsed_seconds = int((_dt.datetime.now() - ts).total_seconds())
            except Exception:
                pass
            break

    # ── Completions and failures ──────────────────────────────────────────────
    completions = re.findall(r"✅ Completed: (\S+)", text)
    completions += re.findall(r"✅ DONE: (RM-[A-Z0-9]+-\d+)", text)
    failures = [
        {"item": m.group(1), "error": m.group(2)[:80]}
        for m in re.finditer(
            r"(?:❌ FAILED|❌ Failed).*?(RM-[A-Z0-9]+-\d+|item\s+\S+)[^\n]*\n?([^\n]*)",
            text, re.IGNORECASE)
    ]

    # ── Live status label ─────────────────────────────────────────────────────
    live_status = "Running"
    for line in reversed(lines[-20:]):
        ll = line.lower()
        if "aider" in ll and ("run" in ll or "call" in ll or "execut" in ll):
            live_status = "Running aider"; break
        if "calling execute_subtask" in ll or "execute_subtask called" in ll:
            live_status = "Executing subtask"; break
        if "decompos" in ll:
            live_status = "Decomposing task"; break
        if "validat" in ll:
            live_status = "Validating"; break
        if "waiting" in ll or "sleep" in ll:
            live_status = "Waiting"; break
        if "❌ failed" in ll or "failed:" in ll:
            live_status = "Retrying"; break

    return {
        "log_file":           str(log_path),
        "log_size_kb":        log_path.stat().st_size // 1024,
        "is_running":         is_running,
        "current_item":       current_item,
        "current_subtask":    current_subtask,
        "subtask_index":      subtask_index,
        "subtask_total":      subtask_total,
        "elapsed_seconds":    elapsed_seconds,
        "live_status":        live_status,
        "completions":        list(dict.fromkeys(completions))[-20:],
        "completion_count":   len(set(completions)),
        "failure_count":      len(failures),
        "recent_failures":    failures[-5:],
        "avg_subtask_seconds": round(avg_dur, 1),
        "subtask_count":      len(durations),
        "subtask_history":    durations[-50:],
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


def _velocity_stats() -> dict:
    """Return daily completion counts for the last 30 days from git log."""
    import datetime as _dt
    result = subprocess.run(
        ["git", "log", "--format=%ad %s", "--date=short", "--grep=→ Completed", "-500"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    )
    counts: dict[str, int] = {}
    for line in result.stdout.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            date_str = parts[0]
            counts[date_str] = counts.get(date_str, 0) + 1

    today = _dt.date.today()
    days = [(today - _dt.timedelta(days=i)).isoformat() for i in range(29, -1, -1)]
    series = [{"date": d, "count": counts.get(d, 0)} for d in days]
    total = sum(counts.get(d, 0) for d in days)
    active_days = sum(1 for d in days if counts.get(d, 0) > 0)
    avg = round(total / active_days, 1) if active_days else 0

    return {"daily": series, "total_30d": total, "active_days": active_days, "avg_per_active_day": avg}


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
            "sft_threshold": 5,
            "lora_threshold": 50,
            "stable_threshold": 200,
            "sft_ready": r.get("sft_ready", False),
            "lora_ready": r.get("lora_ready", False),
            "diff_median_lines": r.get("diff_size_median", 0),
        }
    except Exception as exc:
        return {"error": str(exc), "quality_examples": 0,
                "sft_threshold": 5, "lora_threshold": 50, "stable_threshold": 200}


def _system_health() -> dict:
    import platform
    import urllib.request as _req
    import json as _json

    is_macos = platform.system() == "Darwin"
    ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")

    # Ollama availability + loaded models
    ollama_ok = False
    ollama_queue = 0
    try:
        _req.urlopen(f"http://{ollama_host}/api/tags", timeout=2)
        ollama_ok = True
        with _req.urlopen(f"http://{ollama_host}/api/ps", timeout=1) as r:
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
    disk_free_gb = 0
    try:
        if is_macos:
            df = subprocess.run(["df", "-g", str(REPO_ROOT)], capture_output=True, text=True)
            col_idx = 3
        else:
            df = subprocess.run(["df", "-BG", str(REPO_ROOT)], capture_output=True, text=True)
            col_idx = 3
        for line in df.stdout.splitlines()[1:]:
            parts = line.split()
            if len(parts) > col_idx:
                try:
                    disk_free_gb = int(parts[col_idx].rstrip("G"))
                except ValueError:
                    pass
    except Exception:
        pass

    # CPU usage
    cpu_pct = 0
    try:
        if is_macos:
            top_r = subprocess.run(["top", "-l", "1", "-n", "0"], capture_output=True, text=True, timeout=5)
            m = re.search(r"CPU usage:\s*([\d.]+)%\s*user,\s*([\d.]+)%\s*sys", top_r.stdout)
            if m:
                cpu_pct = round(float(m.group(1)) + float(m.group(2)), 1)
        else:
            with open("/proc/loadavg") as f:
                cpu_pct = round(float(f.read().split()[0]) * 10, 1)
    except Exception:
        pass

    # RAM
    ram_total_gb = 0
    ram_used_pct = 0
    try:
        if is_macos:
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
        else:
            mem_info: dict[str, int] = {}
            with open("/proc/meminfo") as f:
                for ln in f:
                    parts = ln.split()
                    if len(parts) >= 2:
                        mem_info[parts[0].rstrip(":")] = int(parts[1])
            ram_total_kb = mem_info.get("MemTotal", 0)
            ram_avail_kb = mem_info.get("MemAvailable", 0)
            ram_total_gb = ram_total_kb // (1024 ** 2)
            ram_used_pct = round((1 - ram_avail_kb / ram_total_kb) * 100) if ram_total_kb else 0
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


def _executor_action_remote(action: str, body: dict) -> dict:
    """SSH-based executor control for EXECUTOR_HOST."""
    max_items = body.get("max_items", 50)
    log_path = str(_LOG_DIR / "executor_longrun.log")
    remote_script = f"{REMOTE_REPO_ROOT}/bin/auto_execute_roadmap.py"
    ssh_base = ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "BatchMode=yes", EXECUTOR_HOST]

    if action == "start":
        check = subprocess.run(
            ssh_base + ["pgrep -f auto_execute_roadmap || echo NOTRUNNING"],
            capture_output=True, text=True, timeout=10,
        )
        if "NOTRUNNING" not in check.stdout:
            return {"ok": False, "message": f"Already running on {EXECUTOR_HOST}"}
        start_cmd = (
            f"nohup python3 {remote_script} --max-items {max_items} "
            f"> {log_path} 2>&1 & echo $!"
        )
        r = subprocess.run(ssh_base + [start_cmd], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            return {"ok": False, "message": f"SSH start failed: {r.stderr[:200]}"}
        return {"ok": True, "message": f"Remote executor started on {EXECUTOR_HOST} (PID {r.stdout.strip()})"}

    elif action == "stop":
        r = subprocess.run(
            ssh_base + ["pkill -TERM -f auto_execute_roadmap && echo stopped || echo not_running"],
            capture_output=True, text=True, timeout=10,
        )
        return {"ok": True, "message": f"Remote stop signal sent to {EXECUTOR_HOST}: {r.stdout.strip()}"}

    return {"ok": False, "message": f"Unknown action: {action}"}


def _executor_action(action: str, body: dict | None = None) -> dict:
    """Start or stop the autonomous executor. Returns {ok, message}."""
    body = body or {}
    if EXECUTOR_HOST:
        return _executor_action_remote(action, body)
    if action == "start":
        r = subprocess.run(
            ["pgrep", "-f", "auto_execute_roadmap"],
            capture_output=True, text=True,
        )
        if r.stdout.strip():
            return {"ok": False, "message": f"Already running (PID {r.stdout.strip().split()[0]})"}
        log_path = str(_LOG_DIR / "executor_longrun.log")
        max_items = str(body.get("max_items", 50))
        cmd = [
            sys.executable, str(REPO_ROOT / "bin" / "auto_execute_roadmap.py"),
            "--max-items", max_items,
        ]
        filter_arg = body.get("filter", "")
        if filter_arg:
            cmd += ["--filter", filter_arg]
        proc = subprocess.Popen(
            cmd,
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
        # Wait up to 5 seconds for graceful exit, then SIGKILL
        import time as _time
        deadline = _time.time() + 5
        while _time.time() < deadline:
            still = subprocess.run(["pgrep", "-f", "auto_execute_roadmap"],
                                   capture_output=True, text=True).stdout.strip().splitlines()
            if not still:
                break
            _time.sleep(0.5)
        still = subprocess.run(["pgrep", "-f", "auto_execute_roadmap"],
                               capture_output=True, text=True).stdout.strip().splitlines()
        killed = []
        for pid in still:
            subprocess.run(["kill", "-KILL", pid], capture_output=True)
            killed.append(pid)
        msg = f"Stopped PID(s) {', '.join(pids)}"
        if killed:
            msg += f" (SIGKILL used on {', '.join(killed)})"
        return {"ok": True, "message": msg}

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
    # Check quality examples count (minimum 5 to start; 10+ is recommended)
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from framework.learning_analytics import analyze_training_data
        r = analyze_training_data()
        count = r.get("example_count", 0) if isinstance(r, dict) else getattr(r, "example_count", 0)
        if count < 5:
            return {"ok": False, "message": f"Only {count}/5 quality examples — run the executor to collect more (10+ recommended)"}
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
    """Parse TRAINING_LOG_PATH for step progress and status.

    HuggingFace Trainer disables tqdm when stdout is redirected (not a TTY),
    so step counts come from the per-step JSON dicts it emits instead:
        {'loss': 2.66, 'learning_rate': 0.0001, 'epoch': 0.14}
    We count these lines as the current step and parse epoch for percentage.
    tqdm lines are still tried as a fallback for scripts that force progress.
    """
    import time as _time
    log = Path(TRAINING_LOG_PATH)
    if not log.exists():
        return {"is_running": False, "stuck": False, "pids": [], "lines": [],
                "step": 0, "total_steps": 0, "progress_percent": 0,
                "current_step": "", "eta_minutes": 0, "loss": None, "log_tail": []}
    raw   = log.read_text(errors="replace")
    # Split on \r and \n — tqdm uses \r for in-place updates in some modes
    lines = [l for l in re.split(r"[\r\n]+", raw) if l.strip()]

    r = subprocess.run(["pgrep", "-f", "run_training_cycle"], capture_output=True, text=True)
    pids = [p for p in r.stdout.strip().splitlines() if p]
    running = bool(pids)

    stuck = False
    if running:
        stuck = (_time.time() - log.stat().st_mtime) > 600

    step = total = 0
    loss: float | None = None
    current_epoch: float | None = None
    num_epochs = 3  # matches TrainingConfig default in framework/model_trainer.py

    # ── Primary: parse HuggingFace Trainer JSON-dict log lines ──────────────
    # Two formats: {'loss': 2.66, 'epoch': 0.14}  OR  {"loss": 2.66, "epoch": 0.14}
    _metric_re = re.compile(r"""['""]loss['"]\s*:\s*([\d.eE+\-]+)""")
    _epoch_re  = re.compile(r"""['""]epoch['"]\s*:\s*([\d.]+)""")
    metric_count = 0
    for line in lines:
        if _metric_re.search(line) and _epoch_re.search(line):
            metric_count += 1
            loss_m  = _metric_re.search(line)
            epoch_m = _epoch_re.search(line)
            if loss_m:
                try:
                    loss = round(float(loss_m.group(1)), 4)
                except ValueError:
                    pass
            if epoch_m:
                try:
                    current_epoch = float(epoch_m.group(1))
                except ValueError:
                    pass

    if metric_count > 0:
        step = metric_count
        # Estimate total steps from epoch if we have it
        if current_epoch and current_epoch > 0 and num_epochs > 0:
            steps_per_epoch = step / current_epoch if current_epoch < num_epochs else step
            total = max(step, round(steps_per_epoch * num_epochs))

    # ── Fallback: tqdm progress bar lines (when tqdm not disabled) ───────────
    # Exclude model/weight loading lines (Loading weights, Loading model, etc.)
    _SKIP_TQDM = re.compile(r"(?i)(loading\s+weight|loading\s+model|loading\s+check|download|fetching|shard)")
    if total == 0:
        for line in reversed(lines):
            if _SKIP_TQDM.search(line):
                continue
            m = re.search(r"(\d+)/(\d+)\s+\[", line)  # tqdm: "1/62 [14:34<..."
            if not m:
                m = re.search(r"[Ss]tep[s]?\s+(\d+)\s*[/of]+\s*(\d+)", line)
            if m:
                step  = max(step, int(m.group(1)))
                total = int(m.group(2))
                break

    # ── Phase label from recent log lines ─────────────────────────────────────
    current_step = "Preparing"
    for line in reversed(lines[-30:]):
        ll = line.lower()
        if "collect" in ll or "gathering" in ll:
            current_step = "Collecting training data"; break
        elif "tokeniz" in ll or "preprocess" in ll:
            current_step = "Preprocessing data"; break
        elif metric_count > 0 or ("train" in ll and ("lora" in ll or "step" in ll)):
            current_step = "Training LoRA adapter"; break
        elif "save" in ll or "export" in ll or "adapter" in ll:
            current_step = "Saving adapter"; break
        elif "gguf" in ll:
            current_step = "Exporting GGUF"; break
    if metric_count > 0:
        current_step = "Training LoRA adapter"

    # ── Progress percentage ────────────────────────────────────────────────────
    if total > 0 and step > 0:
        pct_val = round(step / total * 100)
    elif current_epoch is not None and num_epochs > 0:
        pct_val = round(min(99, current_epoch / num_epochs * 100))
    else:
        pct_val = 0

    done = not running and any(kw in raw for kw in ("Training complete", "Saved adapter", "Done", "adapter_model"))
    eta_minutes = 0
    if running and total > 0 and step > 0:
        eta_minutes = max(1, round((total - step) * 0.5))

    return {
        "is_running":       running,
        "stuck":            stuck,
        "pids":             pids,
        "done":             done,
        "step":             step,
        "total_steps":      total,
        "progress_percent": pct_val,
        "current_step":     current_step,
        "eta_minutes":      eta_minutes,
        "loss":             loss,
        "epoch":            current_epoch,
        "num_epochs":       num_epochs,
        "log_tail":         lines[-25:],
        "log_file":         TRAINING_LOG_PATH,
    }


def _stop_training() -> dict:
    """SIGTERM → 5s wait → SIGKILL all run_training_cycle processes."""
    import time as _time
    r = subprocess.run(["pgrep", "-f", "run_training_cycle"], capture_output=True, text=True)
    pids = [p for p in r.stdout.strip().splitlines() if p]
    if not pids:
        return {"ok": True, "message": "No training process running"}
    for pid in pids:
        subprocess.run(["kill", "-TERM", pid], capture_output=True)
    deadline = _time.time() + 5
    while _time.time() < deadline:
        still = subprocess.run(["pgrep", "-f", "run_training_cycle"],
                               capture_output=True, text=True).stdout.strip().splitlines()
        if not still:
            break
        _time.sleep(0.5)
    still = subprocess.run(["pgrep", "-f", "run_training_cycle"],
                           capture_output=True, text=True).stdout.strip().splitlines()
    killed = []
    for pid in still:
        subprocess.run(["kill", "-KILL", pid], capture_output=True)
        killed.append(pid)
    msg = f"Stopped training PID(s) {', '.join(pids)}"
    if killed:
        msg += f" (SIGKILL: {', '.join(killed)})"
    return {"ok": True, "message": msg}


def _infra_status() -> dict:
    """Ping known services and list Docker containers via Colima."""
    import socket

    SERVICES = [
        {"name": "Ollama",    "host": os.environ.get("OLLAMA_HOST", "127.0.0.1").split(":")[0], "port": 11434, "label": "AI"},
        {"name": "Dashboard", "host": "127.0.0.1",     "port": 8080,  "label": "Dash"},
        {"name": "Sonarr",    "host": "192.168.10.201", "port": 8989,  "label": "TV"},
        {"name": "Radarr",    "host": "192.168.10.201", "port": 7878,  "label": "Movies"},
        {"name": "Prowlarr",  "host": "192.168.10.201", "port": 9696,  "label": "Index"},
        {"name": "Plex",      "host": "192.168.10.201", "port": 32400, "label": "Stream"},
    ]

    services = []
    for svc in SERVICES:
        t0 = time.time()
        up = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.8)
            up = sock.connect_ex((svc["host"], svc["port"])) == 0
            sock.close()
        except Exception:
            up = False
        ms = round((time.time() - t0) * 1000)
        services.append({**svc, "up": up, "latency_ms": ms if up else None})

    # Docker containers via Colima socket
    docker_containers: list = []
    docker_available = False
    try:
        colima_sock = os.path.expanduser("~/.colima/default/docker.sock")
        env = {**os.environ, "DOCKER_HOST": f"unix://{colima_sock}"}
        r = subprocess.run(
            ["docker", "ps", "--format", "{{json .}}"],
            capture_output=True, text=True, timeout=5, env=env,
        )
        if r.returncode == 0:
            docker_available = True
            for line in r.stdout.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    c = json.loads(line)
                    docker_containers.append({
                        "name":   c.get("Names", ""),
                        "status": c.get("Status", ""),
                        "image":  c.get("Image", "").split(":")[0],
                        "ports":  (c.get("Ports", "") or "")[:60],
                    })
                except Exception:
                    pass
    except Exception:
        pass

    return {
        "services":          services,
        "docker_available":  docker_available,
        "docker_containers": docker_containers,
    }


def _home_status() -> dict:
    """Fetch entity states from Home Assistant REST API."""
    ha_url   = os.environ.get("HA_URL", "")
    ha_token = os.environ.get("HA_TOKEN", "")
    if not ha_url:
        return {"available": False, "message": "HA_URL not configured — set HA_URL and HA_TOKEN env vars",
                "entities": [], "entity_count": 0}

    import urllib.request as _req
    import json as _json
    try:
        req = _req.Request(
            f"{ha_url.rstrip('/')}/api/states",
            headers={
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json",
            },
        )
        with _req.urlopen(req, timeout=5) as r:
            states = _json.loads(r.read())

        DOMAINS = {"sensor", "binary_sensor", "light", "switch", "climate",
                   "media_player", "person", "weather", "cover", "lock"}
        entities = []
        for state in states:
            domain = state["entity_id"].split(".")[0]
            if domain not in DOMAINS:
                continue
            attrs = state.get("attributes", {})
            entities.append({
                "entity_id":    state["entity_id"],
                "domain":       domain,
                "name":         attrs.get("friendly_name", state["entity_id"].split(".")[-1]),
                "state":        state["state"],
                "unit":         attrs.get("unit_of_measurement", ""),
                "device_class": attrs.get("device_class", ""),
            })

        return {"available": True, "entity_count": len(states), "entities": entities[:80]}
    except Exception as exc:
        return {"available": False, "message": str(exc), "entities": [], "entity_count": 0}


def _media_status() -> dict:
    """Fetch live stats from the *Arr stack and Plex."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from domains.media import MediaDomain
        domain = MediaDomain()
        return domain.get_stats()
    except Exception as exc:
        return {"error": str(exc), "health": {}}


def _media_recent() -> dict:
    """Recent TV episode downloads + recent movie downloads."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from connectors.arr_stack import ArrStackConnector
        import os
        sonarr = ArrStackConnector("sonarr",
            os.environ.get("SONARR_URL", "http://192.168.10.201:8989"),
            os.environ.get("SONARR_API_KEY", ""))
        radarr = ArrStackConnector("radarr",
            os.environ.get("RADARR_URL", "http://192.168.10.201:7878"),
            os.environ.get("RADARR_API_KEY", ""))
        episodes = sonarr.get_recent_episodes(10) if sonarr.health_check() else []
        movies   = radarr.get_recent_movies(10)   if radarr.health_check() else []
        needs_key = not os.environ.get("SONARR_API_KEY") and not os.environ.get("RADARR_API_KEY")
        return {"episodes": episodes, "movies": movies, "needs_key": needs_key}
    except Exception as exc:
        return {"episodes": [], "movies": [], "error": str(exc)}


def _media_upcoming() -> dict:
    """Upcoming TV episodes for the next 7 days."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from connectors.arr_stack import ArrStackConnector
        import os
        sonarr = ArrStackConnector("sonarr",
            os.environ.get("SONARR_URL", "http://192.168.10.201:8989"),
            os.environ.get("SONARR_API_KEY", ""))
        episodes = sonarr.get_upcoming_episodes(7) if sonarr.health_check() else []
        needs_key = not os.environ.get("SONARR_API_KEY")
        return {"episodes": episodes, "needs_key": needs_key}
    except Exception as exc:
        return {"episodes": [], "error": str(exc)}


def _media_pipeline() -> dict:
    """Full pipeline status: all 6 services with circuit-breaker protection."""
    sys.path.insert(0, str(REPO_ROOT))

    def _fetch_sonarr():
        from connectors.arr_stack import ArrStackConnector
        c = ArrStackConnector("sonarr", os.environ.get("SONARR_URL", "http://192.168.10.201:8989"),
                              os.environ.get("SONARR_API_KEY", ""))
        up = c.health_check()
        if not up:
            raise ConnectionError("sonarr down")
        sc = c.get_series_count()
        return {"series": sc.get("total", 0), "upcoming": 0, "queue": c.get_queue_count(), "up": True}

    def _fetch_radarr():
        from connectors.arr_stack import ArrStackConnector
        c = ArrStackConnector("radarr", os.environ.get("RADARR_URL", "http://192.168.10.201:7878"),
                              os.environ.get("RADARR_API_KEY", ""))
        up = c.health_check()
        if not up:
            raise ConnectionError("radarr down")
        mc = c.get_movie_count()
        return {"movies": mc.get("total", 0), "monitored": mc.get("monitored", 0),
                "downloaded": mc.get("downloaded", 0), "queue": c.get_queue_count(), "up": True}

    def _fetch_prowlarr():
        from connectors.arr_stack import ArrStackConnector
        c = ArrStackConnector("prowlarr", os.environ.get("PROWLARR_URL", "http://192.168.10.201:9696"),
                              os.environ.get("PROWLARR_API_KEY", ""))
        up = c.health_check()
        if not up:
            raise ConnectionError("prowlarr down")
        ic = c.get_indexer_count()
        return {"indexers": ic.get("enabled", 0), "total": ic.get("total", 0), "up": True}

    def _fetch_qnap():
        from connectors.qnap import QNAPConnector
        c = QNAPConnector(os.environ.get("QNAP_URL", "http://192.168.10.201"),
                          os.environ.get("QNAP_USER", "admin"),
                          os.environ.get("QNAP_PASS", ""))
        if not c.health_check():
            raise ConnectionError("qnap down")
        s = c.get_storage_stats()
        if s.get("status") != "connected":
            raise ConnectionError(f"qnap storage: {s.get('status')}")
        return {**s, "up": True}

    sonarr,   cb_s = _breakers["sonarr"].call(_fetch_sonarr,   {"up": False})
    radarr,   cb_r = _breakers["radarr"].call(_fetch_radarr,   {"up": False})
    prowlarr, cb_p = _breakers["prowlarr"].call(_fetch_prowlarr, {"up": False})
    qnap,     cb_q = _breakers["qnap"].call(_fetch_qnap,       {"up": False})

    # Seedbox: runs through circuit breaker; MediaDomain._seedbox_safe() enforces
    # a wall-clock timeout so DNS hangs never block this function.
    def _fetch_seedbox():
        from domains.media import MediaDomain
        sb = MediaDomain()._seedbox_safe(timeout=10.0)
        status = sb.get("status", "unknown")
        if status not in ("connected",):
            raise ConnectionError(f"seedbox {status}: {sb.get('message', '')}")
        return {
            "recent_files": sb.get("recent_files", 0),
            "total_files":  sb.get("total_files", 0),
            "total_gb":     sb.get("total_size_gb", 0),
            "status":       status,
            "up":           True,
        }

    _seedbox_fallback = {"up": False, "status": "offline"}
    seedbox, cb_sb = _breakers["seedbox"].call(_fetch_seedbox, _seedbox_fallback)
    if seedbox is None:
        seedbox = _seedbox_fallback

    # Plex: lightweight health-only check; isolated so seedbox can't drag it down
    plex: dict = {"up": False}
    sonarr_upcoming = 0
    try:
        from domains.media import MediaDomain
        domain = MediaDomain()
        plex_conn = domain._plex()
        plex_up   = plex_conn.health_check()
        if plex_up:
            sessions  = plex_conn.get_active_sessions()
            libraries = plex_conn.get_library_stats()
            plex = {"libraries": len(libraries), "active_streams": len(sessions), "up": True}
        # Sonarr upcoming (non-critical — ignore if it fails)
        if not cb_s and isinstance(sonarr, dict):
            try:
                sonarr_upcoming = len(domain._sonarr().get_calendar(days=7))
            except Exception:
                pass
    except Exception:
        pass

    if not cb_s and isinstance(sonarr, dict):
        sonarr["upcoming"] = sonarr_upcoming

    return {
        "sonarr":   sonarr   or {"up": False},
        "radarr":   radarr   or {"up": False},
        "prowlarr": prowlarr or {"up": False},
        "plex":     plex,
        "seedbox":  seedbox,
        "qnap":     qnap     or {"up": False},
        "_circuit": {
            "sonarr":   "open" if cb_s  else "closed",
            "radarr":   "open" if cb_r  else "closed",
            "prowlarr": "open" if cb_p  else "closed",
            "qnap":     "open" if cb_q  else "closed",
            "seedbox":  "open" if cb_sb else "closed",
        },
    }


def _media_downloads() -> dict:
    """Active seedbox downloads and queue."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from domains.media import MediaDomain
        domain = MediaDomain()
        return domain.get_downloads()
    except Exception as exc:
        return {"status": "error", "error": str(exc), "files": []}


def _seedbox_status() -> dict:
    """Rich seedbox status: active, completed, blackhole, rclone log, Flood."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from domains.media import MediaDomain
        return MediaDomain().get_seedbox_status()
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}


def _seedbox_queue() -> dict:
    """Active torrent list from Flood (if installed), falls back to SFTP file list."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from connectors.flood_api import FloodAPI
        import os as _os
        flood = FloodAPI(url=_os.environ.get("FLOOD_URL", "http://193.163.71.22:3000"))
        if flood.health_check():
            return flood.get_all_status()
        # Flood not available — return active files from SFTP
        from connectors.seedbox import SeedboxConnector
        sb = SeedboxConnector()
        data = sb.get_active_downloads()
        return {
            "status":       data.get("status", "unknown"),
            "source":       "sftp",
            "active_count": data.get("active_count", 0),
            "active":       data.get("active", []),
            "flood_available": False,
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)[:200]}


def _get_arr_connectors():
    from connectors.arr_stack import ArrStackConnector
    sonarr   = ArrStackConnector("sonarr",   os.environ.get("SONARR_URL",   "http://192.168.10.201:8989"), os.environ.get("SONARR_API_KEY",   ""))
    radarr   = ArrStackConnector("radarr",   os.environ.get("RADARR_URL",   "http://192.168.10.201:7878"), os.environ.get("RADARR_API_KEY",   ""))
    prowlarr = ArrStackConnector("prowlarr", os.environ.get("PROWLARR_URL", "http://192.168.10.201:9696"), os.environ.get("PROWLARR_API_KEY", ""))
    return sonarr, radarr, prowlarr


def _get_qnap_connector():
    from connectors.qnap import QNAPConnector
    return QNAPConnector(
        base_url=os.environ.get("QNAP_URL",  "http://192.168.10.201"),
        username=os.environ.get("QNAP_USER", "admin"),
        password=os.environ.get("QNAP_PASS", ""),
    )


def _media_issues() -> dict:
    """Detect problems across the media pipeline."""
    sys.path.insert(0, str(REPO_ROOT))
    issues = []

    try:
        sonarr, radarr, _ = _get_arr_connectors()
        for connector, svc, label in [(sonarr, "sonarr", "TV"), (radarr, "radarr", "Movie")]:
            if not connector.health_check():
                continue
            for item in connector.get_queue_details():
                tracked = item.get("trackedDownloadStatus", "ok")
                status  = item.get("status", "")
                title   = (item.get("title") or "")[:60]
                msgs    = [m.get("message", "") for m in item.get("statusMessages", [])]
                qid     = item.get("id")
                if tracked in ("warning", "error"):
                    issues.append({
                        "severity": "critical" if tracked == "error" else "warning",
                        "service": svc, "type": "download_failed",
                        "message": f"{label} download issue: {title}",
                        "detail": ("; ".join(msgs)[:120] if msgs else tracked),
                        "fix": "retry", "queue_id": qid,
                    })
                elif status == "downloading" and not item.get("timeleft"):
                    issues.append({
                        "severity": "warning", "service": svc, "type": "stalled",
                        "message": f"Possibly stalled: {title}",
                        "detail": "No time remaining reported",
                        "fix": "retry", "queue_id": qid,
                    })
    except Exception as e:
        issues.append({"severity": "info", "service": "arr", "type": "check_error",
                       "message": f"Queue check error: {str(e)[:80]}", "fix": None})

    try:
        qnap = _get_qnap_connector()
        storage = qnap.get_storage_stats()
        if storage.get("status") == "connected":
            pct  = storage.get("used_pct", 0)
            free = storage.get("free_gb", 0)
            if pct >= 90:
                issues.append({"severity": "critical", "service": "qnap", "type": "disk_full",
                               "message": f"QNAP disk {pct}% full — only {free} GB free",
                               "detail": "Delete completed downloads or expand storage", "fix": None})
            elif pct >= 80:
                issues.append({"severity": "warning", "service": "qnap", "type": "disk_high",
                               "message": f"QNAP disk {pct}% used — {free} GB remaining",
                               "detail": "Consider cleaning up soon", "fix": None})
        rclone = qnap.get_rclone_status()
        if rclone.get("status") == "connected":
            ago = rclone.get("last_sync_ago_min")
            if ago is not None and ago > 30 and not rclone.get("rclone_running"):
                issues.append({"severity": "warning", "service": "rclone", "type": "sync_stale",
                               "message": f"rclone hasn't synced in {ago} min",
                               "detail": "Sync may be stuck or not scheduled", "fix": "force_sync"})
    except Exception as e:
        issues.append({"severity": "info", "service": "qnap", "type": "check_error",
                       "message": f"QNAP check error: {str(e)[:80]}", "fix": None})

    critical = sum(1 for i in issues if i["severity"] == "critical")
    warnings = sum(1 for i in issues if i["severity"] == "warning")
    return {"issues": issues, "count": len(issues), "critical": critical, "warnings": warnings}


def _media_missing() -> dict:
    """Missing monitored episodes and movies."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        sonarr, radarr, _ = _get_arr_connectors()
        eps, ep_total = sonarr.get_missing_episodes(50) if sonarr.health_check() else ([], 0)
        mvs, mv_total = radarr.get_missing_movies(50)   if radarr.health_check() else ([], 0)
        return {"episodes": eps, "episodes_total": ep_total,
                "movies": mvs, "movies_total": mv_total}
    except Exception as exc:
        return {"episodes": [], "movies": [], "error": str(exc)}


def _media_queue_details() -> dict:
    """Detailed queue from Sonarr + Radarr with error detection."""
    sys.path.insert(0, str(REPO_ROOT))
    try:
        sonarr, radarr, _ = _get_arr_connectors()

        def fmt(connector, svc):
            return [{
                "id":          item.get("id"),
                "service":     svc,
                "title":       (item.get("title") or "")[:70],
                "status":      item.get("status", ""),
                "tracked":     item.get("trackedDownloadStatus", "ok"),
                "size_gb":     round((item.get("size") or 0) / (1024**3), 2),
                "sizeleft_gb": round((item.get("sizeleft") or 0) / (1024**3), 2),
                "timeleft":    item.get("timeleft") or "",
                "protocol":    item.get("protocol", ""),
                "error":       item.get("trackedDownloadStatus", "ok") in ("warning", "error"),
                "messages":    [m.get("message","") for m in item.get("statusMessages", [])],
            } for item in connector.get_queue_details()]

        tv     = fmt(sonarr, "sonarr") if sonarr.health_check() else []
        movies = fmt(radarr, "radarr") if radarr.health_check() else []
        all_q  = tv + movies
        return {"tv": tv, "movies": movies, "total": len(all_q),
                "errors": sum(1 for i in all_q if i["error"])}
    except Exception as exc:
        return {"tv": [], "movies": [], "error": str(exc)}


def _media_rclone_status() -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        return _get_qnap_connector().get_rclone_status()
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _media_search_missing(body: dict) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        sonarr, radarr, _ = _get_arr_connectors()
        service   = body.get("service", "sonarr")
        ids       = body.get("ids", [])
        connector = sonarr if service == "sonarr" else radarr
        if not connector.health_check():
            return {"ok": False, "message": f"{service} offline"}
        if ids:
            ok = connector.search_by_ids(ids)
        else:
            ok = connector.search_missing_all()
        return {"ok": ok, "message": ("Search triggered" if ok else "Failed to trigger search")}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _media_force_sync() -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        return _get_qnap_connector().force_rclone_sync()
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _media_queue_remove(body: dict) -> dict:
    sys.path.insert(0, str(REPO_ROOT))
    try:
        sonarr, radarr, _ = _get_arr_connectors()
        service   = body.get("service", "sonarr")
        queue_id  = int(body.get("queue_id", 0))
        blacklist = bool(body.get("blacklist", False))
        if not queue_id:
            return {"ok": False, "message": "No queue_id provided"}
        connector = sonarr if service == "sonarr" else radarr
        ok = connector.remove_from_queue(queue_id, blacklist=blacklist)
        return {"ok": ok, "message": "Removed" if ok else "Failed to remove"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def _audit_events() -> dict:
    from framework.audit_log import tail, stats
    return {"events": tail(100), "stats_24h": stats()}


def _circuit_breaker_status() -> dict:
    return {
        "breakers": [cb.info() for cb in _breakers.values()],
        "summary": {
            "open":      sum(1 for cb in _breakers.values() if cb._state == "open"),
            "half_open": sum(1 for cb in _breakers.values() if cb._state == "half-open"),
            "closed":    sum(1 for cb in _breakers.values() if cb._state == "closed"),
        },
    }


def _system_stats() -> dict:
    from connectors.system_monitor import get_mac_stats, get_ollama_stats
    mac    = get_mac_stats()
    ollama = get_ollama_stats()
    return {"mac": mac, "ollama": ollama}


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


def _roadmap_search(query: str, max_results: int = 10) -> list[dict]:
    """Search roadmap items by text (title, id, category, description)."""
    if not ITEMS_DIR.exists():
        return []
    q = query.lower().strip()
    if not q:
        return []
    results = []
    for md in sorted(ITEMS_DIR.glob("*.md")):
        text = md.read_text()
        if q in text.lower():
            id_m    = re.search(r"\*\*ID:\*\*\s*`([^`]+)`", text)
            title_m = re.search(r"\*\*Title:\*\*\s*(.+)", text)
            cat_m   = re.search(r"\*\*Category:\*\*\s*`([^`]+)`", text)
            stat_m  = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
            loe_m   = re.search(r"\*\*LOE:\*\*\s*`([^`]+)`", text)
            item_id  = id_m.group(1) if id_m else md.stem
            results.append({
                "id":       item_id,
                "title":    (title_m.group(1).strip() if title_m else item_id)[:80],
                "category": cat_m.group(1) if cat_m else "?",
                "status":   stat_m.group(1) if stat_m else "?",
                "loe":      loe_m.group(1) if loe_m else "M",
            })
            if len(results) >= max_results:
                break
    return results


def _roadmap_item_detail(item_id: str) -> dict | None:
    """Get full detail of a roadmap item by ID."""
    if not ITEMS_DIR.exists():
        return None
    # Try exact filename match first, then search
    candidates = list(ITEMS_DIR.glob(f"{item_id}.md"))
    if not candidates:
        candidates = [md for md in ITEMS_DIR.glob("*.md") if item_id in md.stem]
    if not candidates:
        return None
    md = candidates[0]
    text = md.read_text()
    id_m    = re.search(r"\*\*ID:\*\*\s*`([^`]+)`", text)
    title_m = re.search(r"\*\*Title:\*\*\s*(.+)", text)
    cat_m   = re.search(r"\*\*Category:\*\*\s*`([^`]+)`", text)
    stat_m  = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
    loe_m   = re.search(r"\*\*LOE:\*\*\s*`([^`]+)`", text)
    pri_m   = re.search(r"\*\*Priority class:\*\*\s*`([^`]+)`", text)
    risk_m  = re.search(r"\*\*Execution risk:\*\*\s*`?(\d+)`?", text)
    desc_m  = re.search(r"## Description\s*\n+(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return {
        "id":          id_m.group(1) if id_m else md.stem,
        "title":       title_m.group(1).strip() if title_m else "",
        "category":    cat_m.group(1) if cat_m else "",
        "status":      stat_m.group(1) if stat_m else "",
        "loe":         loe_m.group(1) if loe_m else "",
        "priority":    pri_m.group(1) if pri_m else "",
        "risk":        risk_m.group(1) if risk_m else "",
        "description": desc_m.group(1).strip()[:800] if desc_m else "",
        "file":        str(md),
        "raw":         text[:2000],
    }


def _roadmap_move(item_id: str, new_status: str) -> dict:
    """Change the status field of a roadmap item and commit."""
    VALID = {"Pending", "Accepted", "In progress", "Completed"}
    if new_status not in VALID:
        return {"ok": False, "message": f"Invalid status '{new_status}'"}
    if not ITEMS_DIR.exists():
        return {"ok": False, "message": "Items directory not found"}
    candidates = list(ITEMS_DIR.glob(f"{item_id}.md"))
    if not candidates:
        candidates = [md for md in ITEMS_DIR.glob("*.md") if item_id in md.stem]
    if not candidates:
        return {"ok": False, "message": f"Item {item_id} not found"}
    md = candidates[0]
    text = md.read_text()
    old_m = re.search(r"\*\*Status:\*\*\s*`([^`]+)`", text)
    if not old_m:
        return {"ok": False, "message": "No Status field found"}
    old_status = old_m.group(1)
    new_text = re.sub(r"(\*\*Status:\*\*\s*)`[^`]+`", f"\\1`{new_status}`", text)
    md.write_text(new_text)
    try:
        subprocess.run(["git", "add", str(md)], capture_output=True, cwd=REPO_ROOT)
        subprocess.run(["git", "commit", "-m", f"status: {item_id} to {new_status}"],
                       capture_output=True, cwd=REPO_ROOT)
    except Exception:
        pass
    return {"ok": True, "id": item_id, "old_status": old_status, "new_status": new_status,
            "message": f"{item_id}: {old_status} to {new_status}"}


def _dev_generate(data: dict) -> dict:
    """Generate code (+ optional tests/docs) via Ollama."""
    import urllib.request as _req
    import json as _json

    prompt = data.get("prompt", "").strip()
    if not prompt:
        return {"error": "No prompt provided", "code": "", "tests": "", "docs": ""}

    engine     = data.get("engine", "claude")
    do_tests   = data.get("create_tests", True)
    do_docs    = data.get("add_docs", True)
    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    model      = os.environ.get("OLLAMA_CODE_MODEL", os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:14b"))

    system = (
        "You are an expert Python developer. "
        "Return ONLY valid JSON with keys: code (string), tests (string or null), docs (string or null). "
        "No markdown fences, no commentary outside the JSON object."
    )
    parts = [f"Task: {prompt}"]
    if do_tests:
        parts.append("Include pytest unit tests in the 'tests' field.")
    if do_docs:
        parts.append("Include a module docstring and usage example in the 'docs' field.")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n".join(parts)},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "num_predict": 2048},
    }
    try:
        req = _req.Request(
            f"{ollama_url}/api/chat",
            data=_json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        with _req.urlopen(req, timeout=90) as resp:
            raw = _json.loads(resp.read())
        content = raw.get("message", {}).get("content", "")
        try:
            result = _json.loads(content)
        except Exception:
            result = {"code": content, "tests": None, "docs": None}
        return {
            "engine": engine,
            "code":  result.get("code",  "") or "",
            "tests": result.get("tests", "") if do_tests else "",
            "docs":  result.get("docs",  "") if do_docs  else "",
        }
    except Exception as exc:
        return {"error": str(exc)[:200], "code": "", "tests": "", "docs": ""}


def _dev_apply(data: dict) -> dict:
    """Save generated code to artifacts/dev_generated/ for review."""
    import time as _time
    code  = data.get("code",  "").strip()
    tests = data.get("tests", "").strip()
    docs  = data.get("docs",  "").strip()
    if not code:
        return {"error": "No code to apply", "message": ""}

    out_dir = Path(__file__).parent.parent / "artifacts" / "dev_generated"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = _time.strftime("%Y%m%d_%H%M%S")
    (out_dir / f"generated_{ts}.py").write_text(code)
    if tests:
        (out_dir / f"test_generated_{ts}.py").write_text(tests)
    if docs:
        (out_dir / f"docs_generated_{ts}.md").write_text(docs)
    return {"message": f"Saved to artifacts/dev_generated/generated_{ts}.py"}


def _dev_status() -> dict:
    """Quick status check for AI coding engines."""
    import shutil as _shutil
    import urllib.request as _req
    import json as _json

    ollama_url = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
    ollama_ok = False
    try:
        with _req.urlopen(f"{ollama_url}/api/tags", timeout=3) as r:
            d = _json.loads(r.read())
            ollama_ok = isinstance(d.get("models"), list)
    except Exception:
        pass

    aider_ok  = bool(_shutil.which("aider"))
    codex_ok  = bool(_shutil.which("codex"))
    return {
        "engines": {
            "aider":  {"available": aider_ok,  "note": "local CLI" if aider_ok else "not installed"},
            "codex":  {"available": codex_ok,  "note": "local CLI" if codex_ok else "not installed"},
            "claude": {"available": ollama_ok, "note": "via Ollama" if ollama_ok else "Ollama not reachable"},
        },
        "ollama_url": ollama_url,
    }


def _roadmap_ai_generate(data: dict) -> dict:
    """Translate natural language into a structured roadmap item via Ollama."""
    description = data.get("description", "").strip()
    if not description:
        return {"error": "No description provided"}
    try:
        sys.path.insert(0, str(REPO_ROOT / "bin"))
        from ai_requirement_translator import translate_requirement, _next_id  # type: ignore
        item = translate_requirement(description)
        item["id"] = _next_id(item.get("category", "UTIL"))
        # Normalise field names for the frontend
        if "success_criteria" in item and "acceptance_criteria" not in item:
            item["acceptance_criteria"] = item.pop("success_criteria")
        item.setdefault("acceptance_criteria", [])
        item.setdefault("dependencies", [])
        return item
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _roadmap_create_in_plane(data: dict) -> dict:
    """Create a roadmap item in Plane and write a markdown backup."""
    try:
        from framework.plane_connector import PlaneAPI
        api = PlaneAPI()
        if not api.health_check():
            return {"success": False, "error": "Plane not reachable"}
        title    = data.get("title", "Untitled")
        desc     = data.get("description", "")
        category = data.get("category", "UTIL")
        loe      = data.get("loe", "M")
        criteria = data.get("acceptance_criteria", [])
        full_desc = desc
        if criteria:
            crit_lines = "\n".join(f"- {c}" for c in criteria if c)
            full_desc += f"\n\n## Acceptance Criteria\n{crit_lines}"
        priority_map = {
            "urgent": "urgent", "high": "high", "medium": "medium", "low": "low",
            "P0-Critical": "urgent", "P1-High": "high", "P2-Medium": "medium", "P3-Low": "low",
        }
        priority = priority_map.get(data.get("priority", "medium"), "medium")
        issue, created = api.upsert_issue(
            external_id=data.get("id", ""),
            title=title,
            description=full_desc,
            state_name="Backlog",
            category=category,
            priority=priority,
        )
        plane_id = issue.get("id", "") if isinstance(issue, dict) else ""
        _roadmap_create(data)
        return {"success": True, "plane_id": plane_id, "id": data.get("id", ""), "created": created}
    except Exception as exc:
        return {"success": False, "error": str(exc)[:200]}


# ── Network monitoring helpers ────────────────────────────────────────────────

def _network_topology(force: bool = False) -> dict:
    """Return cached network topology (runs nmap or ping sweep)."""
    try:
        from framework.network_scanner import get_scanner
        return get_scanner().scan(force=force)
    except Exception as exc:
        return {"error": str(exc)[:200], "nodes": [], "edges": []}


def _network_opnsense() -> dict:
    """OPNsense firewall summary — returns empty dict if not configured."""
    try:
        from framework.opnsense_client import OPNsenseClient
        api_key = os.environ.get("OPNSENSE_API_KEY", "")
        if not api_key:
            return {"configured": False}
        return {**OPNsenseClient.from_env().summary(), "configured": True}
    except Exception as exc:
        return {"configured": True, "error": str(exc)[:200]}


def _network_qnap() -> dict:
    """QNAP NAS summary — returns empty dict if not configured."""
    try:
        from framework.qnap_client import QNAPClient
        if not os.environ.get("QNAP_PASSWORD"):
            return {"configured": False}
        return {**QNAPClient.from_env().summary(), "configured": True}
    except Exception as exc:
        return {"configured": True, "error": str(exc)[:200]}


def _network_isp() -> dict:
    """ISP / latency monitor status."""
    try:
        from domains.isp_monitor import get_monitor
        mon = get_monitor()
        if not mon._running:
            mon.start()
        return mon.status()
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _network_isp_history() -> dict:
    """Recent ISP latency history (last 60 samples)."""
    try:
        from domains.isp_monitor import get_monitor
        return {"history": get_monitor().recent_history(60)}
    except Exception as exc:
        return {"error": str(exc)[:200], "history": []}


def _network_overview() -> dict:
    """Fast aggregated network status for the tab header."""
    topo = _cached("net_topo", _network_topology, 300)[0]
    isp  = _cached("net_isp",  _network_isp,      60)[0]
    return {
        "hosts_alive": topo.get("alive", 0),
        "hosts_total": topo.get("total", 0),
        "internet_up": isp.get("internet_up", None),
        "gateway_rtt": isp.get("gateway_rtt_ms"),
        "external_rtt": isp.get("external_rtt_ms"),
        "subnet": topo.get("subnet", "192.168.10.0/24"),
    }


def _roadmap_scan() -> dict:
    """Scan all RM-*.md files in the repo and return deduplication report."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "bin"))
        from scan_all_roadmap_docs import scan_roadmap_docs_api  # type: ignore
        return scan_roadmap_docs_api()
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _roadmap_import(data: dict) -> dict:
    """Bulk-import a list of roadmap items into Plane, skipping already-existing IDs."""
    items = data.get("items", [])
    if not items:
        return {"error": "No items provided", "imported": 0, "skipped": 0}
    try:
        from framework.plane_connector import PlaneAPI
        api = PlaneAPI()
        if not api.health_check():
            return {"error": "Plane not reachable", "imported": 0, "skipped": 0}

        # Build set of already-known external IDs (from name prefix [RM-XXX])
        known: set[str] = set()
        cursor: str | None = None
        while True:
            batch, cursor = api.list_issues(cursor=cursor, page_size=100)
            for iss in batch:
                name = iss.get("name", "")
                import re as _re
                m = _re.match(r"^\[(RM-[A-Z][A-Z0-9-]*-\d+)\]", name)
                if m:
                    known.add(m.group(1))
            if not cursor:
                break

        imported = skipped = errors = 0
        for item in items:
            item_id = item.get("id", "")
            if item_id in known:
                skipped += 1
                continue
            try:
                priority_map = {
                    "urgent": "urgent", "high": "high", "medium": "medium",
                    "low": "low", "p0": "urgent", "p1": "high", "p2": "medium", "p3": "low",
                }
                priority = priority_map.get(item.get("priority", "medium").lower(), "medium")
                api.upsert_issue(
                    external_id=item_id,
                    title=item.get("title", item_id),
                    description=item.get("description", ""),
                    state_name=item.get("status", "Backlog"),
                    category=item.get("category", "UTIL"),
                    priority=priority,
                )
                imported += 1
                known.add(item_id)
                time.sleep(0.25)
            except Exception as exc:
                errors += 1
                if errors > 10:
                    break  # stop hammering on repeated failures

        fast = api.get_stats_fast()
        return {
            "imported":       imported,
            "skipped":        skipped,
            "errors":         errors,
            "total_in_plane": fast.get("total", 0),
        }
    except Exception as exc:
        return {"error": str(exc)[:200], "imported": 0, "skipped": 0}


def _roadmap_decompose(data: dict) -> dict:
    """Decompose a roadmap item into subtasks and enqueue the plan."""
    item = data.get("item")
    if not item:
        return {"error": "No item provided"}
    enqueue = data.get("enqueue", False)
    try:
        from domains.task_decomposer import TaskDecomposer
        td = TaskDecomposer()
        plan = td.create_execution_plan(item)
        result: dict = {"plan": plan, "enqueued": False, "task_ids": []}
        if enqueue:
            from framework.execution_queue import get_queue
            q = get_queue()
            task_ids = q.enqueue_plan(plan, priority=item.get("priority", "medium"))
            result["enqueued"] = True
            result["task_ids"] = task_ids
        return result
    except Exception as exc:
        return {"error": str(exc)[:300]}


def _execution_claim_next(data: dict) -> dict:
    """Claim the next pending task from the execution queue."""
    engine = data.get("engine", "claude")
    try:
        from framework.execution_queue import get_queue
        task = get_queue().claim_next_task(engine)
        return {"task": task}
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _execution_complete(data: dict) -> dict:
    """Mark a claimed task as complete or failed."""
    task_id = data.get("task_id")
    if not task_id:
        return {"error": "task_id required"}
    success = bool(data.get("success", True))
    try:
        from framework.execution_queue import get_queue
        updated = get_queue().complete_task(
            task_id,
            success=success,
            result=data.get("result"),
            error=data.get("error"),
        )
        return {"updated": updated}
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _execution_queue_status() -> dict:
    """Return current queue counts and recent task list."""
    try:
        from framework.execution_queue import get_queue
        return get_queue().get_queue_status()
    except Exception as exc:
        return {"error": str(exc)[:200], "pending": 0, "claimed": 0, "done": 0, "failed": 0}


def _aider_worker_status() -> dict:
    try:
        from bin.aider_worker import get_status
        return get_status()
    except Exception as exc:
        return {"error": str(exc)[:200]}


def _docker_containers() -> list:
    try:
        from domains.docker_monitor import get_monitor
        return get_monitor().get_all_containers()
    except Exception as exc:
        return [{"error": str(exc)[:200]}]


def _docker_security() -> dict:
    try:
        from domains.docker_monitor import get_monitor
        return get_monitor().get_security_posture()
    except Exception as exc:
        return {"error": str(exc)[:200], "score": 0, "issues": []}


def _docker_snapshot() -> dict:
    try:
        from domains.docker_monitor import get_monitor
        return get_monitor().get_snapshot()
    except Exception as exc:
        return {"error": str(exc)[:200], "containers": [], "summary": {}}


def _zabbix_status() -> dict:
    """Check if Zabbix web UI is reachable on :10080."""
    import urllib.request as _urllib_req
    try:
        req = _urllib_req.Request(
            "http://localhost:10080/",
            headers={"User-Agent": "dashboard-healthcheck/1.0"},
            method="GET",
        )
        with _urllib_req.urlopen(req, timeout=4) as r:
            reachable = r.status in (200, 302, 301)
        return {"reachable": reachable, "url": "http://localhost:10080"}
    except Exception as exc:
        return {"reachable": False, "url": "http://localhost:10080", "error": str(exc)[:120]}


def _aider_worker_trigger() -> dict:
    try:
        from bin.aider_worker import get_worker
        msg = get_worker().trigger_now()
        return {"ok": True, "message": msg}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def _roadmap_create(data: dict) -> dict:
    """Create a new roadmap item markdown file."""
    if not ITEMS_DIR.exists():
        return {"ok": False, "message": "Items directory not found"}
    cat = re.sub(r"[^A-Z0-9]", "", data.get("category", "UTIL").upper()) or "UTIL"
    prefix = f"RM-{cat}"
    existing_nums = []
    for f in ITEMS_DIR.glob(f"{prefix}-*.md"):
        m = re.search(r"-(\d+)\.md$", f.name)
        if m:
            existing_nums.append(int(m.group(1)))
    next_num = max(existing_nums, default=0) + 1
    item_id = f"{prefix}-{next_num:03d}"
    title       = data.get("title", "Untitled").strip()
    description = data.get("description", "").strip()
    loe         = data.get("loe", "M")
    status      = data.get("status", "Pending")
    content = (
        f"# {item_id}: {title}\n\n"
        f"- **ID:** `{item_id}`\n"
        f"- **Title:** {title}\n"
        f"- **Category:** `{cat}`\n"
        f"- **Type:** `Feature`\n"
        f"- **Status:** `{status}`\n"
        f"- **LOE:** `{loe}`\n"
        f"- **Execution risk:** `2`\n"
        f"- **Priority class:** `P3`\n"
        f"- **Readiness:** `immediate`\n\n"
        f"## Description\n\n"
        f"{description or 'No description provided.'}\n\n"
        f"## Acceptance Criteria\n\n"
        f"- Implementation complete and tested\n"
        f"- Committed to main branch\n"
    )
    out_path = ITEMS_DIR / f"{item_id}.md"
    out_path.write_text(content)
    try:
        subprocess.run(["git", "add", str(out_path)], capture_output=True, cwd=REPO_ROOT)
        subprocess.run(["git", "commit", "-m", f"Add {item_id}: {title}"],
                       capture_output=True, cwd=REPO_ROOT)
    except Exception:
        pass
    return {"ok": True, "id": item_id, "title": title, "status": status, "category": cat}


def _chat_message(message: str, context: dict | None = None) -> dict:
    """Route chat message to appropriate handler. Falls back to Ollama."""
    import urllib.request as _req
    import json as _json

    msg_lower = message.lower().strip()

    # Intent: roadmap search
    if any(kw in msg_lower for kw in ('search', 'find', 'look for', 'show items', 'roadmap item')):
        q = re.sub(r'\b(search|find|look for|show items?|roadmap items?|in roadmap|items? (for|about|with))\b', '',
                   message, flags=re.IGNORECASE).strip()
        q = q or message
        results = _roadmap_search(q)
        if results:
            lines = '\n'.join(f"- **{r['id']}** [{r['status']}]: {r['title']}" for r in results)
            return {"type": "roadmap_search", "text": f"Found **{len(results)}** item(s):\n\n{lines}",
                    "results": results}
        return {"type": "roadmap_search", "text": f"No items found matching '{q}'.", "results": []}

    # Intent: system status
    if any(kw in msg_lower for kw in ('status', 'how many', 'completed', 'progress', 'running', 'stats')):
        rm   = _roadmap_stats()
        ex   = _executor_live_status()
        sys_h = _system_health()
        run_icon = "online" if ex.get("running") else "idle"
        ol_icon  = "online" if sys_h.get("ollama_available") else "offline"
        cur = f" -- {ex.get('current_item')}" if ex.get("current_item") else ""
        text = (
            f"**System Status:**\n"
            f"- Roadmap: **{rm['completed']}/{rm['total']}** completed, "
            f"{rm['in_progress']} in progress, {rm['accepted']} accepted\n"
            f"- Executor: **{run_icon}**{cur}\n"
            f"- Ollama: **{ol_icon}**\n"
            f"- CPU: {sys_h.get('cpu_pct', 0)}%  "
            f"RAM: {sys_h.get('ram_used_pct', 0)}%  "
            f"Disk: {sys_h.get('disk_free_gb', '?')}GB free"
        )
        return {"type": "status", "text": text}

    # Intent: executor control
    if 'start executor' in msg_lower or ('start' in msg_lower and 'executor' in msg_lower):
        r = _executor_action('start', {})
        return {"type": "action", "text": f"{'OK' if r['ok'] else 'FAIL'} {r['message']}"}
    if 'stop executor' in msg_lower or ('stop' in msg_lower and 'executor' in msg_lower):
        r = _executor_action('stop', {})
        return {"type": "action", "text": f"{'OK' if r['ok'] else 'FAIL'} {r['message']}"}

    # Intent: create item
    if any(kw in msg_lower for kw in ('create item', 'add item', 'new item', 'new task',
                                       'add to roadmap', 'create task')):
        return {
            "type": "create_prompt",
            "text": (
                "I can create a roadmap item. Use the **+ New Item** button in the Roadmap tab, "
                "or tell me:\n- **Title**: What's the task?\n"
                "- **Category**: (MEDIA, AI, UTIL, TEST, SECURITY...)\n"
                "- **Description**: What should be built?"
            ),
        }

    # Default: Ollama
    ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1:11434")
    try:
        payload = _json.dumps({
            "model": "qwen2.5-coder:14b",
            "prompt": (
                "You are an AI assistant for an integrated AI development platform. "
                "The platform manages 600 roadmap items, an autonomous executor, "
                "local Ollama models (qwen2.5-coder), "
                "a media pipeline (Sonarr/Radarr/Plex), and a LoRA fine-tuning system. "
                "Be concise and helpful. Format with markdown.\n\n"
                f"User: {message}\n\nAssistant:"
            ),
            "stream": False,
            "options": {"num_predict": 400, "temperature": 0.7},
        }).encode()
        req = _req.Request(
            f"http://{ollama_host}/api/generate",
            data=payload, headers={"Content-Type": "application/json"},
        )
        with _req.urlopen(req, timeout=30) as r:
            resp = _json.loads(r.read())
            return {"type": "ollama", "text": resp.get("response", "").strip()}
    except Exception as exc:
        return {
            "type": "fallback",
            "text": (
                "**I can help you:**\n"
                "- Search: *'find image enhancement items'*\n"
                "- Status: *'how many items completed?'*\n"
                "- Control: *'start executor'*, *'stop executor'*\n"
                "- Create: *'create item for video processing'*\n\n"
                f"*(Ollama offline: {str(exc)[:50]})*"
            ),
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
        "categories": _category_stats(),
    }


def _health() -> dict:
    return {
        "status": "ok",
        "service": "ai-platform-dashboard",
        "version": "1.0.0",
        "ts": time.time(),
        "repo_root": str(REPO_ROOT),
        "executor_host": EXECUTOR_HOST or "local",
    }


def _embed_widget() -> dict:
    """Compact stats payload for Homepage/Homarr widget integration."""
    roadmap = _roadmap_stats()
    exec_status = _executor_live_status()
    system = _system_health()
    total = roadmap.get("total", 0)
    done = roadmap.get("completed", 0) + roadmap.get("accepted", 0)
    success_rate = round(done / total * 100) if total else 0
    return {
        "completions": roadmap.get("completed", 0),
        "accepted": roadmap.get("accepted", 0),
        "in_progress": roadmap.get("in_progress", 0),
        "pending": roadmap.get("pending", 0),
        "total": total,
        "success_rate": success_rate,
        "executor_running": exec_status.get("running", False),
        "current_item": exec_status.get("current_item", ""),
        "ollama_available": system.get("ollama_available", False),
        "cpu_pct": system.get("cpu_pct", 0),
        "ram_used_pct": system.get("ram_used_pct", 0),
    }


# ── Analytics / metrics endpoints ────────────────────────────────────────────

def _analytics_dependencies() -> dict:
    """Dependency graph data from dependency_analyzer."""
    try:
        from domains.dependency_analyzer import DependencyAnalyzer
        da = DependencyAnalyzer(str(ITEMS_DIR))
        da.load_items()
        da.build_graph()
        return {
            "graph": da.to_d3_json(),
            "unblocked": da.get_unblocked_items(),
            "critical_path": da.find_critical_path(),
            "bottlenecks": da.find_bottlenecks(),
            "stats": {"total": len(da._nodes), "with_deps": sum(1 for n in da._nodes.values() if n.dependencies)}
        }
    except Exception as e:
        return {"error": str(e), "graph": {"nodes": [], "links": []}}

def _analytics_effort() -> dict:
    """Effort velocity and sprint forecast from effort_predictor."""
    try:
        from domains.effort_predictor import EffortPredictor
        ep = EffortPredictor()
        return {
            "velocity_trend": ep.get_velocity_trend(),
            "sprint_capacity": ep.get_sprint_capacity("current").to_dict() if hasattr(ep.get_sprint_capacity("current"), "to_dict") else {},
        }
    except Exception as e:
        return {"error": str(e)}

def _analytics_priorities() -> dict:
    """Priority rankings from priority_engine."""
    try:
        from domains.priority_engine import PriorityEngine, PriorityScore
        import dataclasses
        pe = PriorityEngine(items_dir=str(ITEMS_DIR))
        pe.load_items()
        ranked = pe.rank_all()[:100]
        quick_wins = pe.get_quick_wins(limit=20)
        return {
            "ranked": [dataclasses.asdict(s) for s in ranked],
            "quick_wins": [dataclasses.asdict(s) for s in quick_wins],
        }
    except Exception as e:
        return {"error": str(e)}

def _analytics_progress() -> dict:
    """Progress analytics and burndown from progress_analytics."""
    try:
        from domains.progress_analytics import ProgressAnalytics
        pa = ProgressAnalytics(str(ITEMS_DIR))
        pa.load_completion_history()
        return {
            "dashboard": pa.to_dashboard_data(),
            "burndown": pa.get_burndown(),
            "velocity_trend": pa.get_velocity_trend(),
            "forecast": pa.forecast_completion(),
        }
    except Exception as e:
        return {"error": str(e)}

def _media_quality_scores() -> dict:
    """Quality scores from quality_analyzer."""
    try:
        from domains.quality_analyzer import QualityAnalyzer
        qa = QualityAnalyzer()
        return qa.get_library_summary()
    except Exception as e:
        return {"error": str(e), "profiles": []}

def _media_bandwidth_data() -> dict:
    """Bandwidth stats from bandwidth_manager."""
    try:
        from domains.bandwidth_manager import BandwidthManager
        bm = BandwidthManager()
        return {
            "current_mbps": bm.get_current_usage_mbps(),
            "limit_mbps": bm.get_current_limit(),
            "throttle_params": bm.get_throttle_params(),
            "should_throttle": bm.should_throttle(),
            "is_business_hours": bm.is_business_hours(),
        }
    except Exception as e:
        return {"error": str(e)}

def _media_recommendations_ai() -> dict:
    """AI-powered content recommendations from content_recommender."""
    try:
        from domains.content_recommender import ContentRecommender
        cr = ContentRecommender()
        return {"recommendations": cr.get_recommendations(limit=20)}
    except Exception as e:
        return {"error": str(e), "recommendations": []}

def _training_viz_data() -> dict:
    """Training visualization data from training_viz."""
    try:
        from domains.training_viz import TrainingViz
        tv = TrainingViz()
        return tv.get_dashboard_payload()
    except Exception as e:
        return {"error": str(e)}

def _system_metrics_data() -> dict:
    """Prometheus-format metrics from metrics_system."""
    try:
        from framework.metrics_system import MetricsRegistry
        reg = MetricsRegistry.instance()
        metrics_out = {}
        for name, m in reg._metrics.items():
            if hasattr(m, 'get'):
                metrics_out[name] = m.get()
            elif hasattr(m, '_value'):
                metrics_out[name] = m._value
        return {
            "metrics": metrics_out,
            "prometheus": reg.to_prometheus_text(),
        }
    except Exception as e:
        return {"error": str(e), "metrics": {}}


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
        elif path == "/api/velocity":
            self._serve_json(_velocity_stats())
        elif path == "/api/infra/status":
            d, from_cache, age = _cached("infra_status", _infra_status)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/home/status":
            self._serve_json(_home_status())
        elif path == "/api/health":
            self._serve_json(_health())
        elif path == "/api/embed/widget":
            self._serve_json(_embed_widget())
        elif path == "/api/media/status":
            self._serve_json(_media_status())
        elif path == "/api/media/pipeline":
            d, from_cache, age = _cached("media_pipeline", _media_pipeline)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/recent":
            d, from_cache, age = _cached("media_recent", _media_recent)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/recent-additions":
            d, from_cache, age = _cached("media_recent", _media_recent)
            self._serve_json(d)
        elif path == "/api/media/upcoming":
            d, from_cache, age = _cached("media_upcoming", _media_upcoming)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/downloads":
            d, from_cache, age = _cached("media_downloads", _media_downloads)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/seedbox/status":
            d, from_cache, age = _cached("seedbox_status", _seedbox_status)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/seedbox/queue":
            d, from_cache, age = _cached("seedbox_queue", _seedbox_queue)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/issues":
            d, from_cache, age = _cached("media_issues", _media_issues)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/missing":
            d, from_cache, age = _cached("media_missing", _media_missing)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/queue":
            d, from_cache, age = _cached("media_queue", _media_queue_details)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/rclone-status":
            d, from_cache, age = _cached("media_rclone", _media_rclone_status)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/audit/events":
            self._serve_json(_audit_events())
        elif path == "/api/circuit-breakers":
            self._serve_json(_circuit_breaker_status())
        elif path == "/api/system/stats":
            d, from_cache, age = _cached("system_stats", _system_stats)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/selfheal/status":
            d, from_cache, age = _cached("selfheal_status", _selfheal_status)
            self._serve_json(d)
        elif path == "/api/selfheal/config":
            self._serve_json(_selfheal_config())
        elif path == "/api/roadmap/search":
            from urllib.parse import parse_qs, urlparse as _up
            qs = parse_qs(_up(self.path).query)
            q = qs.get("q", [""])[0]
            self._serve_json({"results": _roadmap_search(q)})
        elif path.startswith("/api/roadmap/item/"):
            item_id = path[len("/api/roadmap/item/"):]
            detail = _roadmap_item_detail(item_id)
            self._serve_json(detail if detail else {"error": "not found"})
        elif path == "/api/plane/status":
            self._serve_json(_plane_status())
        elif path == "/api/plane/stats":
            d, from_cache, age = _cached("plane_stats", _plane_stats, ttl=30)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/analytics/dependencies":
            d, from_cache, age = _cached("analytics_deps", _analytics_dependencies, ttl=120)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/analytics/effort":
            d, from_cache, age = _cached("analytics_effort", _analytics_effort, ttl=300)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/analytics/priorities":
            d, from_cache, age = _cached("analytics_priorities", _analytics_priorities, ttl=120)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/analytics/progress":
            d, from_cache, age = _cached("analytics_progress", _analytics_progress, ttl=60)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/quality-scores":
            d, from_cache, age = _cached("media_quality", _media_quality_scores, ttl=300)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/media/bandwidth":
            self._serve_json(_media_bandwidth_data())
        elif path == "/api/media/recommendations-ai":
            d, from_cache, age = _cached("media_recs_ai", _media_recommendations_ai, ttl=600)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/training/viz":
            d, from_cache, age = _cached("training_viz", _training_viz_data, ttl=30)
            if from_cache: d = dict(d); d["_cached"] = True; d["_cache_age"] = age
            self._serve_json(d)
        elif path == "/api/metrics":
            self._serve_json(_system_metrics_data())
        elif path == "/api/dev/status":
            self._serve_json(_dev_status())
        elif path == "/api/execution/queue-status":
            self._serve_json(_execution_queue_status())
        elif path == "/api/aider/worker-status":
            self._serve_json(_aider_worker_status())
        elif path == "/api/zabbix/status":
            self._serve_json(_zabbix_status())
        elif path == "/api/docker/containers":
            self._serve_json(_docker_containers())
        elif path == "/api/docker/security":
            self._serve_json(_docker_security())
        elif path == "/api/docker/status":
            self._serve_json(_docker_snapshot())
        elif path == "/api/plane/items":
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            self._serve_json(_plane_items(qs))
        elif path == "/api/plane/states":
            with _cache_lock:
                sm = _resp_cache.get("_plane_state_map")
            if sm and time.monotonic() < sm[1]:
                self._serve_json({"states": [{"id": k, "name": v} for k, v in sm[0].items()]})
            else:
                # Cache cold — fetch now and cache for next time
                try:
                    api = _get_plane_api()
                    if api and api.api_token and api.project_id:
                        _sts = api.list_states()
                        _sm_data = {s["id"]: s["name"] for s in _sts}
                        with _cache_lock:
                            _resp_cache["_plane_state_map"] = (_sm_data, time.monotonic() + 3600, time.time())
                        self._serve_json({"states": [{"id": k, "name": v} for k, v in _sm_data.items()]})
                    else:
                        self._serve_json({"states": [], "warming": True})
                except Exception:
                    self._serve_json({"states": [], "warming": True})
        elif path == "/api/network/overview":
            self._serve_json(_network_overview())
        elif path == "/api/network/topology":
            force = urlparse(self.path).query == "force=1"
            self._serve_json(_cached("net_topo", lambda: _network_topology(force), 300)[0])
        elif path == "/api/network/opnsense":
            self._serve_json(_cached("net_opnsense", _network_opnsense, 30)[0])
        elif path == "/api/network/qnap":
            self._serve_json(_cached("net_qnap", _network_qnap, 60)[0])
        elif path == "/api/network/isp":
            self._serve_json(_network_isp())
        elif path == "/api/network/isp/history":
            self._serve_json(_network_isp_history())
        elif path.startswith("/plane-proxy"):
            self._do_proxy_plane("GET")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        from framework.audit_log import log as _audit
        path   = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body   = json.loads(self.rfile.read(length) or b"{}")
        ip     = self.client_address[0] if self.client_address else ""

        if path == "/api/executor":
            action = body.get("action", "")
            result = _executor_action(action, body)
            _audit(f"executor_{action}", "executor", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path in ("/api/train", "/api/training/start"):
            result = _start_training()
            _audit("training_started", "training", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/training/stop":
            result = _stop_training()
            _audit("training_stopped", "training", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/model/deploy":
            result = _deploy_model()
            _audit("model_deployed", "ollama", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/media/search-missing":
            result = _media_search_missing(body)
            svc = body.get("service", "")
            _audit("missing_search", svc, "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/media/force-sync":
            result = _media_force_sync()
            _audit("rclone_forced", "qnap", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/media/queue/remove":
            result = _media_queue_remove(body)
            _audit("queue_item_removed", body.get("service", ""), "ok" if result.get("ok") else "fail", ip,
                   f"queue_id={body.get('queue_id')}")
            self._serve_json(result)
        elif path == "/api/circuit-breakers/reset":
            svc = body.get("service", "")
            if svc in _breakers:
                _breakers[svc].reset()
                _audit("circuit_reset", svc, "ok", ip)
                self._serve_json({"ok": True, "message": f"Reset {svc} circuit breaker"})
            else:
                self._serve_json({"ok": False, "message": f"Unknown service: {svc}"})
        elif path == "/api/selfheal/run":
            apply_fixes = body.get("apply_fixes", True)
            result = _selfheal_run(apply_fixes=apply_fixes)
            if result.get("ok"):
                fixes = len(result.get("report", {}).get("fixes_applied", []))
                _audit("selfheal_run", "media", "ok", ip, f"fixes={fixes}")
            self._serve_json(result)
        elif path == "/api/selfheal/diagnose":
            result = _selfheal_diagnose(body)
            _audit("ai_diagnose", body.get("issue", "")[:60], "ok", ip)
            self._serve_json(result)
        elif path == "/api/chat/message":
            self._serve_json(_chat_message(body.get("message", ""), body.get("context")))
        elif path == "/api/roadmap/move":
            self._serve_json(_roadmap_move(body.get("id", ""), body.get("status", "")))
        elif path == "/api/roadmap/create":
            self._serve_json(_roadmap_create(body))
        elif path == "/api/plane/sync-to":
            result = _plane_sync_to()
            _audit("plane_sync_to", "plane", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/plane/sync-from":
            result = _plane_sync_from()
            _audit("plane_sync_from", "plane", "ok" if result.get("ok") else "fail", ip)
            self._serve_json(result)
        elif path == "/api/development/generate":
            self._serve_json(_dev_generate(body))
        elif path == "/api/development/apply":
            self._serve_json(_dev_apply(body))
        elif path == "/api/roadmap/ai-generate":
            self._serve_json(_roadmap_ai_generate(body))
        elif path == "/api/roadmap/create-in-plane":
            result = _roadmap_create_in_plane(body)
            if result.get("success"):
                _audit("roadmap_item_created", body.get("id", ""), "ok", ip)
            self._serve_json(result)
        elif path == "/api/roadmap/scan":
            self._serve_json(_roadmap_scan())
        elif path == "/api/roadmap/import":
            self._serve_json(_roadmap_import(body))
        elif path == "/api/roadmap/decompose":
            self._serve_json(_roadmap_decompose(body))
        elif path == "/api/execution/next-task":
            self._serve_json(_execution_claim_next(body))
        elif path == "/api/execution/complete":
            self._serve_json(_execution_complete(body))
        elif path == "/api/aider/trigger":
            self._serve_json(_aider_worker_trigger())
        elif path == "/api/network/scan":
            self._serve_json(_network_topology(force=True))
        elif path.startswith("/plane-proxy"):
            self._do_proxy_plane("POST")
        else:
            self.send_response(404)
            self.end_headers()

    def _do_proxy_plane(self, method: str) -> None:
        """Proxy any request to Plane on :3001, stripping X-Frame-Options: DENY."""
        import http.client as _hc
        parsed    = urlparse(self.path)
        # Strip "/plane-proxy" prefix but keep the rest (including leading "/")
        proxy_path = parsed.path[len("/plane-proxy"):]
        if not proxy_path:
            proxy_path = "/"
        if parsed.query:
            proxy_path += "?" + parsed.query

        body: bytes | None = None
        length = int(self.headers.get("Content-Length", 0))
        if length:
            body = self.rfile.read(length)

        fwd: dict = {"Host": "localhost:3001"}
        for h in ("Accept", "Accept-Language", "Accept-Encoding", "Content-Type",
                  "Cookie", "Authorization", "Referer"):
            v = self.headers.get(h)
            if v:
                fwd[h] = v

        try:
            conn = _hc.HTTPConnection("localhost", 3001, timeout=20)
            conn.request(method, proxy_path, body, fwd)
            resp     = conn.getresponse()
            raw_data = resp.read()

            STRIP = {"x-frame-options", "content-security-policy", "transfer-encoding"}
            headers  = [(k, v) for k, v in resp.getheaders() if k.lower() not in STRIP]

            self.send_response(resp.status)
            for k, v in headers:
                self.send_header(k, v)
            self.send_header("Content-Security-Policy", "frame-ancestors *")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(raw_data)
        except Exception as exc:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Proxy error: {exc}"}).encode())

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
        # Allow embedding in iframes (for Homepage/Homarr integration)
        self.send_header("Content-Security-Policy", "frame-ancestors *")
        self.send_header("Access-Control-Allow-Origin", "*")
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

def _selfheal_status() -> dict:
    """Current daemon state + recent fixes + last report summary."""
    state = dict(_heal_state)
    if state.get("last_report"):
        r = state["last_report"]
        state["last_report"] = {
            "counts":   r.get("counts", {}),
            "services": r.get("services", {}),
            "issues":   r.get("issues", []),
            "fixes_applied": r.get("fixes_applied", []),
        }
    state["recent_fixes"]   = _recent_fixes(10)
    state["heal_log_tail"]  = _heal_tail(30)
    return state


def _selfheal_run(apply_fixes: bool = True) -> dict:
    """Trigger one manual heal cycle."""
    try:
        report = _run_heal_cycle(apply_fixes=apply_fixes)
        with _cache_lock:
            _resp_cache.pop("selfheal_status", None)   # invalidate cache
        return {"ok": True, "report": report}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def _selfheal_diagnose(body: dict) -> dict:
    """AI diagnosis of a specific issue via Ollama."""
    issue_text = body.get("issue", "")
    context    = body.get("context", {})
    if not issue_text:
        return {"error": "No issue description provided"}
    return _ai_diagnose(issue_text, context or None)


def _selfheal_config() -> dict:
    """Return *arr configuration summary for the config audit panel."""
    try:
        from framework.auto_fixer import AutoFixer
        fixer = AutoFixer()
        return {"ok": True, "config": fixer.get_arr_config_summary()}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


# ── Plane helpers ─────────────────────────────────────────────────────────────

_plane_api_singleton = None
_plane_api_lock = threading.Lock()


def _get_plane_api():
    """Return a shared PlaneAPI singleton (reuses session and cache)."""
    global _plane_api_singleton
    if _plane_api_singleton is not None:
        return _plane_api_singleton
    with _plane_api_lock:
        if _plane_api_singleton is not None:
            return _plane_api_singleton
        try:
            from framework.plane_connector import PlaneAPI
            api = PlaneAPI(
                base_url   = os.environ.get("PLANE_URL",        "http://localhost:8000"),
                api_token  = os.environ.get("PLANE_API_TOKEN",  ""),
                workspace  = os.environ.get("PLANE_WORKSPACE",  "iap"),
                project_id = os.environ.get("PLANE_PROJECT_ID", ""),
            )
            _plane_api_singleton = api
        except Exception:
            pass
    return _plane_api_singleton


def _plane_fetch_all_issues(api, state_id_to_name: dict) -> list:
    """Fetch all Plane issues and normalize to display dicts. Cached 5 min."""
    _key = "_plane_all_issues"
    with _cache_lock:
        cached = _resp_cache.get(_key)
    if cached and time.monotonic() < cached[1]:
        return cached[0]

    # Fetch all issues in one shot (Plane CE supports per_page up to 1000)
    data = api._get(api._proj_url("/issues/"), {"per_page": 1000})
    all_raw: list = data.get("results", []) if isinstance(data, dict) else []

    # Normalize
    _id_re = re.compile(r"^\[(RM-[A-Z][A-Z0-9-]*-\d+)\]\s*")
    items: list = []
    for iss in all_raw:
        name  = iss.get("name", "")
        m     = _id_re.match(name)
        rm_id = m.group(1) if m else ""
        title = name[m.end():].strip() if m else name
        sid   = iss.get("state", "")
        sname = state_id_to_name.get(sid, "Unknown") if state_id_to_name else "Unknown"
        items.append({
            "id":       iss.get("id"),
            "rm_id":    rm_id,
            "title":    title,
            "state":    sname,
            "priority": iss.get("priority", "none"),
            "_name_lc": name.lower(),  # for search
        })

    with _cache_lock:
        _resp_cache[_key] = (items, time.monotonic() + 300, time.time())
    return items


def _plane_items(params: dict) -> dict:
    """Paginated Plane issue list with state/search filtering done client-side.

    Plane CE API ignores ?state= and ?search= filters, so we cache all issues
    and filter locally. Full fetch is cached for 5 minutes.
    """
    api = _get_plane_api()
    if not api or not api.api_token or not api.project_id:
        return {"error": "Plane not configured", "items": [], "total": 0}
    try:
        per_page     = min(int(params.get("per_page", ["100"])[0]), 500)
        page         = max(1, int(params.get("page",     ["1"])[0]))
        search       = (params.get("q",     [None])[0] or "").strip().lower()
        state_filter = (params.get("state", [None])[0] or "").strip()

        # Ensure state map is warm
        with _cache_lock:
            sm = _resp_cache.get("_plane_state_map")
        state_id_to_name: dict = sm[0] if (sm and time.monotonic() < sm[1]) else {}
        if not state_id_to_name:
            _sts = api.list_states()
            state_id_to_name = {s["id"]: s["name"] for s in _sts}
            with _cache_lock:
                _resp_cache["_plane_state_map"] = (state_id_to_name, time.monotonic() + 3600, time.time())

        all_items = _plane_fetch_all_issues(api, state_id_to_name)

        # Client-side filter
        filtered = all_items
        if state_filter and state_filter.lower() not in ("all", ""):
            filtered = [i for i in filtered if i["state"].lower() == state_filter.lower()]
        if search:
            filtered = [i for i in filtered if search in i["_name_lc"]]

        total = len(filtered)
        start = (page - 1) * per_page
        page_items = [
            {k: v for k, v in i.items() if k != "_name_lc"}
            for i in filtered[start:start + per_page]
        ]

        return {"items": page_items, "total": total, "page": page, "per_page": per_page}
    except Exception as exc:
        return {"error": str(exc)[:200], "items": [], "total": 0}


def _plane_stats() -> dict:
    """Roadmap stats for dashboard cards.

    Fast path: single API call for total, uses cached state_map for breakdown.
    Background: if by_state cache is cold, kicks off a lightweight paginated
    count (fetches issues 100 at a time, only reading state field).
    """
    api = _get_plane_api()
    if not api or not api.api_token or not api.project_id:
        return {"error": "Plane not configured"}
    try:
        fast = api.get_stats_fast()
        total = fast.get("total", 0)

        # Pull state_map from server cache (warmed at startup)
        with _cache_lock:
            sm = _resp_cache.get("_plane_state_map")
        state_id_to_name: dict = sm[0] if (sm and time.monotonic() < sm[1]) else {}

        # Derive by_state from cached all-issues list if available
        with _cache_lock:
            _all_cached = _resp_cache.get("_plane_all_issues")
        by_state: dict = {}
        if _all_cached and time.monotonic() < _all_cached[1]:
            for item in _all_cached[0]:
                sname = item.get("state", "Unknown")
                by_state[sname] = by_state.get(sname, 0) + 1

        return {
            "total":             total,
            "done":              by_state.get("Done", 0),
            "in_progress":       by_state.get("In Progress", 0),
            "backlog":           by_state.get("Backlog", 0) + by_state.get("Todo", 0),
            "velocity_per_week": "—",
            "by_state":          by_state,
        }
    except Exception as exc:
        return {"error": str(exc)[:120]}


def _plane_status() -> dict:
    api = _get_plane_api()
    if not api:
        return {"reachable": False, "error": "plane_connector not available"}
    if not api.api_token or not api.project_id:
        return {
            "reachable": False,
            "configured": False,
            "message": "Set PLANE_API_TOKEN and PLANE_PROJECT_ID in docker/.env",
            "plane_url": api.base_url,
        }
    try:
        if not api.health_check():
            return {"reachable": False, "plane_url": api.base_url}
        fast = api.get_stats_fast()
        return {
            "reachable":    True,
            "configured":   True,
            "plane_url":    api.base_url,
            "workspace":    api.workspace,
            "project_id":   api.project_id,
            "total_issues": fast["total"],
            "last_sync":    None,
        }
    except Exception as exc:
        return {"reachable": False, "error": str(exc)[:120]}


def _plane_sync_to() -> dict:
    """Trigger markdown → Plane sync in a subprocess to avoid blocking."""
    api = _get_plane_api()
    if not api or not api.api_token or not api.project_id:
        return {"ok": False, "error": "Plane not configured — set PLANE_API_TOKEN and PLANE_PROJECT_ID"}
    if not api.health_check():
        return {"ok": False, "error": "Plane not reachable"}
    try:
        import subprocess
        env = {**os.environ}
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "bin" / "sync_roadmap_to_plane.py")],
            capture_output=True, text=True, timeout=120, env=env,
        )
        output = result.stdout + result.stderr
        created = output.count(" created")
        updated = output.count(" updated")
        return {"ok": result.returncode == 0, "created": created, "updated": updated, "log": output[-500:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Sync timed out (>120s)"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def _plane_sync_from() -> dict:
    """Trigger Plane → markdown sync in a subprocess."""
    api = _get_plane_api()
    if not api or not api.api_token or not api.project_id:
        return {"ok": False, "error": "Plane not configured — set PLANE_API_TOKEN and PLANE_PROJECT_ID"}
    if not api.health_check():
        return {"ok": False, "error": "Plane not reachable"}
    try:
        import subprocess
        env = {**os.environ}
        result = subprocess.run(
            ["python3", str(REPO_ROOT / "bin" / "sync_plane_to_markdown.py")],
            capture_output=True, text=True, timeout=60, env=env,
        )
        output = result.stdout + result.stderr
        # Count "→" occurrences as changed files
        import re as _re
        changed = len(_re.findall(r"RM-\S+: .+ → .+", output))
        return {"ok": result.returncode == 0, "changed": changed, "log": output[-500:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "Sync timed out (>60s)"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:200]}


def main():
    global _heal_thread
    parser = argparse.ArgumentParser(description="Execution dashboard server")
    parser.add_argument("--port",        type=int, default=8080)
    parser.add_argument("--host",        default="0.0.0.0")
    parser.add_argument("--no-selfheal", action="store_true", help="Disable self-healing daemon")
    args = parser.parse_args()

    if not args.no_selfheal:
        try:
            _heal_thread = _start_heal_daemon()
            print("Self-healing daemon started (5 min interval)")
        except Exception as e:
            print(f"Warning: could not start self-healing daemon: {e}")

    # Warm Plane state cache in background so first /api/plane/items is fast
    def _warm_plane_state_cache():
        import time as _time
        _time.sleep(20)  # wait for selfheal and other startup API calls to settle
        try:
            api = _get_plane_api()
            if api and api.api_token and api.project_id:
                states = api.list_states()
                with _cache_lock:
                    _resp_cache["_plane_state_map"] = (
                        {s["id"]: s["name"] for s in states},
                        time.monotonic() + 3600,
                        time.time(),
                    )
        except Exception:
            pass
    threading.Thread(target=_warm_plane_state_cache, daemon=True).start()

    # Start ISP latency monitor
    try:
        from domains.isp_monitor import get_monitor as _get_isp_monitor
        _get_isp_monitor().start()
    except Exception:
        pass

    # Start overnight aider worker
    try:
        from bin.aider_worker import get_worker as _get_aider_worker
        _get_aider_worker().start()
        print("Aider worker started (runs daily at 02:00)")
    except Exception as e:
        print(f"Warning: could not start aider worker: {e}")

    class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    server = ThreadedHTTPServer((args.host, args.port), Handler)
    print(f"Dashboard: http://localhost:{args.port}/")
    print(f"API:       http://localhost:{args.port}/api/status")
    print("Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        _stop_heal_daemon()


if __name__ == "__main__":
    main()
