#!/usr/bin/env python3
"""Minimal harness to run Aider benchmarks via local launcher."""

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


def load_scenario(config_path: Path, scenario: str) -> dict:
    data = json.loads(config_path.read_text())
    if scenario not in data:
        raise SystemExit(f"Scenario '{scenario}' not found in {config_path}")
    return data[scenario]


def capture_new_artifacts(before: set[str]) -> list[str]:
    root = ARTIFACT_ROOT
    if not root.exists():
        return []
    names = {relative_artifact_name(p, root) for p in root.rglob("metadata.json")}
    return sorted(names - before)


def list_artifacts() -> set[str]:
    root = ARTIFACT_ROOT
    if not root.exists():
        return set()
    return {relative_artifact_name(p, root) for p in root.rglob("metadata.json")}


def relative_artifact_name(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        try:
            return str(path.relative_to(root.parent))
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
    raise SystemExit(f"Unable to create benchmark run root (tried: {', '.join(str(c) for c in candidates)})")


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
    results = []
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
        try:
            log_rel = str(log_path.relative_to(REPO_ROOT))
        except ValueError:
            log_rel = str(log_path)
        results.append({
            "command": cmd,
            "exit_code": code,
            "duration_sec": round(time.time() - start, 2),
            "log": log_rel,
        })
    return results


def build_command(mode: str, prompt: str, files: list[str]) -> list[str]:
    cmd = [str(REPO_ROOT / "bin" / "aider_local.sh")]
    if mode == "smart":
        cmd.append("--smart")
    cmd.extend(["--message", prompt])
    cmd.extend(files)
    return cmd


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


def append_summary(record: dict, summary_path: Path) -> Path:
    paths = [summary_path]
    if summary_path != FALLBACK_SUMMARY_FILE:
        paths.append(FALLBACK_SUMMARY_FILE)
    last_exc: OSError | None = None
    for path in paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
            return path
        except OSError as exc:
            last_exc = exc
    raise SystemExit(f"Unable to write benchmark summary: {last_exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a benchmark scenario via aider_local.sh")
    parser.add_argument("--scenario", required=True, help="Scenario slug from config")
    parser.add_argument("--mode", choices=["fast", "smart"], default="fast")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    args = parser.parse_args()

    config_path = Path(args.config)
    scenario = load_scenario(config_path, args.scenario)

    run_root = resolve_run_root(Path(args.run_root))
    summary_file = Path(os.environ.get("AIDER_BENCH_SUMMARY_FILE", run_root / "summary.jsonl"))
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / args.scenario / args.mode / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    baseline_dir = capture_baseline(scenario.get("files", []), run_dir)

    cmd = build_command(args.mode, scenario["prompt"], scenario.get("files", []))
    log_path = run_dir / "aider.log"
    print(f"[benchmark] scenario={args.scenario} mode={args.mode}")
    print(f"[benchmark] command={' '.join(cmd)}")

    before_artifacts = list_artifacts()
    start = time.time()
    exit_code = stream_process(cmd, log_path)
    duration = round(time.time() - start, 2)
    print(f"[benchmark] aider exit_code={exit_code} duration={duration}s")

    validation_env = {"AIDER_BENCH_BASELINE_DIR": str(baseline_dir)}
    validation_results = run_validations(scenario.get("validations", []), run_dir, validation_env)
    artifacts = capture_new_artifacts(before_artifacts)

    status = "passed" if exit_code == 0 and all(r["exit_code"] == 0 for r in validation_results) else "failed"
    try:
        log_rel = str(log_path.relative_to(REPO_ROOT))
    except ValueError:
        log_rel = str(log_path)
    metadata = {
        "scenario": args.scenario,
        "mode": args.mode,
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
        "log": log_rel,
        "status": status
    }
    (run_dir / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    append_summary(metadata, summary_file)
    if exit_code != 0:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
