"""Standalone emitter for the local-autonomy dashboard artifact.

Usage:
    python3 bin/local_autonomy_dashboard_emit.py [--artifact-root PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from framework.local_autonomy_dashboard import build_local_autonomy_dashboard, emit_dashboard
from framework.local_memory_store import LocalMemoryStore
from framework.repo_pattern_store import RepoPatternLibrary
from framework.retrieval_cache import RetrievalCache


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit local-autonomy dashboard artifact")
    parser.add_argument(
        "--artifact-root",
        default=str(REPO_ROOT / "artifacts" / "local_autonomy_dashboard"),
    )
    args = parser.parse_args()
    artifact_dir = Path(args.artifact_root)

    memory_store = LocalMemoryStore()
    pattern_library = RepoPatternLibrary()
    cache = RetrievalCache()

    try:
        dashboard = build_local_autonomy_dashboard(
            memory_store=memory_store,
            pattern_library=pattern_library,
            cache=cache,
        )
        out_path = emit_dashboard(dashboard, artifact_dir=artifact_dir)
    except Exception as exc:
        print(f"[DASHBOARD FAILED] {exc}", file=sys.stderr)
        return 1

    data = json.loads(Path(out_path).read_text())
    print(f"\n{'='*56}")
    print(f"  Local Autonomy Dashboard")
    print(f"{'='*56}")
    print(f"  Overall health  : {data['overall_health']}")
    print(f"  Memory stats    : {data['memory_stats']}")
    print(f"  Pattern stats   : {data['repo_pattern_stats']}")
    print(f"  Cache stats     : {data['retrieval_cache_stats']}")
    print(f"  Retry telemetry : {data['retry_telemetry_summary']}")
    print(f"  Readiness       : {data['readiness_summary']}")
    print(f"  Aider preflight : {data['aider_preflight_summary']}")
    print(f"  Artifact        : {out_path}")
    print(f"{'='*56}\n")

    return 1 if data["overall_health"] == "degraded" else 0


if __name__ == "__main__":
    sys.exit(main())
