"""Bounded failure-retention helpers used by manager preflight paths."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STAGE4_TRACE = REPO_ROOT / "artifacts" / "stage4_manager" / "traces.jsonl"


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def message_has_target_ref(message: str, target: str) -> bool:
    name = Path(target).name
    return target in message or name in message


@dataclass(frozen=True)
class MemoryDecision:
    target: str
    lane: str
    failures_by_class: dict[str, int]
    successes: int
    missing_file_ref_risk: bool
    literal_shell_risky_risk: bool
    should_force_anchor: bool
    should_reroute_manual: bool
    reason: str | None = None


def _read_stage4_rows(
    *,
    lane: str,
    target: str,
    manifest_version: int | None,
    window_days: int,
    trace_path: Path = DEFAULT_STAGE4_TRACE,
) -> list[dict[str, Any]]:
    if not trace_path.exists():
        return []
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=max(1, window_days))
    rows: list[dict[str, Any]] = []
    with trace_path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("promotion_lane") != lane:
                continue
            if row.get("target_file") != target:
                continue
            if manifest_version is not None and str(row.get("promotion_manifest_version")) != str(manifest_version):
                continue
            ts = _parse_timestamp(row.get("timestamp"))
            if ts is None or ts < cutoff:
                continue
            rows.append(row)
    return rows


def assess_target_risk(
    *,
    lane: str,
    target: str,
    message: str,
    manifest_version: int | None,
    retry_class: str | None = None,
    window_days: int = 7,
) -> MemoryDecision:
    rows = _read_stage4_rows(
        lane=lane,
        target=target,
        manifest_version=manifest_version,
        window_days=window_days,
    )
    failures_by_class: dict[str, int] = {}
    successes = 0
    for row in rows:
        if row.get("accepted"):
            successes += 1
            continue
        failure_class = str(row.get("final_tag") or row.get("classification") or "unknown")
        failures_by_class[failure_class] = failures_by_class.get(failure_class, 0) + 1

    msg_lower = message.lower()
    target_lower = target.lower()
    is_shell_target = target_lower.endswith(".sh")
    has_literal_replace = "replace exact text" in msg_lower
    has_shell_control_markers = any(
        marker in msg_lower
        for marker in (
            "set -e",
            "set -u",
            "set -o pipefail",
            "trap ",
            " ifs=",
            "#!/usr/bin/env bash",
            "readonly ",
        )
    )

    missing_file_ref_risk = failures_by_class.get("missing_file_ref", 0) > 0
    literal_shell_risky_risk = failures_by_class.get("literal_shell_risky", 0) > 0 or (
        is_shell_target and has_literal_replace and has_shell_control_markers
    )

    should_force_anchor = not message_has_target_ref(message, target) or missing_file_ref_risk
    should_reroute_manual = lane == "candidate" and literal_shell_risky_risk and retry_class in {
        None,
        "",
        "none",
        "fallback_on_failure",
    }

    reason = None
    if should_reroute_manual:
        reason = "failure_memory literal_shell_risky"
    elif should_force_anchor and missing_file_ref_risk:
        reason = "failure_memory missing_file_ref"

    return MemoryDecision(
        target=target,
        lane=lane,
        failures_by_class=failures_by_class,
        successes=successes,
        missing_file_ref_risk=missing_file_ref_risk,
        literal_shell_risky_risk=literal_shell_risky_risk,
        should_force_anchor=should_force_anchor,
        should_reroute_manual=should_reroute_manual,
        reason=reason,
    )

