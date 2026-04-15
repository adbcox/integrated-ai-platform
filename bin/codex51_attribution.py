#!/usr/bin/env python3
"""Deterministic attribution counters for Codex 5.1 replacement artifacts."""

from __future__ import annotations

import json
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from _datetime_compat import UTC
from pathlib import Path
from typing import Any

ATTRIBUTION_BUCKETS = [
    "local_primary",
    "local_with_manager_rescue",
    "local_with_rag_assist",
    "local_with_guard_prevention",
    "codex_or_manual_primary",
    "mixed_or_shared",
]


@dataclass
class AttributionSignals:
    success: bool
    rescue_count: int
    escalation_count: int
    guard_count: int
    ranking_version: str


def classify_attribution_bucket(signals: AttributionSignals) -> str:
    rescue = int(signals.rescue_count)
    escalate = int(signals.escalation_count)
    guard = int(signals.guard_count)
    success = bool(signals.success)
    ranking = str(signals.ranking_version or "")

    if escalate > 0 and rescue > 0:
        return "mixed_or_shared"
    if escalate > 0:
        return "codex_or_manual_primary"
    if rescue > 0:
        return "local_with_manager_rescue"
    if guard > 0:
        return "local_with_guard_prevention"
    if success and ranking.startswith("rag"):
        return "local_with_rag_assist"
    if success:
        return "local_primary"
    return "mixed_or_shared"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _iso_to_git_time(value: str | None) -> str | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S +0000")


def exact_campaign_commit_hashes(
    *,
    repo_root: Path,
    task_id: str,
    profile: str,
    started_at_utc: str | None,
    finished_at_utc: str | None,
) -> list[str]:
    prefix = f"^campaign:{task_id}:{profile}"
    since_value = _iso_to_git_time(started_at_utc)
    until_value = _iso_to_git_time(finished_at_utc)
    cmd = [
        "git",
        "log",
        "--format=%H",
        f"--grep={prefix}",
    ]
    if since_value:
        cmd.append(f"--since={since_value}")
    if until_value:
        cmd.append(f"--until={until_value}")
    proc = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return []
    hashes = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return sorted(set(hashes))


def _extract_plan_families(plan_payload: dict[str, Any], statuses: list[dict[str, Any]]) -> list[str]:
    families: set[str] = set()
    strategy_decisions = plan_payload.get("manager_decisions", {}).get("strategy_decisions", {})
    if isinstance(strategy_decisions, dict):
        for entry in strategy_decisions.values():
            if isinstance(entry, dict):
                fam = str(entry.get("family") or "").strip()
                if fam:
                    families.add(fam)
    for row in statuses:
        if not isinstance(row, dict):
            continue
        dec = row.get("strategy_decision") if isinstance(row.get("strategy_decision"), dict) else {}
        fam = str(dec.get("family") or "").strip()
        if fam:
            families.add(fam)
    return sorted(families)


def enrich_run_row(
    *,
    row: dict[str, Any],
    repo_root: Path,
    plan_payload: dict[str, Any] | None = None,
    statuses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    payload = dict(row)
    signals = AttributionSignals(
        success=bool(payload.get("success")),
        rescue_count=int(payload.get("rescue_count") or 0),
        escalation_count=int(payload.get("escalation_count") or 0),
        guard_count=int(payload.get("guard_count") or 0),
        ranking_version=str(payload.get("ranking_version") or ""),
    )
    bucket = classify_attribution_bucket(signals)
    payload["attribution_bucket"] = bucket

    families: list[str] = []
    if isinstance(plan_payload, dict):
        families = _extract_plan_families(plan_payload, statuses or [])
    payload["families"] = families

    commit_hashes: list[str] = []
    task_id = str(payload.get("task_id") or "")
    profile = str(payload.get("attribution_profile") or "normal")
    if task_id:
        commit_hashes = exact_campaign_commit_hashes(
            repo_root=repo_root,
            task_id=task_id,
            profile=profile,
            started_at_utc=str(payload.get("started_at_utc") or ""),
            finished_at_utc=str(payload.get("timestamp_utc") or ""),
        )
    payload["accepted_commit_hashes_exact"] = commit_hashes
    payload["accepted_commit_count_exact"] = len(commit_hashes)
    return payload


def aggregate_attribution(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bucket_counts = {key: 0 for key in ATTRIBUTION_BUCKETS}
    success_by_bucket = {key: 0 for key in ATTRIBUTION_BUCKETS}
    family_counts: dict[str, dict[str, int]] = defaultdict(lambda: {key: 0 for key in ATTRIBUTION_BUCKETS})

    run_count = len(rows)
    success_count = 0
    rescue_count = 0
    escalation_count = 0
    guard_count = 0
    first_attempt_success_count = 0
    accepted_commit_count_exact = 0

    for row in rows:
        bucket = str(row.get("attribution_bucket") or "mixed_or_shared")
        if bucket not in bucket_counts:
            bucket = "mixed_or_shared"
        bucket_counts[bucket] += 1

        success = bool(row.get("success"))
        if success:
            success_count += 1
            success_by_bucket[bucket] += 1
        rescue_count += int(row.get("rescue_count") or 0)
        escalation_count += int(row.get("escalation_count") or 0)
        guard_count += int(row.get("guard_count") or 0)
        if float(row.get("first_attempt_quality_rate") or 0.0) >= 1.0:
            first_attempt_success_count += 1

        accepted_commit_count_exact += int(row.get("accepted_commit_count_exact") or 0)
        for fam in row.get("families") or []:
            fam_key = str(fam or "").strip()
            if not fam_key:
                continue
            family_counts[fam_key][bucket] += 1

    local_share_numerator = (
        bucket_counts["local_primary"]
        + bucket_counts["local_with_manager_rescue"]
        + bucket_counts["local_with_rag_assist"]
        + bucket_counts["local_with_guard_prevention"]
    )
    codex_manual_share_numerator = bucket_counts["codex_or_manual_primary"]

    def _rate(n: int, d: int) -> float:
        if d <= 0:
            return 0.0
        return round(n / d, 3)

    return {
        "run_count": run_count,
        "task_count": run_count,
        "success_count": success_count,
        "accepted_commit_count_exact": accepted_commit_count_exact,
        "rescue_count": rescue_count,
        "escalation_count": escalation_count,
        "guard_count": guard_count,
        "first_attempt_success_count": first_attempt_success_count,
        "attribution_bucket_counts": bucket_counts,
        "success_by_bucket": success_by_bucket,
        "family_attribution_counts": dict(family_counts),
        "local_share_rate": _rate(local_share_numerator, run_count),
        "codex_or_manual_share_rate": _rate(codex_manual_share_numerator, run_count),
        "mixed_or_shared_rate": _rate(bucket_counts["mixed_or_shared"], run_count),
    }


def write_attribution_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summarize_buckets(rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("attribution_bucket") or "mixed_or_shared") for row in rows)
    return {key: int(counter.get(key, 0)) for key in ATTRIBUTION_BUCKETS}
