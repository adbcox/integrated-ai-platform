#!/usr/bin/env python3
"""Thin governed wrapper around markitdown CLI for local ingestion."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import shutil


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert supported documents to markdown via markitdown")
    parser.add_argument("input", help="Input file path")
    parser.add_argument("-o", "--output", required=True, help="Output markdown path")
    parser.add_argument(
        "--allow-ext",
        action="append",
        default=[".pdf", ".docx", ".pptx", ".xlsx", ".txt", ".html", ".csv", ".md"],
        help="Allowed input extension (repeatable)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists() or not input_path.is_file():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 2

    allow_ext = {ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in args.allow_ext}
    if input_path.suffix.lower() not in allow_ext:
        print(
            f"ERROR: unsupported input extension '{input_path.suffix}'. Allowed: {sorted(allow_ext)}",
            file=sys.stderr,
        )
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    if shutil.which("markitdown"):
        cmd = ["markitdown", str(input_path), "-o", str(output_path)]
    elif shutil.which("uvx"):
        cmd = ["uvx", "--from", "markitdown", "markitdown", str(input_path), "-o", str(output_path)]
    else:
        print("ERROR: markitdown (or uvx) is not available in PATH", file=sys.stderr)
        return 2
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        print("ERROR: markitdown failed", file=sys.stderr)
        if proc.stderr:
            print(proc.stderr.strip(), file=sys.stderr)
        return proc.returncode

    print(f"PASS: converted {input_path} -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
