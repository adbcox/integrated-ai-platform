"""RM-OPS-007 archive convergence logic.

Determines which completed ready_for_archive items can be moved to archived state using
explicit evidence checks, applies updates, and emits machine-readable decisions.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

TERMINAL_STATUSES = {"completed", "complete"}
VALIDATION_OK = {"passed", "complete", "completed"}
EXECUTION_BLOCKED = {"not_started", "in_progress", "planned", "pending"}


@dataclass
class ArchiveDecision:
    item_id: str
    action: str  # archived | hold
    reason: str

    def to_dict(self) -> dict[str, str]:
        return {"item_id": self.item_id, "action": self.action, "reason": self.reason}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def load_item(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def is_archive_candidate(item: dict[str, Any]) -> bool:
    return normalize(item.get("status")) in TERMINAL_STATUSES and normalize(item.get("archive_status")) == "ready_for_archive"


def evidence_allows_archive(item: dict[str, Any]) -> tuple[bool, str]:
    validation = item.get("validation") or {}
    execution = item.get("execution") or {}
    archive_readiness = item.get("archive_readiness") or {}

    validation_status = normalize(validation.get("validation_status"))
    execution_status = normalize(execution.get("execution_status"))
    item_complete = validation.get("item_complete_evidence") is True
    archive_ready = archive_readiness.get("ready") is True

    if execution_status in EXECUTION_BLOCKED:
        return False, f"execution_status={execution.get('execution_status')}"

    if item_complete or validation_status in VALIDATION_OK or archive_ready:
        return True, "evidence_sufficient"

    return False, "insufficient_validation_or_readiness_evidence"


def update_item_for_archive(item: dict[str, Any], today_iso: str) -> dict[str, Any]:
    item["archive_status"] = "archived"
    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        metadata["updated_at"] = today_iso
    return item


def archive_converge_items(
    items_dir: Path,
    *,
    apply_changes: bool,
    today_iso: str,
) -> tuple[list[ArchiveDecision], list[str]]:
    decisions: list[ArchiveDecision] = []
    archived_ids: list[str] = []

    for item_path in sorted(items_dir.glob("RM-*.yaml")):
        item = load_item(item_path)
        item_id = str(item.get("id") or item_path.stem)

        if not is_archive_candidate(item):
            continue

        allowed, reason = evidence_allows_archive(item)
        if allowed:
            decisions.append(ArchiveDecision(item_id=item_id, action="archived", reason=reason))
            archived_ids.append(item_id)
            if apply_changes:
                updated = update_item_for_archive(item, today_iso)
                item_path.write_text(yaml.safe_dump(updated, sort_keys=False, allow_unicode=False), encoding="utf-8")
        else:
            decisions.append(ArchiveDecision(item_id=item_id, action="hold", reason=reason))

    return decisions, archived_ids


def sync_registry_and_sync_state(
    *,
    registry_path: Path,
    sync_state_path: Path,
    item_status_by_id: dict[str, dict[str, str]],
) -> None:
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8")) or {}
    for row in registry.get("items", []):
        item_id = str(row.get("id") or "")
        truth = item_status_by_id.get(item_id)
        if truth:
            row["status"] = truth["status"]
            row["archive_status"] = truth["archive_status"]

    sync = yaml.safe_load(sync_state_path.read_text(encoding="utf-8")) or {}
    for row in sync.get("items", []):
        item_id = str(row.get("id") or "")
        truth = item_status_by_id.get(item_id)
        if truth:
            if truth["status"]:
                row["status"] = truth["status"]
            row["archive_status"] = truth["archive_status"]

    registry_path.write_text(yaml.safe_dump(registry, sort_keys=False, allow_unicode=False), encoding="utf-8")
    sync_state_path.write_text(yaml.safe_dump(sync, sort_keys=False, allow_unicode=False), encoding="utf-8")


def collect_item_status(items_dir: Path) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for item_path in sorted(items_dir.glob("RM-*.yaml")):
        item = load_item(item_path)
        item_id = str(item.get("id") or item_path.stem)
        result[item_id] = {
            "status": str(item.get("status") or ""),
            "archive_status": str(item.get("archive_status") or ""),
        }
    return result
