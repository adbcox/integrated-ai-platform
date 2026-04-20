#!/usr/bin/env python3
"""Build qualify-v4 benchmark and attribution artifacts from available trace data.

Reads artifacts/stage3_manager/traces.jsonl and writes:
  artifacts/codex51/benchmark/latest.json  — {"classes": {"name": {"passed": bool}}}
  artifacts/codex51/attribution/latest.json — {"orchestration_delta": float, "model_delta": float}

These artifacts are consumed by bin/level10_qualify.py to drive
benchmark8_ready and attribution8_ready gates.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE3_TRACE = REPO_ROOT / "artifacts" / "stage3_manager" / "traces.jsonl"
DEFAULT_BENCHMARK_OUT = REPO_ROOT / "artifacts" / "codex51" / "benchmark" / "latest.json"
DEFAULT_ATTRIBUTION_OUT = REPO_ROOT / "artifacts" / "codex51" / "attribution" / "latest.json"

DIRECTORY_CLASS_MAP: list[tuple[str, str]] = [
    ("framework/", "framework_code"),
    ("bin/", "bin_scripts"),
    ("tests/", "test_code"),
    ("config/", "config_data"),
    ("shell/", "shell_scripts"),
    ("promotion/", "promotion_engine"),
    ("governance/", "governance_artifacts"),
]

PASS_ACCEPTANCE_THRESHOLD = 0.5


def _classify_target(target: str) -> str:
    for prefix, class_name in DIRECTORY_CLASS_MAP:
        if prefix in target:
            return class_name
    return "other"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows


def build_benchmark_payload(rows: list[dict]) -> dict:
    by_class: dict[str, list[bool]] = defaultdict(list)
    for row in rows:
        target = str(row.get("target_file") or row.get("target") or "")
        if not target:
            continue
        class_name = _classify_target(target)
        by_class[class_name].append(bool(row.get("accepted")))
    classes: dict[str, dict] = {}
    for class_name, accepted_list in sorted(by_class.items()):
        total = len(accepted_list)
        accepted_count = sum(accepted_list)
        rate = accepted_count / total if total else 0.0
        classes[class_name] = {
            "passed": rate >= PASS_ACCEPTANCE_THRESHOLD,
            "acceptance_rate": round(rate, 3),
            "run_count": total,
        }
    return {"classes": classes, "source": "stage3_traces", "run_count": sum(len(v) for v in by_class.values())}


def build_attribution_payload(rows: list[dict]) -> dict:
    total = len(rows)
    if total == 0:
        return {"orchestration_delta": 0.0, "model_delta": 0.0, "source": "stage3_traces", "run_count": 0}
    accepted_count = sum(1 for r in rows if r.get("accepted"))
    fallback_count = sum(1 for r in rows if r.get("fallback_used"))
    accepted_rate = accepted_count / total
    fallback_rate = fallback_count / total
    orchestration_delta = round(accepted_rate - fallback_rate, 3)
    model_delta = round((1.0 - fallback_rate) - fallback_rate, 3)
    return {
        "orchestration_delta": orchestration_delta,
        "model_delta": model_delta,
        "source": "stage3_traces",
        "run_count": total,
        "accepted_rate": round(accepted_rate, 3),
        "fallback_rate": round(fallback_rate, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build qualify-v4 benchmark and attribution artifacts")
    parser.add_argument("--stage3-trace", default=str(DEFAULT_STAGE3_TRACE))
    parser.add_argument("--benchmark-out", default=str(DEFAULT_BENCHMARK_OUT))
    parser.add_argument("--attribution-out", default=str(DEFAULT_ATTRIBUTION_OUT))
    parser.add_argument("--dry-run", action="store_true", help="Print computed values without writing")
    args = parser.parse_args()

    rows = _load_jsonl(Path(args.stage3_trace).resolve())
    if not rows:
        print(f"[qualify_v4_artifact_builder] WARNING: no rows in {args.stage3_trace}", file=sys.stderr)

    benchmark_payload = build_benchmark_payload(rows)
    attribution_payload = build_attribution_payload(rows)

    if args.dry_run:
        print("=== benchmark ===")
        print(json.dumps(benchmark_payload, indent=2))
        print("=== attribution ===")
        print(json.dumps(attribution_payload, indent=2))
        return 0

    bench_path = Path(args.benchmark_out).resolve()
    bench_path.parent.mkdir(parents=True, exist_ok=True)
    bench_path.write_text(json.dumps(benchmark_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    attr_path = Path(args.attribution_out).resolve()
    attr_path.parent.mkdir(parents=True, exist_ok=True)
    attr_path.write_text(json.dumps(attribution_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[qualify_v4_artifact_builder] wrote benchmark -> {bench_path}")
    print(f"[qualify_v4_artifact_builder] wrote attribution -> {attr_path}")
    print(f"[qualify_v4_artifact_builder] benchmark classes: {list(benchmark_payload['classes'].keys())}")
    print(
        f"[qualify_v4_artifact_builder] orchestration_delta={attribution_payload['orchestration_delta']} "
        f"model_delta={attribution_payload['model_delta']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
