#!/usr/bin/env python3
"""Run a bounded OpenHands headless smoke and require AgentState.FINISHED."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate OpenHands headless run completion state")
    parser.add_argument("--timeout-seconds", type=int, default=600)
    parser.add_argument(
        "--task",
        default=(
            "Create /workspace/tmp/openhands_validation.txt containing exactly: "
            "VALIDATION_OK and then confirm completion."
        ),
    )
    parser.add_argument(
        "--log-path",
        default="artifacts/oss_wave/openhands_validation.log",
        help="Where to persist combined run logs",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    log_path = (repo_root / args.log_path).resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [str(repo_root / "bin" / "oss_wave_openhands.sh"), "launch-headless"]
    env = os.environ.copy()
    env["OPENHANDS_TASK"] = args.task

    start = time.time()
    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        lines: list[str] = []

        while True:
            if time.time() - start > args.timeout_seconds:
                proc.kill()
                log_file.write("\nVALIDATION_TIMEOUT\n")
                print(f"FAIL: OpenHands validation timed out after {args.timeout_seconds}s")
                print(f"Log: {log_path}")
                return 124

            line = proc.stdout.readline()
            if line:
                sys.stdout.write(line)
                log_file.write(line)
                lines.append(line)
                continue

            if proc.poll() is not None:
                break

            time.sleep(0.1)

        rc = proc.wait()

    combined = "".join(lines)
    if "AgentState.FINISHED" not in combined:
        print("FAIL: AgentState.FINISHED not found in OpenHands logs")
        print(f"Exit code: {rc}")
        print(f"Log: {log_path}")
        return 1

    if rc != 0:
        print("FAIL: OpenHands exited non-zero despite AgentState.FINISHED")
        print(f"Exit code: {rc}")
        print(f"Log: {log_path}")
        return rc

    print("PASS: OpenHands validation observed AgentState.FINISHED")
    print(f"Log: {log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
