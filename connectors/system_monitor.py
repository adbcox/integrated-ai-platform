"""Local system monitoring — CPU, RAM, disk, network via psutil."""
from __future__ import annotations

import os
import platform
import time
from typing import Any, Dict


def get_mac_stats() -> Dict[str, Any]:
    """CPU%, RAM%, disk%, load avg, uptime. Gracefully degrades without psutil."""
    result: Dict[str, Any] = {
        "hostname": platform.node(),
        "os":       platform.system(),
        "arch":     platform.machine(),
    }

    try:
        import psutil

        cpu   = psutil.cpu_percent(interval=0.3)
        mem   = psutil.virtual_memory()
        disk  = psutil.disk_usage("/")
        load  = os.getloadavg()
        boot  = psutil.boot_time()
        uptime_h = round((time.time() - boot) / 3600, 1)

        # Network throughput (1-second sample)
        n0 = psutil.net_io_counters()
        time.sleep(0.5)
        n1 = psutil.net_io_counters()
        net_mb_s = round(
            (n1.bytes_sent + n1.bytes_recv - n0.bytes_sent - n0.bytes_recv) / (1024**2 * 0.5),
            2,
        )

        # Per-core temps (macOS: no sensor API; skip gracefully)
        temps = {}
        try:
            raw = psutil.sensors_temperatures()
            if raw:
                for name, entries in raw.items():
                    if entries:
                        temps[name] = round(entries[0].current, 1)
        except (AttributeError, Exception):
            pass

        result.update({
            "status":       "ok",
            "cpu_pct":      round(cpu, 1),
            "cpu_cores":    psutil.cpu_count(logical=False),
            "cpu_threads":  psutil.cpu_count(logical=True),
            "mem_pct":      round(mem.percent, 1),
            "mem_used_gb":  round(mem.used  / (1024**3), 1),
            "mem_total_gb": round(mem.total / (1024**3), 1),
            "disk_pct":     round(disk.percent, 1),
            "disk_free_gb": round(disk.free  / (1024**3), 1),
            "disk_total_gb": round(disk.total / (1024**3), 1),
            "net_mb_s":     net_mb_s,
            "load_1m":      round(load[0], 2),
            "load_5m":      round(load[1], 2),
            "load_15m":     round(load[2], 2),
            "uptime_h":     uptime_h,
            "temps":        temps,
        })

    except ImportError:
        result["status"]  = "needs_psutil"
        result["message"] = "pip install psutil"
    except Exception as exc:
        result["status"]  = "error"
        result["message"] = str(exc)[:120]

    return result


def get_ollama_stats() -> Dict[str, Any]:
    """Ollama process reachability + loaded model list."""
    import urllib.request, json as _json
    host = os.environ.get("OLLAMA_HOST", "localhost:11434")
    if "://" not in host:
        host = f"http://{host}"
    try:
        with urllib.request.urlopen(f"{host}/api/tags", timeout=3) as r:
            data = _json.loads(r.read())
        models = [m.get("name", "") for m in data.get("models", [])]
        return {
            "status":      "running",
            "models":      models,
            "model_count": len(models),
            "host":        host,
        }
    except Exception as exc:
        return {"status": "offline", "error": str(exc)[:80], "host": host}
