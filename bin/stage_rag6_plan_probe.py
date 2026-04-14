#!/usr/bin/env python3
"""Stage RAG-6 planning helper for Stage-7 multi-plan orchestration."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG4_PLAN = REPO_ROOT / "bin" / "stage_rag4_plan_probe.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag6"
LOG_FILE = LOG_DIR / "usage.jsonl"


def append_log(entry: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _family_key(path: str) -> str:
    name = Path(path).stem.lower()
    for sep in ("_", "-"):
        if sep in name:
            return name.split(sep, 1)[0]
    return name


def _link_score(candidate: dict[str, Any], primary_path: str) -> float:
    reason = candidate.get("selection_reason", {}) or {}
    related = {str(p) for p in reason.get("related_paths", []) if p}
    if primary_path in related:
        return 2.0
    companion_of = set(reason.get("companion_of", []) or [])
    if primary_path in companion_of:
        return 1.5
    return float(reason.get("companion_link_strength") or 0.0)


def _risk_bucket(confidence: int) -> str:
    if confidence >= 8:
        return "low"
    if confidence >= 5:
        return "medium"
    return "high"


def run_rag4(args: argparse.Namespace) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(STAGE_RAG4_PLAN),
        "--plan-id",
        f"{args.plan_id}-rag4",
        "--top",
        str(args.top),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
        "--max-targets",
        str(args.max_targets),
        "--related-limit",
        str(args.related_limit),
        "--history-window",
        str(args.history_window),
    ]
    if args.notes:
        cmd.extend(["--notes", args.notes])
    for prefix in args.preferred_prefix:
        cmd.extend(["--preferred-prefix", prefix])
    cmd.extend(args.query)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def build_subplans(
    *,
    targets: list[dict[str, Any]],
    max_subplans: int,
    subplan_size: int,
) -> list[dict[str, Any]]:
    if not targets:
        return []

    ordered = list(targets)
    consumed: set[str] = set()
    subplans: list[dict[str, Any]] = []

    for primary in ordered:
        primary_path = str(primary.get("path") or "")
        if not primary_path or primary_path in consumed:
            continue

        cluster = [primary]
        consumed.add(primary_path)
        for candidate in ordered:
            path = str(candidate.get("path") or "")
            if not path or path in consumed:
                continue
            if len(cluster) >= subplan_size:
                break
            same_family = _family_key(path) == _family_key(primary_path)
            linked = _link_score(candidate, primary_path) >= 1.5
            if same_family or linked:
                cluster.append(candidate)
                consumed.add(path)

        avg_confidence = round(
            sum(int(item.get("confidence") or 0) for item in cluster) / max(1, len(cluster)),
            2,
        )
        subplan_id = f"subplan-{len(subplans) + 1}"
        subplans.append(
            {
                "subplan_id": subplan_id,
                "primary": primary_path,
                "targets": [str(item.get("path")) for item in cluster],
                "target_meta": [
                    {
                        "path": str(item.get("path")),
                        "confidence": int(item.get("confidence") or 0),
                        "rank_score": float(item.get("rank_score") or 0.0),
                        "risk_bucket": _risk_bucket(int(item.get("confidence") or 0)),
                        "family": _family_key(str(item.get("path") or "")),
                    }
                    for item in cluster
                ],
                "confidence": avg_confidence,
                "size": len(cluster),
                "strategy": "linked_family_cluster",
            }
        )
        if len(subplans) >= max_subplans:
            break

    return subplans


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-6 planning helper")
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("query", nargs="+", help="Natural language probe for Stage-7")
    parser.add_argument("--top", type=int, default=8)
    parser.add_argument("--window", type=int, default=25)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--max-targets", type=int, default=9)
    parser.add_argument("--max-subplans", type=int, default=3)
    parser.add_argument("--subplan-size", type=int, default=3)
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument("--history-window", type=int, default=15)
    parser.add_argument("--notes", help="Optional notes/context for the plan")
    parser.add_argument(
        "--preferred-prefix",
        action="append",
        default=[],
        help="Preferred path prefix (repeatable) used for lane-aware ranking",
    )
    args = parser.parse_args()

    rag4_plan = run_rag4(args)
    targets = list(rag4_plan.get("targets", []))
    preferred_prefixes = [p for p in args.preferred_prefix if p]
    if preferred_prefixes:
        lane_aligned = [
            t for t in targets if any(str(t.get("path") or "").startswith(prefix) for prefix in preferred_prefixes)
        ]
        # Stage-7 should consume lane-clean candidates whenever available.
        if lane_aligned:
            targets = lane_aligned
    subplans = build_subplans(
        targets=targets,
        max_subplans=max(1, args.max_subplans),
        subplan_size=max(1, args.subplan_size),
    )

    plan = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "plan_id": args.plan_id,
        "stage": "stage7",
        "query": " ".join(args.query),
        "subplans": subplans,
        "notes": args.notes,
        "provenance": {
            "query_tokens": args.query,
            "max_targets": args.max_targets,
            "max_subplans": args.max_subplans,
            "subplan_size": args.subplan_size,
            "preferred_prefixes": preferred_prefixes,
            "ranking_version": "rag6-v1-clustered-subplan",
            "upstream_rag4_plan_id": rag4_plan.get("plan_id"),
            "upstream_ranking_version": (rag4_plan.get("provenance") or {}).get("ranking_version"),
            "retrieved_targets": len(targets),
            "emitted_subplans": len(subplans),
        },
        "raw_payload": rag4_plan,
    }

    append_log(plan)
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
