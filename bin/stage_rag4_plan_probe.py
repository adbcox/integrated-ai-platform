#!/usr/bin/env python3
"""Stage RAG-4 planning helper for Stage-6 multi-target orchestration."""

from __future__ import annotations

import argparse  # stage6-rag4-v4a  # stage6-rag4-v3b
import datetime as dt
import json  # stage6-linkscore
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STAGE_RAG3_SEARCH = REPO_ROOT / "bin" / "stage_rag3_search.py"
LOG_DIR = REPO_ROOT / "artifacts" / "stage_rag4"
LOG_FILE = LOG_DIR / "usage.jsonl"


def run_search(args: argparse.Namespace, *, top_override: int | None = None) -> dict[str, Any]:
    top_value = top_override if top_override is not None else args.top
    cmd = [
        sys.executable,
        str(STAGE_RAG3_SEARCH),
        "--top",
        str(top_value),
        "--window",
        str(args.window),
        "--preview-lines",
        str(args.preview_lines),
        "--related-limit",
        str(args.related_limit),
        "--history-window",
        str(args.history_window),
    ]
    cmd += args.query
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def append_log(entry: dict[str, Any]) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_FILE.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _count_related_sources(related_entries: list[dict[str, Any]]) -> tuple[int, int]:
    sibling = 0
    git_history = 0
    for rel in related_entries:
        source = str(rel.get("source") or "")
        if source == "sibling":
            sibling += 1
        elif source == "git_history":
            git_history += 1
    return sibling, git_history


def _path_matches_prefix(path: str, prefixes: list[str]) -> bool:
    if not prefixes:
        return True
    return any(path.startswith(prefix) for prefix in prefixes)


def _path_domain(path: str) -> str:
    if path.startswith("bin/"):
        return "bin"
    if path.startswith("docs/"):
        return "docs"
    if path.startswith("tests/"):
        return "tests"
    if path == "Makefile":
        return "makefile"
    return "other"


def _query_intent(tokens: list[str]) -> str:
    lowered = [t.lower() for t in tokens]
    doc_terms = {"doc", "docs", "documentation", "readme", "guide", "roadmap", "policy"}
    code_terms = {
        "stage6",
        "stage5",
        "manager",
        "rag4",
        "retry",
        "failure",
        "memory",
        "python",
        "script",
        "bin",
        "lane",
        "target",
    }
    doc_hits = sum(1 for t in lowered if any(t.startswith(term) for term in doc_terms))
    code_hits = sum(1 for t in lowered if any(t.startswith(term) for term in code_terms))
    if code_hits > doc_hits:
        return "code"
    if doc_hits > code_hits:
        return "docs"
    return "mixed"


def _domain_bonus(*, intent: str, domain: str) -> float:
    if intent == "code":
        return {
            "bin": 1.35,
            "tests": 0.35,
            "docs": -1.25,
            "makefile": -0.55,
            "other": -0.25,
        }.get(domain, -0.25)
    if intent == "docs":
        return {
            "docs": 1.2,
            "makefile": 0.15,
            "bin": -0.85,
            "tests": -0.45,
            "other": -0.2,
        }.get(domain, -0.2)
    return 0.0


def _ranking_score(
    *,
    base_score: float,
    sibling_count: int,
    git_history_count: int,
    related_count: int,
    related_score: int,
    lane_aligned: bool,
    domain: str,
    intent: str,
) -> float:
    # Stage-6 currently executes mostly bin-scoped work; make lane alignment decisive.
    lane_bonus = 2.35 if lane_aligned else -2.35
    companion_bonus = (min(related_count, 4) * 0.18) + (git_history_count * 0.22) + (sibling_count * 0.12)
    related_preview_bonus = min(related_score / 420.0, 1.6)
    domain_intent_bonus = _domain_bonus(intent=intent, domain=domain)
    return round(base_score + lane_bonus + companion_bonus + related_preview_bonus + domain_intent_bonus, 4)


