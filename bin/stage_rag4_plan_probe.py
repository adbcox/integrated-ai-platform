#!/usr/bin/env python3
"""Stage RAG-4 planning helper for Stage-6 multi-target orchestration."""

from __future__ import annotations

import argparse  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage7-op  # stage6-rag4-v4b  # stage6-rag4-v3b
import datetime as dt
import json  # stage6-linkscore-v2
import math
import re
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
    if path.startswith("framework/"):
        return "framework"
    if path.startswith("promotion/"):
        return "promotion"
    if path == "Makefile":
        return "makefile"
    return "other"


TOKEN_SPLIT_RE = re.compile(r"[^a-z0-9]+")


def _path_tokens(path: str) -> set[str]:
    stem = Path(path).stem.lower()
    parts = TOKEN_SPLIT_RE.split(stem)
    return {p for p in parts if p}


def _family_key(path: str) -> str:
    """Coarse grouping key used to preserve companion diversity."""
    tokens = sorted(_path_tokens(path))
    if tokens:
        return tokens[0]
    return Path(path).stem.lower()


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
    modification_terms = {
        "add",
        "improve",
        "better",
        "update",
        "fix",
        "enhance",
        "change",
        "modify",
        "refactor",
        "docstring",
        "documentation",
        "comment",
    }
    doc_hits = sum(1 for t in lowered if any(t.startswith(term) for term in doc_terms))
    code_hits = sum(1 for t in lowered if any(t.startswith(term) for term in code_terms))
    modification_hits = sum(1 for t in lowered if any(t.startswith(term) for term in modification_terms))

    # If query has modification intent (add, improve, fix, etc) + code-related context,
    # treat as modification task to boost target-specific files over tangentially related ones
    # Expand detection: code objects (function/class), code-related terms (validation/handling/logic/algorithm),
    # or manager/system/handler files all indicate code being modified
    code_object_terms = {"function", "method", "class", "module", "variable", "parameter", "handler", "manager"}
    code_context_terms = {"validation", "handling", "logic", "algorithm", "error", "exception", "event", "state", "processing"}
    code_other_terms = {"script", "code", "feature", "implementation", "executor", "classifier", "performance", "optimization"}
    # Common framework/code-related tokens to detect code context
    code_hints = {"factory", "schema", "runtime", "engine", "request", "task"}

    # Check if any token contains a code-related term (substring match, not exact)
    has_code_object = any(term in token for token in lowered for term in code_object_terms)
    has_code_context = any(term in lowered for term in code_context_terms)
    has_code_other = any(term in lowered for term in code_other_terms)
    has_code_hint = any(hint in token.lower() for token in lowered for hint in code_hints)

    has_code_signal = has_code_object or has_code_context or has_code_other or has_code_hint
    if modification_hits >= 1 and has_code_signal:
        return "modification"

    if code_hits > doc_hits:
        return "code"
    if doc_hits > code_hits:
        return "docs"
    return "mixed"


def _domain_bonus(*, intent: str, domain: str) -> float:
    if intent == "modification":
        # For modification tasks, strongly prefer core library/framework files over tools/tests
        return {
            "framework": 2.25,  # Core framework classes are prime modification targets
            "promotion": 1.85,  # Promotion system is also legitimate target
            "other": 1.45,      # artifacts/ and other actual code
            "tests": 0.55,      # test files can be targets but less likely
            "bin": -2.15,       # Heavy penalty: bin files are tooling/scripts, not modification targets
            "docs": -1.85,
            "makefile": -1.25,
        }.get(domain, 1.45)
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


