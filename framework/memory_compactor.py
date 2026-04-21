"""Memory compactor for LocalMemoryStore JSONL persistence.

Reads append-only failure_patterns.jsonl and success_patterns.jsonl, deduplicates
by natural key, merges recurrence/reuse counts, and rewrites atomically via .tmp rename.
Produces a MemoryCompactionResult artifact.

Compaction is separate from LocalMemoryStore append behavior — it does not touch
the store's write paths.
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from framework.local_memory_store import FailurePattern, LocalMemoryStore, SuccessPattern

# -- import-time assertions --
assert callable(LocalMemoryStore.read_failures), "INTERFACE MISMATCH: LocalMemoryStore.read_failures"
assert callable(LocalMemoryStore.read_successes), "INTERFACE MISMATCH: LocalMemoryStore.read_successes"
assert callable(LocalMemoryStore.query_failures), "INTERFACE MISMATCH: LocalMemoryStore.query_failures"
assert callable(LocalMemoryStore.query_successes), "INTERFACE MISMATCH: LocalMemoryStore.query_successes"
assert "recurrence_count" in FailurePattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: FailurePattern.recurrence_count"
assert "reuse_count" in SuccessPattern.__dataclass_fields__, \
    "INTERFACE MISMATCH: SuccessPattern.reuse_count"


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class MemoryCompactionResult:
    failures_before: int
    failures_after: int
    successes_before: int
    successes_after: int
    compacted_at: str
    dry_run: bool


def compact_failure_patterns(
    memory_store: LocalMemoryStore,
    *,
    dry_run: bool = False,
) -> MemoryCompactionResult:
    """Deduplicate failure patterns by natural key, summing recurrence_count."""
    records = memory_store.read_failures()
    before = len(records)

    merged: dict[tuple, FailurePattern] = {}
    for r in records:
        key = (r.task_kind, r.error_type, r.old_string_prefix)
        if key in merged:
            existing = merged[key]
            merged[key] = dataclasses.replace(
                existing,
                recurrence_count=existing.recurrence_count + r.recurrence_count,
                recorded_at=max(existing.recorded_at, r.recorded_at),
            )
        else:
            merged[key] = r

    after = len(merged)

    if not dry_run and before > 0:
        path = memory_store._failure_path
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            "\n".join(json.dumps(dataclasses.asdict(p), ensure_ascii=False) for p in merged.values()),
            encoding="utf-8",
        )
        tmp.rename(path)

    return MemoryCompactionResult(
        failures_before=before,
        failures_after=after,
        successes_before=0,
        successes_after=0,
        compacted_at=_iso_now(),
        dry_run=dry_run,
    )


def compact_success_patterns(
    memory_store: LocalMemoryStore,
    *,
    dry_run: bool = False,
) -> MemoryCompactionResult:
    """Deduplicate success patterns by natural key, summing reuse_count."""
    records = memory_store.read_successes()
    before = len(records)

    merged: dict[tuple, SuccessPattern] = {}
    for r in records:
        key = (r.task_kind, r.target_file_suffix, r.old_string_prefix)
        if key in merged:
            existing = merged[key]
            merged[key] = dataclasses.replace(
                existing,
                reuse_count=existing.reuse_count + r.reuse_count,
                recorded_at=max(existing.recorded_at, r.recorded_at),
            )
        else:
            merged[key] = r

    after = len(merged)

    if not dry_run and before > 0:
        path = memory_store._success_path
        tmp = path.with_suffix(".tmp")
        tmp.write_text(
            "\n".join(json.dumps(dataclasses.asdict(p), ensure_ascii=False) for p in merged.values()),
            encoding="utf-8",
        )
        tmp.rename(path)

    return MemoryCompactionResult(
        failures_before=0,
        failures_after=0,
        successes_before=before,
        successes_after=after,
        compacted_at=_iso_now(),
        dry_run=dry_run,
    )


def compact_memory(
    memory_store: LocalMemoryStore,
    *,
    dry_run: bool = False,
) -> MemoryCompactionResult:
    """Compact both failure and success patterns, returning combined counts."""
    f_result = compact_failure_patterns(memory_store, dry_run=dry_run)
    s_result = compact_success_patterns(memory_store, dry_run=dry_run)

    return MemoryCompactionResult(
        failures_before=f_result.failures_before,
        failures_after=f_result.failures_after,
        successes_before=s_result.successes_before,
        successes_after=s_result.successes_after,
        compacted_at=_iso_now(),
        dry_run=dry_run,
    )


__all__ = [
    "MemoryCompactionResult",
    "compact_failure_patterns",
    "compact_success_patterns",
    "compact_memory",
]
