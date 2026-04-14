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


def _path_tokens(path: str) -> set[str]:
    stem = Path(path).stem.lower()
    raw = [p for p in stem.replace("-", "_").split("_") if p]
    tokens: set[str] = set(raw)
    if "/" in path:
        for part in Path(path).parts:
            part = part.lower()
            if part and part not in {"bin", "docs", "shell"}:
                tokens.add(part)
    return {t for t in tokens if t and len(t) > 1}


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


def _subplan_conflict_meta(cluster: list[dict[str, Any]]) -> tuple[float, list[str]]:
    signals: list[str] = []
    if len(cluster) <= 1:
        return 0.0, signals
    conflict = 0.0
    seen_families: dict[str, int] = {}
    seen_dirs: dict[str, int] = {}
    token_sets = [_path_tokens(str(item.get("path") or "")) for item in cluster]
    for idx, item in enumerate(cluster):
        path = str(item.get("path") or "")
        family = _family_key(path)
        parent = str(Path(path).parent)
        if family:
            seen_families[family] = seen_families.get(family, 0) + 1
        if parent:
            seen_dirs[parent] = seen_dirs.get(parent, 0) + 1
        for jdx in range(idx + 1, len(cluster)):
            overlap = token_sets[idx] & token_sets[jdx]
            if overlap:
                weight = min(1.5, 0.3 * len(overlap))
                conflict += weight
                signals.append(f"token_overlap:{','.join(sorted(list(overlap)[:3]))}")
    repeated_families = [k for k, v in seen_families.items() if v > 1]
    if repeated_families:
        conflict += 0.4 * len(repeated_families)
        signals.append(f"family_repeat:{','.join(sorted(repeated_families)[:3])}")
    repeated_dirs = [k for k, v in seen_dirs.items() if v > 1]
    if repeated_dirs:
        conflict += 0.25 * len(repeated_dirs)
        signals.append(f"dir_repeat:{','.join(sorted(repeated_dirs)[:2])}")
    return round(conflict, 3), signals[:6]


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
        avg_rank_score = round(
            sum(float(item.get("rank_score") or 0.0) for item in cluster) / max(1, len(cluster)),
            4,
        )
        conflict_score, conflict_signals = _subplan_conflict_meta(cluster)
        link_strength = round(
            sum(_link_score(item, primary_path) for item in cluster if str(item.get("path") or "") != primary_path)
            / max(1, len(cluster) - 1),
            3,
        ) if len(cluster) > 1 else 0.0
        yield_score = round((avg_confidence * 0.85) + (avg_rank_score * 0.25) + (link_strength * 0.8) - conflict_score, 3)
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
                "rank_score": avg_rank_score,
                "size": len(cluster),
                "strategy": "linked_family_cluster",
                "risk_score": conflict_score,
                "yield_score": yield_score,
                "conflict_signals": conflict_signals,
                "link_strength": link_strength,
            }
        )
        if len(subplans) >= max_subplans:
            break

    return sorted(
        subplans,
        key=lambda sp: (
            -float(sp.get("yield_score") or 0.0),
            float(sp.get("risk_score") or 0.0),
            -float(sp.get("confidence") or 0.0),
        ),
    )


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
            "ranking_version": "rag6-v2-conflict-yield-cluster",
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
