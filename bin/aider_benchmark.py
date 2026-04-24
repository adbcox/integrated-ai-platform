#!/usr/bin/env python3
"""Run and inspect local Aider benchmarks."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "config" / "aider_benchmarks.json"
DEFAULT_RUN_ROOT = Path(os.environ.get("AIDER_BENCH_RUN_ROOT", REPO_ROOT / "tmp" / "aider_benchmarks"))
ARTIFACT_ROOT = Path(os.environ.get("AIDER_RUN_ROOT", REPO_ROOT / "artifacts" / "aider_runs" / "local"))
FALLBACK_SUMMARY_FILE = Path(os.environ.get("AIDER_BENCH_SUMMARY_FALLBACK", "/tmp/aider_benchmarks/summary.jsonl"))


def load_scenarios(config_path: Path) -> dict[str, dict]:
    return json.loads(config_path.read_text())


def list_artifacts() -> set[str]:
    if not ARTIFACT_ROOT.exists():
        return set()
    return {relative_artifact_name(p, ARTIFACT_ROOT) for p in ARTIFACT_ROOT.rglob("metadata.json")}


def capture_new_artifacts(before: set[str]) -> list[str]:
    if not ARTIFACT_ROOT.exists():
        return []
    names = {relative_artifact_name(p, ARTIFACT_ROOT) for p in ARTIFACT_ROOT.rglob("metadata.json")}
    return sorted(names - before)


def relative_artifact_name(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def resolve_run_root(path: Path) -> Path:
    candidates = [path, Path("/tmp/aider_benchmarks")]
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / f".write_test_{os.getpid()}"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return candidate
        except OSError:
            continue
    raise SystemExit("Unable to create benchmark run root")


def stream_process(cmd: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
            log.flush()
            sys.stdout.write(line)
        return proc.wait()


def run_validations(commands: list[str], log_dir: Path, extra_env: dict[str, str] | None = None) -> list[dict]:
    results: list[dict] = []
    base_env = os.environ.copy()
    if extra_env:
        base_env.update(extra_env)
    for idx, cmd in enumerate(commands, start=1):
        log_path = log_dir / f"validation-{idx}.log"
        start = time.time()
        with log_path.open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=base_env,
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                log.write(line)
                log.flush()
                sys.stdout.write(line)
            code = proc.wait()
        results.append({
            "command": cmd,
            "exit_code": code,
            "duration_sec": round(time.time() - start, 2),
            "log": rel_to_repo(log_path),
        })
    return results


def rel_to_repo(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_banner_keyvals(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for token in text.strip().split():
        if token.startswith("[") or "=" not in token:
            continue
        key, value = token.split("=", 1)
        data[key] = value
    return data


def extract_profile(log_path: Path) -> dict[str, str]:
    profile: dict[str, str] = {}
    try:
        with log_path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                stripped = line.strip()
                if not stripped.startswith("[aider-local]"):
                    continue
                if "OLLAMA_API_BASE=" in stripped and "api_base" not in profile:
                    profile["api_base"] = stripped.split("=", 1)[1]
                elif "model=" in stripped and "model" not in profile:
                    kv = parse_banner_keyvals(stripped)
                    for key in ("model", "map_tokens", "timeout"):
                        if key in kv:
                            profile[key] = kv[key]
                if {"api_base", "model", "map_tokens", "timeout"}.issubset(profile.keys()):
                    break
    except OSError:
        pass
    return profile


def capture_baseline(files: list[str], run_dir: Path) -> Path:
    baseline_dir = run_dir / "baseline"
    baseline_dir.mkdir(parents=True, exist_ok=True)
    for rel in files:
        src = REPO_ROOT / rel
        dest = baseline_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.copy2(src, dest)
    return baseline_dir


def append_summary(record: dict, summary_path: Path) -> None:
    paths = [summary_path]
    if summary_path != FALLBACK_SUMMARY_FILE:
        paths.append(FALLBACK_SUMMARY_FILE)
    last_exc: OSError | None = None
    for path in paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
            return
        except OSError as exc:
            last_exc = exc
    raise SystemExit(f"Unable to write benchmark summary: {last_exc}")


def build_command(mode: str, prompt: str, files: list[str]) -> list[str]:
    cmd = ["bash", str(REPO_ROOT / "bin" / "aider_local.sh")]
    if mode == "hard":
        cmd.append("--hard")
    elif mode == "smart":
        cmd.append("--smart")
    cmd.extend(["--message", prompt])
    cmd.extend(files)
    return cmd


def run_scenario(name: str, mode: str, scenario: dict, run_root: Path, summary_path: Path) -> int:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / name / mode / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = capture_baseline(scenario.get("files", []), run_dir)

    cmd = build_command(mode, scenario["prompt"], scenario.get("files", []))
    log_path = run_dir / "aider.log"
    print(f"[benchmark] scenario={name} mode={mode}")
    print(f"[benchmark] command={' '.join(cmd)}")

    before = list_artifacts()
    start = time.time()
    exit_code = stream_process(cmd, log_path)
    duration = round(time.time() - start, 2)
    print(f"[benchmark] aider exit_code={exit_code} duration={duration}s")

    validation_env = {"AIDER_BENCH_BASELINE_DIR": str(baseline_dir)}
    validation_results = run_validations(scenario.get("validations", []), run_dir, validation_env)
    artifacts = capture_new_artifacts(before)

    status = "passed" if exit_code == 0 and all(v["exit_code"] == 0 for v in validation_results) else "failed"
    metadata = {
        "scenario": name,
        "mode": mode,
        "description": scenario.get("description"),
        "prompt": scenario.get("prompt"),
        "files": scenario.get("files", []),
        "validations": validation_results,
        "success": scenario.get("success"),
        "command": cmd,
        "exit_code": exit_code,
        "duration_sec": duration,
        "started_at": timestamp,
        "artifacts": artifacts,
        "log": rel_to_repo(log_path),
        "status": status,
        "profile": extract_profile(log_path),
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    append_summary(metadata, summary_path)
    return exit_code


def report_summary(summary_path: Path) -> int:
    if not summary_path.exists():
        print(f"[report] no summary at {summary_path}")
        return 1
    records = [json.loads(line) for line in summary_path.read_text().splitlines() if line.strip()]
    if not records:
        print(f"[report] no records in {summary_path}")
        return 1
    headers = [
        ("started", "started_at"),
        ("scenario", "scenario"),
        ("mode", "mode"),
        ("status", "status"),
        ("model", "model"),
        ("map", "map_tokens"),
        ("timeout", "timeout"),
        ("api_base", "api_base"),
    ]
    rows = []
    for record in records:
        profile = record.get("profile") or {}
        rows.append({
            "started_at": record.get("started_at", ""),
            "scenario": record.get("scenario", ""),
            "mode": record.get("mode", ""),
            "status": record.get("status", ""),
            "model": profile.get("model", "?"),
            "map_tokens": profile.get("map_tokens", "?"),
            "timeout": profile.get("timeout", "?"),
            "api_base": profile.get("api_base", ""),
        })
    widths = {label: max(len(label), *(len(str(row[key])) for row in rows)) for label, key in headers}
    header_line = "  ".join(label.ljust(widths[label]) for label, _ in headers)
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(str(row[key]).ljust(widths[label]) for label, key in headers))
    return 0


def compare_summary(summary_path: Path, scenario: str) -> int:
    if not summary_path.exists():
        print(f"[compare] no summary at {summary_path}")
        return 1
    best: dict[str, dict] = {}
    with summary_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("scenario") != scenario:
                continue
            mode = record.get("mode", "")
            current = best.get(mode)
            if not current or record.get("started_at", "") >= current.get("started_at", ""):
                best[mode] = record
    if not best:
        print(f"[compare] no runs for scenario '{scenario}'")
        return 1
    headers = [
        ("mode", "mode"),
        ("started", "started_at"),
        ("status", "status"),
        ("model", "model"),
        ("map", "map_tokens"),
        ("timeout", "timeout"),
        ("api_base", "api_base"),
    ]
    rows = []
    for mode, record in sorted(best.items()):
        profile = record.get("profile") or {}
        rows.append({
            "mode": mode,
            "started_at": record.get("started_at", ""),
            "status": record.get("status", ""),
            "model": profile.get("model", "?"),
            "map_tokens": profile.get("map_tokens", "?"),
            "timeout": profile.get("timeout", "?"),
            "api_base": profile.get("api_base", ""),
        })
    widths = {label: max(len(label), *(len(str(row[key])) for row in rows)) for label, key in headers}
    header_line = "  ".join(label.ljust(widths[label]) for label, _ in headers)
    print(f"[compare] scenario={scenario}")
    print(header_line)
    print("-" * len(header_line))
    for row in rows:
        print("  ".join(str(row[key]).ljust(widths[label]) for label, key in headers))
    return 0


def list_scenario_names(scenarios: dict[str, dict]) -> None:
    for name, payload in scenarios.items():
        print(f"{name}: {payload.get('description', '')}")


def print_models() -> None:
    print("Mode   Model                             Map  Timeout  Notes")
    print("---------------------------------------------------------------")
    print("fast   ollama_chat/qwen2.5-coder:1.5b    0    60       CPU default")
    print("hard   ollama_chat/qwen2.5-coder:7b      1024 120      heavier tasks")
    print("smart  ollama_chat/qwen2.5-coder:32b     4096 240      requires 32B endpoint")


def latest_summary_path(preferred: Path) -> Path:
    path = preferred
    if not path.exists() and FALLBACK_SUMMARY_FILE.exists():
        path = FALLBACK_SUMMARY_FILE
    elif path.exists() and FALLBACK_SUMMARY_FILE.exists():
        try:
            if FALLBACK_SUMMARY_FILE.stat().st_mtime > path.stat().st_mtime:
                path = FALLBACK_SUMMARY_FILE
        except OSError:
            pass
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or inspect local Aider benchmarks")
    parser.add_argument("--scenario", help="Scenario slug from config")
    parser.add_argument("--mode", choices=["fast", "hard", "smart"], default="fast")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    parser.add_argument("--list", action="store_true", help="List scenarios and exit")
    parser.add_argument("--all", action="store_true", help="Run every scenario")
    parser.add_argument("--report", action="store_true", help="Show summary table")
    parser.add_argument("--compare", help="Show latest per-mode summary for SCENARIO")
    parser.add_argument("--models", action="store_true", help="Show fast/hard/smart defaults")
    args = parser.parse_args()

    config_path = Path(args.config)
    scenarios = load_scenarios(config_path)
    run_root = resolve_run_root(Path(args.run_root))
    summary_path = Path(os.environ.get("AIDER_BENCH_SUMMARY_FILE", run_root / "summary.jsonl"))

    if args.list:
        list_scenario_names(scenarios)
        return
    if args.models:
        print_models()
        return
    if args.report:
        sys.exit(report_summary(latest_summary_path(summary_path)))
    if args.compare:
        sys.exit(compare_summary(latest_summary_path(summary_path), args.compare))

    targets: list[str]
    if args.all:
        targets = list(scenarios.keys())
    else:
        if not args.scenario:
            parser.error("--scenario is required unless --all/--report/--compare/--list/--models is used")
        targets = [args.scenario]

    for name in targets:
        if name not in scenarios:
            print(f"ERROR: unknown scenario '{name}'")
            continue
        rc = run_scenario(name, args.mode, scenarios[name], run_root, summary_path)
        if rc != 0:
            sys.exit(rc)


if __name__ == "__main__":
    main()
