#!/usr/bin/env python3
"""Generate structured codebase repomap for multi-file task planning.

Produces a machine-readable symbol map of the repository with:
- Python class/function/variable definitions
- Inter-file dependencies
- Size and complexity metrics
- Line-of-code estimates

This enables better multi-file code understanding for edit planning and routing decisions.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from framework.codebase_repomap import RepomapGenerator


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "artifacts" / "repomap" / "latest.json",
        help="Output path for repomap JSON",
    )
    parser.add_argument(
        "--include",
        nargs="+",
        default=["bin/*.py", "framework/*.py", "docs/*.md"],
        help="Glob patterns to include",
    )
    parser.add_argument(
        "--exclude",
        nargs="+",
        default=[".git/**", "__pycache__/**", "artifacts/**", ".venv/**", "tmp/**"],
        help="Glob patterns to exclude",
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=500,
        help="Maximum files to scan",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )

    args = parser.parse_args()

    print(f"Generating codebase repomap from {REPO_ROOT}")
    generator = RepomapGenerator(REPO_ROOT)

    entries = generator.scan_repository(
        include_patterns=args.include,
        exclude_patterns=args.exclude,
        max_files=args.max_files,
    )

    if args.verbose:
        print(f"Scanned {len(entries)} files")
        for path in sorted(entries.keys())[:10]:
            entry = entries[path]
            print(
                f"  {path}: {entry.lines_of_code} LOC, "
                f"{len(entry.symbols)} symbols, {len(entry.dependencies)} deps"
            )

    # Save repomap
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generator.save_repomap(args.output)
    print(f"Wrote repomap to {args.output}")

    # Also save summary
    summary_path = args.output.parent / "summary.json"
    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "file_count": len(entries),
        "total_loc": sum(e.lines_of_code for e in entries.values()),
        "total_symbols": sum(len(e.symbols) for e in entries.values()),
        "total_dependencies": sum(len(e.dependencies) for e in entries.values()),
        "repomap_path": str(args.output),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote summary to {summary_path}")

    if args.verbose:
        print(f"Total LOC: {summary['total_loc']}, Symbols: {summary['total_symbols']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
