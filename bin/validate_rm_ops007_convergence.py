#!/usr/bin/env python3
"""Validate RM-OPS-007 convergence outcomes and archive truth alignment."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
ITEMS_DIR = REPO_ROOT / "docs/roadmap/items"
REPORT_PATH = REPO_ROOT / "artifacts/operations/rm_ops007_archive_convergence_report.json"
OUTPUT_PATH = REPO_ROOT / "artifacts/validation/rm_ops007_convergence_validation.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def main() -> int:
    errors: list[str] = []

    if not REPORT_PATH.exists():
        errors.append("missing convergence report artifact")
        report = {}
    else:
        report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

    if report:
        if report.get("run_kind") != "rm_ops007_archive_convergence":
            errors.append("invalid run_kind in convergence report")
        if report.get("derived_refresh_code") not in (0, None):
            errors.append(f"derived_refresh_code={report.get('derived_refresh_code')}")

    item_truth: dict[str, str] = {}
    for p in sorted(ITEMS_DIR.glob("RM-*.yaml")):
        d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        item_truth[str(d.get("id") or p.stem)] = str(d.get("archive_status") or "")

    for row in report.get("decisions", []):
        item_id = row.get("item_id")
        action = row.get("action")
        archive_status = item_truth.get(str(item_id), "")
        if action == "archived" and archive_status != "archived":
            errors.append(f"{item_id}: decision archived but canonical archive_status={archive_status!r}")
        if action == "hold" and archive_status == "archived":
            errors.append(f"{item_id}: decision hold but canonical archive_status became archived")

    result = {
        "generated_at": now_iso(),
        "status": "PASS" if not errors else "FAIL",
        "error_count": len(errors),
        "errors": errors,
        "report_ref": str(REPORT_PATH.relative_to(REPO_ROOT)),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