def _calibrate_confidences(targets: list[dict[str, Any]]) -> None:
    """Assign confidence buckets with score-spread awareness (avoids constant 10s)."""
    if not targets:
        return
    if len(targets) == 1:
        targets[0]["confidence"] = 8 if targets[0].get("lane_aligned") else 6
        return

    scores = [float(t.get("rank_score", 0.0)) for t in targets]
    lo = min(scores)
    hi = max(scores)
    span = hi - lo

    if span < 0.25:
        # Flat-score fallback: confidence by rank with light lane bias.
        for idx, target in enumerate(targets):
            base = max(3, 9 - idx)
            if target.get("lane_aligned"):
                base += 1
            target["confidence"] = max(1, min(10, base))
        return

    for target in targets:
        norm = (float(target.get("rank_score", 0.0)) - lo) / span
        confidence = 2 + int(round(norm * 7))
        if target.get("lane_aligned"):
            confidence += 1
        target["confidence"] = max(1, min(10, confidence))


def _expand_lane_companions(
    *,
    targets: list[dict[str, Any]],
    lane_targets: list[dict[str, Any]],
    preferred_prefixes: list[str],
    direct_result_paths: set[str],
) -> list[dict[str, Any]]:
    """Inject lane-aligned companions discovered through related links."""
    by_path = {t["path"]: t for t in targets}
    companion_pool: dict[str, dict[str, Any]] = {}
    for primary in lane_targets:
        primary_score = float(primary.get("rank_score", 0.0))
        related_paths = primary.get("selection_reason", {}).get("related_paths", [])
        for rel_path in related_paths:
            if not rel_path or rel_path in by_path:
                continue
            if not _path_matches_prefix(rel_path, preferred_prefixes):
                continue
            if rel_path not in direct_result_paths:
                # Keep companion expansion bounded to already-retrieved candidates.
                continue
            domain = _path_domain(rel_path)
            # Keep synthetic companions safely below direct retrieval hits.
            synthetic_score = round(primary_score - 1.6, 4)
            existing = companion_pool.get(rel_path)
            if existing is None:
                companion_pool[rel_path] = {
                    "path": rel_path,
                    "preview": None,
                    "related": [],
                    "source": "stage_rag4_companion",
                    "base_score": 0.0,
                    "rank_score": synthetic_score,
                    "related_score": 0,
                    "lane_aligned": True,
                    "domain": domain,
                    "selection_reason": {
                        "sibling_count": 0,
                        "git_history_count": 0,
                        "related_paths": [],
                        "related_count": 0,
                        "preferred_prefixes": preferred_prefixes,
                        "lane_aligned": True,
                        "query_intent": "code",
                        "domain_bonus": 0.0,
                        "companion_of": [primary["path"]],
                        "companion_support": 1,
                    },
                }
                continue
            existing["rank_score"] = max(float(existing.get("rank_score", 0.0)), synthetic_score)
            reason = existing.setdefault("selection_reason", {})
            supports = reason.setdefault("companion_of", [])
            if primary["path"] not in supports:
                supports.append(primary["path"])
                reason["companion_support"] = int(reason.get("companion_support", 0)) + 1

    if not companion_pool:
        return targets
    targets.extend(companion_pool.values())
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description="Stage RAG-4 planning helper")
    parser.add_argument("query", nargs="+", help="Natural language probe for Stage-6")
    parser.add_argument("--plan-id", required=True)
    parser.add_argument("--top", type=int, default=6)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--preview-lines", type=int, default=18)
    parser.add_argument("--max-targets", type=int, default=4)
    parser.add_argument("--related-limit", type=int, default=2)
    parser.add_argument(
        "--preferred-prefix",
        action="append",
        default=[],
        help="Preferred path prefix (repeatable) used for lane-aware ranking",
    )
    parser.add_argument(
        "--history-window",
        type=int,
        default=15,
        help="Git log window for partner discovery",
    )
    parser.add_argument("--notes", help="Optional notes/context for the plan")
    args = parser.parse_args()

    preferred_prefixes = [prefix for prefix in args.preferred_prefix if prefix]
    intent = _query_intent(args.query)
    search_top = args.top
    if preferred_prefixes and intent == "code":
        # Broaden retrieval for code-intent lane runs so we can recover more
        # lane-aligned candidates without emitting out-of-lane targets.
        search_top = max(args.top, args.max_targets * 4)
    search_payload = run_search(args, top_override=search_top)
    results = search_payload.get("results", [])

    targets: list[dict[str, Any]] = []
    for entry in results:
        path = entry.get("path")
        if not path:
            continue
        domain = _path_domain(path)
        related_entries = [rel for rel in entry.get("related", []) if rel.get("path")]
        related_files = [rel.get("path") for rel in related_entries]
        related_count = len(related_files)
        related_score = sum(len(rel.get("preview", "")) for rel in related_entries)
        sibling_count, git_history_count = _count_related_sources(related_entries)
        base_score = float(entry.get("score") or 0.0)
        lane_aligned = _path_matches_prefix(path, preferred_prefixes)
        rank_score = _ranking_score(
            base_score=base_score,
            sibling_count=sibling_count,
            git_history_count=git_history_count,
            related_count=related_count,
            related_score=related_score,
            lane_aligned=lane_aligned,
            domain=domain,
            intent=intent,
        )
        targets.append(
            {
                "path": path,
                "preview": entry.get("preview"),
                "related": related_files,
                "source": "stage_rag3",
                "base_score": base_score,
                "rank_score": rank_score,
                "related_score": related_score,
                "lane_aligned": lane_aligned,
                "domain": domain,
                "selection_reason": {
                    "sibling_count": sibling_count,
                    "git_history_count": git_history_count,
                    "related_paths": related_files,
                    "related_count": related_count,
                    "preferred_prefixes": preferred_prefixes,
                    "lane_aligned": lane_aligned,
                    "query_intent": intent,
                    "domain_bonus": _domain_bonus(intent=intent, domain=domain),
                },
            }
        )

    direct_result_paths = {str(entry.get("path")) for entry in results if entry.get("path")}

    # Deduplicate by path so Stage-6 does not receive repeated jobs for one file.
    deduped: dict[str, dict[str, Any]] = {}
    for target in targets:
        path = target["path"]
        existing = deduped.get(path)
        if existing is None:
            deduped[path] = target
            continue
        if (
            target["rank_score"],
            int(target.get("lane_aligned", False)),
        ) > (
            existing["rank_score"],
            int(existing.get("lane_aligned", False)),
        ):
            deduped[path] = target

    # Keep targets deterministic by retrieval score + companion strength.
    targets = sorted(
        deduped.values(),
        key=lambda item: (int(item.get("lane_aligned", False)), item["rank_score"], item["path"]),
        reverse=True,
    )
    _calibrate_confidences(targets)
    targets = sorted(
        targets,
        key=lambda item: (int(item.get("lane_aligned", False)), item["rank_score"], item["confidence"], item["path"]),
        reverse=True,
    )

    # For code-intent lane-focused planning, emit lane-aligned targets only when
    # available so Stage-6 does not receive avoidable out-of-lane noise.
    if preferred_prefixes and intent == "code":
        lane_targets = [t for t in targets if t.get("lane_aligned")]
        non_lane_targets = [t for t in targets if not t.get("lane_aligned")]
        if lane_targets:
            targets = _expand_lane_companions(
                targets=lane_targets,
                lane_targets=lane_targets,
                preferred_prefixes=preferred_prefixes,
                direct_result_paths=direct_result_paths,
            )
            _calibrate_confidences(targets)
            targets = sorted(
                targets,
                key=lambda item: (
                    int(item.get("lane_aligned", False)),
                    item["rank_score"],
                    item["confidence"],
                    item["path"],
                ),
                reverse=True,
            )
        else:
            targets = non_lane_targets

    targets = targets[: args.max_targets]

    plan = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "plan_id": args.plan_id,
        "stage": "stage6",
        "query": " ".join(args.query),
        "targets": targets,
        "notes": args.notes,
        "preview_window": args.preview_lines,
        "provenance": {
            "query_tokens": args.query,
            "search_top": search_top,
            "result_count": len(results),
            "unique_target_count": len(targets),
            "related_limit": args.related_limit,
            "history_window": args.history_window,
            "preferred_prefixes": preferred_prefixes,
            "query_intent": intent,
            "ranking_version": "rag4-v4-intent-domain-companions",
        },
        "raw_payload": search_payload,
    }

    append_log(plan)
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
