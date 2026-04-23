#!/usr/bin/env python3
"""Local-first Aider router with bounded retries and machine-readable attribution.

This script exists to make local Ollama the default execution path for Developer
Assistance. It tries a small ordered set of local models, captures per-attempt
artifacts under artifacts/aider_runs/, and emits a compact routing summary.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
ARTIFACT_ROOT = BASE_DIR / "artifacts" / "aider_runs"


DEFAULT_API_BASE = os.environ.get("OLLAMA_API_BASE", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_MODEL_ORDER = [
    "ollama_chat/qwen2.5-coder:14b",
    "ollama_chat/deepseek-coder-v2:latest",
    "ollama_chat/qwen2.5-coder:7b",
]


@dataclass(frozen=True)
class AttemptResult:
    model: str
    status: str  # passed|failed|skipped
    exit_code: Optional[int]
    duration_sec: float
    run_dir: Optional[str]
    failure_signatures: list[str]


def _now_ts() -> str:
    return time.strftime("%Y%m%d_%H%M%S", time.localtime())


def _slugify(value: str) -> str:
    out = []
    for ch in value.strip():
        out.append(ch if ch.isalnum() or ch in {"-", "_", "."} else "-")
    slug = "".join(out).strip("-._")
    return slug or "task"


def _http_ok(url: str, *, timeout_sec: float = 5.0) -> tuple[bool, str]:
    # Use curl for consistency with other scripts and to avoid urllib TLS edge cases.
    cmd = ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "--max-time", str(timeout_sec), url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return False, "curl_missing"
    code = (proc.stdout or "").strip()
    if code == "200":
        return True, "ok"
    detail = (proc.stderr or proc.stdout or "").strip()[:300]
    return False, f"http_{code or 'unknown'}:{detail}"


def _fetch_ollama_model_names(api_base: str, *, timeout_sec: float = 6.0) -> Optional[set[str]]:
    """Return the set of model names available on the Ollama endpoint.

    Names are returned in the Ollama-native format (e.g. "qwen2.5-coder:14b").
    """
    url = f"{api_base.rstrip('/')}/api/tags"
    cmd = ["curl", "-sS", "--max-time", str(timeout_sec), url]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        return None
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout or "{}")
    except Exception:  # noqa: BLE001
        return None
    models = payload.get("models")
    if not isinstance(models, list):
        return None
    names: set[str] = set()
    for entry in models:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            name = entry["name"].strip()
            if name:
                names.add(name)
    return names


def _strip_aider_prefix(model: str) -> str:
    # Aider uses prefixes like "ollama_chat/<model>". Ollama's /api/tags returns "<model>".
    if "/" in model:
        return model.split("/", 1)[1].strip()
    return model.strip()


def _latest_subdir(path: Path) -> Optional[Path]:
    if not path.exists():
        return None
    subdirs = [p for p in path.iterdir() if p.is_dir()]
    if not subdirs:
        return None
    subdirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return subdirs[0]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def _build_message_from_task(task: dict[str, Any]) -> str:
    objective = str(task.get("objective") or "").strip()
    constraints = task.get("constraints") if isinstance(task.get("constraints"), list) else []
    out_of_scope = task.get("out_of_scope") if isinstance(task.get("out_of_scope"), list) else []
    acceptance = task.get("acceptance_criteria") if isinstance(task.get("acceptance_criteria"), list) else []
    validations = task.get("validation_commands") if isinstance(task.get("validation_commands"), list) else []
    files = []
    for entry in task.get("target_files") or []:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str):
            files.append(entry["path"].strip())
    files = [f for f in files if f]

    limits = task.get("limits") if isinstance(task.get("limits"), dict) else {}
    max_files = limits.get("max_files")
    max_loc = limits.get("max_loc")

    lines: list[str] = []
    lines.append("You are a local-first coding assistant running via Ollama.")
    if objective:
        lines.append(f"Objective: {objective}")
    if files:
        lines.append("Hard constraints:")
        lines.append(f"- Only edit these files: {', '.join(files)}")
        lines.append("- Do not create or modify any other files.")
    if isinstance(max_files, int):
        lines.append(f"- Keep changed files <= {max_files}.")
    if isinstance(max_loc, int):
        lines.append(f"- Keep the diff within ~{max_loc} total added+deleted lines.")
    if constraints:
        lines.append("Additional constraints:")
        for item in constraints:
            item_s = str(item).strip()
            if item_s:
                lines.append(f"- {item_s}")
    if out_of_scope:
        lines.append("Out of scope:")
        for item in out_of_scope:
            item_s = str(item).strip()
            if item_s:
                lines.append(f"- {item_s}")
    if acceptance:
        lines.append("Acceptance criteria:")
        for item in acceptance:
            item_s = str(item).strip()
            if item_s:
                lines.append(f"- {item_s}")
    if validations:
        lines.append("Validation commands that must pass after your edits:")
        for cmd in validations:
            cmd_s = str(cmd).strip()
            if cmd_s:
                lines.append(f"- {cmd_s}")
    lines.append("If you cannot satisfy constraints, stop and explain why.")
    return "\n".join(lines).strip() + "\n"


def _load_task_file(task_file: Path) -> dict[str, Any]:
    data = _read_json(task_file)
    if not isinstance(data, dict):
        raise ValueError("task file is not a JSON object")
    if "task" not in data:
        raise ValueError("task file missing 'task' key")
    return data


def _extract_task_files(task: dict[str, Any]) -> list[str]:
    files = []
    for entry in task.get("target_files") or []:
        if not isinstance(entry, dict):
            continue
        path = entry.get("path")
        if isinstance(path, str) and path.strip():
            files.append(path.strip())
    if not files:
        raise ValueError("task file has no target_files paths")
    return files


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Route a local Aider run across preferred Ollama models.")
    parser.add_argument("--task-file", help="Path to JSON task brief (preferred for automation).")
    parser.add_argument("--name", help="Optional name for artifact labeling.")
    parser.add_argument("--api-base", default=DEFAULT_API_BASE, help="Ollama API base URL.")
    parser.add_argument("--mode", default=os.environ.get("AIDER_ROUTER_MODE", "default"),
                        choices=("default", "micro", "hard"),
                        help="Controls map-tokens and timeout defaults.")
    parser.add_argument("--models", help="Comma-separated model list (overrides defaults).")
    parser.add_argument("--primary-retry", type=int, default=int(os.environ.get("AIDER_ROUTER_PRIMARY_RETRY", "1")),
                        help="Retry the primary model this many times on failure before fallback.")
    parser.add_argument("--message", help="Direct message string to pass to Aider (if no task-file).")
    parser.add_argument("files", nargs="*", help="Target files for direct mode (if no task-file).")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    api_base = (args.api_base or DEFAULT_API_BASE).rstrip("/")
    ok, detail = _http_ok(f"{api_base}/api/tags", timeout_sec=4.0)
    if not ok:
        sys.stderr.write(f"ERROR: Ollama endpoint '{api_base}' unreachable ({detail})\n")
        return 2
    available_models = _fetch_ollama_model_names(api_base)

    task: Optional[dict[str, Any]] = None
    message = (args.message or "").strip()
    files = [f for f in (args.files or []) if f.strip()]
    task_name = (args.name or "").strip()
    task_class = ""

    if args.task_file:
        task_path = Path(args.task_file)
        if not task_path.is_absolute():
            task_path = (BASE_DIR / task_path).resolve()
        task = _load_task_file(task_path)
        task_name = task_name or str(task.get("task", {}).get("name") or "")
        task_class = str(task.get("task", {}).get("class") or "")
        message = _build_message_from_task(task)
        files = _extract_task_files(task)

    if not message:
        sys.stderr.write("ERROR: --message is required when --task-file is not provided\n")
        return 2
    if not files:
        sys.stderr.write("ERROR: target files are required (positional args or from --task-file)\n")
        return 2

    model_order = DEFAULT_MODEL_ORDER
    if args.models:
        model_order = [m.strip() for m in args.models.split(",") if m.strip()]
        if not model_order:
            model_order = DEFAULT_MODEL_ORDER

    # Mode tuning: keep bounded but allow more context for non-micro tasks.
    if args.mode == "micro":
        map_tokens = int(os.environ.get("AIDER_ROUTER_MAP_TOKENS_MICRO", "0"))
        timeout = int(os.environ.get("AIDER_ROUTER_TIMEOUT_MICRO", "120"))
    elif args.mode == "hard":
        map_tokens = int(os.environ.get("AIDER_ROUTER_MAP_TOKENS_HARD", "2048"))
        timeout = int(os.environ.get("AIDER_ROUTER_TIMEOUT_HARD", "240"))
    else:
        map_tokens = int(os.environ.get("AIDER_ROUTER_MAP_TOKENS", "1024"))
        timeout = int(os.environ.get("AIDER_ROUTER_TIMEOUT", "180"))

    forced_fail = (os.environ.get("AIDER_ROUTER_FORCE_FAIL_MODEL") or "").strip()

    run_slug = _slugify(task_name or (task_class or "aider"))
    router_run_id = f"{_now_ts()}_{run_slug}_{os.getpid()}"
    router_root = ARTIFACT_ROOT / "router" / router_run_id
    router_root.mkdir(parents=True, exist_ok=True)

    attempts: list[AttemptResult] = []

    primary = model_order[0]
    expanded_models: list[str] = [primary] * max(1, args.primary_retry + 1) + model_order[1:]

    for idx, model in enumerate(expanded_models, start=1):
        if forced_fail and model == forced_fail:
            attempts.append(
                AttemptResult(
                    model=model,
                    status="skipped",
                    exit_code=None,
                    duration_sec=0.0,
                    run_dir=None,
                    failure_signatures=["forced_fail_model"],
                )
            )
            continue
        if available_models is not None:
            raw_name = _strip_aider_prefix(model)
            if raw_name and raw_name not in available_models:
                attempts.append(
                    AttemptResult(
                        model=model,
                        status="skipped",
                        exit_code=None,
                        duration_sec=0.0,
                        run_dir=None,
                        failure_signatures=["model_missing_local"],
                    )
                )
                continue

        attempt_root = router_root / f"attempt_{idx}"
        attempt_root.mkdir(parents=True, exist_ok=True)

        env = os.environ.copy()
        env["AIDER_RUN_ROOT"] = str(attempt_root)
        env["AIDER_SUP_LABEL"] = f"router-{idx}"
        env["AIDER_SUP_FAIL_FAST"] = "0"

        cmd = [
            "bash",
            str(BASE_DIR / "bin" / "aider_local.sh"),
            "--api-base",
            api_base,
            "--model",
            model,
            "--map-tokens",
            str(map_tokens),
            "--timeout",
            str(timeout),
            "--message",
            message,
            *files,
        ]

        start = time.time()
        proc = subprocess.run(cmd, env=env, check=False)
        duration = round(time.time() - start, 2)

        out_dir = _latest_subdir(attempt_root)
        metadata = _read_json(out_dir / "metadata.json") if out_dir else {}
        status = str(metadata.get("status") or ("passed" if proc.returncode == 0 else "failed"))
        failure_signatures = []
        if isinstance(metadata.get("failure_signatures"), list):
            failure_signatures = [str(x) for x in metadata.get("failure_signatures") if str(x)]

        attempts.append(
            AttemptResult(
                model=model,
                status=status,
                exit_code=proc.returncode,
                duration_sec=duration,
                run_dir=str(out_dir.relative_to(BASE_DIR)) if out_dir else None,
                failure_signatures=failure_signatures,
            )
        )

        if status == "passed" and proc.returncode == 0:
            break

    succeeded_attempt = next((a for a in attempts if a.status == "passed" and (a.exit_code or 0) == 0), None)
    used_multiple_models = len({a.model for a in attempts if a.status != "skipped"}) > 1

    routing_bucket = "escalated"
    selected_model = None
    if succeeded_attempt:
        selected_model = succeeded_attempt.model
        if selected_model == primary and attempts and attempts[0].model == primary and succeeded_attempt == attempts[0]:
            routing_bucket = "local_primary"
        elif selected_model == primary:
            routing_bucket = "local_retry"
        else:
            routing_bucket = "local_fallback_model"

    summary = {
        "router_run_id": router_run_id,
        "api_base": api_base,
        "task_name": task_name or None,
        "task_class": task_class or None,
        "mode": args.mode,
        "model_order": model_order,
        "map_tokens": map_tokens,
        "timeout": timeout,
        "routing_bucket": routing_bucket,
        "mixed": bool(used_multiple_models and succeeded_attempt),
        "selected_model": selected_model,
        "attempts": [
            {
                "model": a.model,
                "status": a.status,
                "exit_code": a.exit_code,
                "duration_sec": a.duration_sec,
                "run_dir": a.run_dir,
                "failure_signatures": a.failure_signatures,
            }
            for a in attempts
        ],
        "escalation_recommended": succeeded_attempt is None,
        "escalation_reason": None if succeeded_attempt else "bounded_local_retries_exhausted",
        "timestamp": int(time.time()),
    }

    (router_root / "routing_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    events_path = ARTIFACT_ROOT / "router_events.jsonl"
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(summary) + "\n")

    # Print a compact machine-readable line for callers.
    print(json.dumps({k: summary[k] for k in ("routing_bucket", "selected_model", "mixed", "router_run_id")}))

    return 0 if succeeded_attempt else 1


if __name__ == "__main__":
    raise SystemExit(main())