def _is_modification_target(path: str) -> bool:
    """Detect if a path looks like a modification target (actual code, not test tooling)."""
    # Core library/framework files are the prime modification targets
    if path.startswith("framework/"):
        return True
    # Promotion system is legitimate target
    if path.startswith("promotion/"):
        return True
    # Artifacts and explicitly created test directories are likely targets
    if path.startswith("artifacts/"):
        return True
    # Shell scripts are sometimes targets but less likely than code
    if path.startswith("shell/") and not path.startswith("shell/test"):
        return True
    # Exclude bin/ (mostly tooling/tests), docs/, tests/ by default
    return False


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
    path: str = "",
) -> float:
    # For modification tasks, lane alignment is less critical; file targeting is critical
    if intent == "modification":
        lane_bonus = 0.5 if lane_aligned else -0.5
        # Strong boost for files that look like modification targets
        target_bonus = 3.2 if _is_modification_target(path) else -1.8
        # Git history suggests active development (more likely target)
        git_bonus = git_history_count * 0.35
        companion_bonus = (min(related_count, 2) * 0.12) + (sibling_count * 0.08)
        related_preview_bonus = min(related_score / 420.0, 0.8)
        domain_intent_bonus = _domain_bonus(intent=intent, domain=domain)
        return round(base_score + lane_bonus + target_bonus + git_bonus + companion_bonus + related_preview_bonus + domain_intent_bonus, 4)

    # Original scoring for code/docs intents
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
    query_tokens: set[str],
    max_targets: int,
) -> list[dict[str, Any]]:
    """Inject lane-aligned companions discovered through related links.

    This keeps expansion bounded and diverse:
    - weakly linked companions are rejected,
    - only one synthetic companion per family is retained.
    """
    by_path = {t["path"]: t for t in targets}
    support_count: dict[str, int] = {}
    for primary in lane_targets:
        for rel_path in primary.get("selection_reason", {}).get("related_paths", []):
            if rel_path:
                support_count[rel_path] = support_count.get(rel_path, 0) + 1

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

            rel_tokens = _path_tokens(rel_path)
            primary_tokens = _path_tokens(primary["path"])
            overlap_tokens = sorted((rel_tokens & primary_tokens) | (rel_tokens & query_tokens))
            link_strength = 0
            if overlap_tokens:
                link_strength += 1
            if _family_key(rel_path) == _family_key(primary["path"]):
                link_strength += 1
            if support_count.get(rel_path, 0) >= 2:
                link_strength += 1
            if link_strength < 2:
                continue

            domain = _path_domain(rel_path)
            # Keep synthetic companions safely below direct retrieval hits.
            synthetic_score = round(primary_score - 1.6 + (0.12 * min(link_strength, 3)), 4)
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
                        "companion_support": support_count.get(rel_path, 1),
                        "companion_link_strength": link_strength,
                        "link_tokens": overlap_tokens,
                    },
                }
                continue
            existing["rank_score"] = max(float(existing.get("rank_score", 0.0)), synthetic_score)
            reason = existing.setdefault("selection_reason", {})
            supports = reason.setdefault("companion_of", [])
            if primary["path"] not in supports:
                supports.append(primary["path"])
                reason["companion_support"] = int(reason.get("companion_support", 0)) + 1
            reason["companion_link_strength"] = max(int(reason.get("companion_link_strength", 1)), link_strength)
            if overlap_tokens:
                existing_tokens = set(reason.get("link_tokens", []))
                reason["link_tokens"] = sorted(existing_tokens | set(overlap_tokens))

    if not companion_pool:
        return targets
    # Retain at most one synthetic companion per family to avoid same-module crowding.
    kept_companions: list[dict[str, Any]] = []
    seen_families: set[str] = set()
    sorted_companions = sorted(
        companion_pool.values(),
        key=lambda item: (
            int(item.get("selection_reason", {}).get("companion_link_strength", 0)),
            int(item.get("selection_reason", {}).get("companion_support", 0)),
            float(item.get("rank_score", 0.0)),
        ),
        reverse=True,
    )
    max_companions = max(0, max_targets // 2)
    for companion in sorted_companions:
        family = _family_key(companion["path"])
        if family in seen_families:
            continue
        seen_families.add(family)
        kept_companions.append(companion)
        if len(kept_companions) >= max_companions:
            break

    targets.extend(kept_companions)
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
    query_tokens = {t.lower() for t in args.query if t}
    search_top = args.top
    if preferred_prefixes and intent == "code":
        # Broaden retrieval for code-intent lane runs so we can recover more
        # lane-aligned candidates without emitting out-of-lane targets.
        search_top = max(args.top, args.max_targets * 4)
    elif intent == "modification":
        # Broaden retrieval for modification queries to capture actual modification targets
        # that might not rank high in token-based search but should be ranked high
        # by domain/path bonuses (e.g., framework/ files vs test/bin files)
        search_top = max(args.top, 24)
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
            path=path,
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
    # For modification intent, rank by score; for code intent, prioritize lane-alignment.
    if intent == "modification":
        # Sort purely by ranking score for modification tasks, ignoring lane alignment
        targets = sorted(
            deduped.values(),
            key=lambda item: (item["rank_score"], item["path"]),
            reverse=True,
        )
    else:
        # For code/docs intent, lane alignment is important
        targets = sorted(
            deduped.values(),
            key=lambda item: (int(item.get("lane_aligned", False)), item["rank_score"], item["path"]),
            reverse=True,
        )
    _calibrate_confidences(targets)

    # Secondary sort for determinism
    if intent == "modification":
        targets = sorted(
            targets,
            key=lambda item: (item["rank_score"], item["confidence"], item["path"]),
            reverse=True,
        )
    else:
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
                query_tokens=query_tokens,
                max_targets=args.max_targets,
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
            "ranking_version": "rag4-v3-lane-link-diverse",
        },
        "raw_payload": search_payload,
    }

    append_log(plan)
    json.dump(plan, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
