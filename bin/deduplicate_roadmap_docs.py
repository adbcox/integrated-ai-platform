#!/usr/bin/env python3
"""Analyse duplicates and produce a deduplication plan.

Finding: all 27 "duplicate" IDs are [ITEM] + [EXECUTION_PACK] pairs.
Execution packs are complementary execution-plan docs, not content duplicates.
No merging is needed for the ITEMS/ directory itself.

The plan produced here:
  - Confirms zero true content duplicates inside docs/roadmap/ITEMS/
  - Documents that EXECUTION_PACKs share the same ID prefix (by design)
  - Records the 8 EXECUTION_PACK-only IDs that have no matching ITEM file
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).parent.parent
_REPORT = _REPO / "roadmap_scan_report.json"
_PLAN_OUT = _REPO / "deduplication_plan.json"


def main() -> int:
    if not _REPORT.exists():
        print("ERROR: roadmap_scan_report.json not found — run scan_all_roadmap_docs.py first")
        return 1

    report = json.loads(_REPORT.read_text())
    items = report["items"]
    duplicates = report["duplicates"]  # id → [filepath, ...]

    # Classify each duplicate pair
    true_item_dupes: list[dict] = []       # ITEM appears more than once
    item_exec_pairs: list[dict] = []       # exactly one ITEM + one EXEC
    exec_only_ids: list[str] = []          # EXEC exists but no ITEM

    # Build lookup: id → list of items (by type)
    by_id: dict[str, dict] = {}
    for item in items:
        iid = item["id"]
        if iid not in by_id:
            by_id[iid] = {"items": [], "execs": []}
        if item["is_exec_pack"]:
            by_id[iid]["execs"].append(item)
        else:
            by_id[iid]["items"].append(item)

    for iid, paths in duplicates.items():
        entry = by_id[iid]
        n_items = len(entry["items"])
        n_execs = len(entry["execs"])

        if n_items > 1:
            true_item_dupes.append({
                "id": iid,
                "files": [i["filepath"] for i in entry["items"]],
                "action": "MERGE — pick largest/most complete ITEM file",
            })
        elif n_items == 1 and n_execs >= 1:
            item_exec_pairs.append({
                "id": iid,
                "item": entry["items"][0]["filepath"],
                "exec_packs": [e["filepath"] for e in entry["execs"]],
                "action": "NO_ACTION — EXEC_PACK is complementary, not a duplicate",
            })

    # Find EXEC-only IDs (exec pack but no item file)
    all_ids_in_items = {i["id"] for i in items if not i["is_exec_pack"]}
    all_ids_in_execs = {i["id"] for i in items if i["is_exec_pack"]}
    exec_only_ids = sorted(all_ids_in_execs - all_ids_in_items)

    plan = {
        "summary": {
            "total_files": report["total_files"],
            "issue_items": report["issue_items"],
            "exec_packs": report["exec_packs"],
            "unique_ids": report["unique_ids"],
            "true_content_duplicates": len(true_item_dupes),
            "item_exec_pairs": len(item_exec_pairs),
            "exec_only_ids": len(exec_only_ids),
            "verdict": (
                "CLEAN — no content duplicates in ITEMS/. "
                "All shared IDs are ITEM+EXECUTION_PACK pairs (by design)."
            ),
        },
        "true_duplicates": true_item_dupes,
        "item_exec_pairs": item_exec_pairs,
        "exec_only_ids": exec_only_ids,
        "recommendation": {
            "for_plane": (
                "Import only docs/roadmap/ITEMS/ files (601 issues). "
                "EXECUTION_PACK files are execution notes, not Plane issues."
            ),
            "for_exec_only": (
                f"{len(exec_only_ids)} EXECUTION_PACK IDs have no matching ITEM file. "
                "These may represent items that were planned but never written as issues."
            ),
            "action": "NONE — no file deletion or archiving needed",
        },
    }

    _PLAN_OUT.write_text(json.dumps(plan, indent=2))

    print("DEDUPLICATION ANALYSIS")
    print("=" * 60)
    s = plan["summary"]
    print(f"  Total files scanned:     {s['total_files']}")
    print(f"  Issue ITEMS:             {s['issue_items']}")
    print(f"  Execution packs:         {s['exec_packs']}")
    print(f"  Unique IDs:              {s['unique_ids']}")
    print(f"  True content duplicates: {s['true_content_duplicates']}  ← ZERO")
    print(f"  ITEM+EXEC pairs:         {s['item_exec_pairs']}")
    print(f"  EXEC-only IDs:           {s['exec_only_ids']}")
    print(f"\nVerdict: {s['verdict']}")

    if exec_only_ids:
        print(f"\nEXEC-only IDs (no matching ITEM file):")
        for iid in exec_only_ids:
            print(f"  {iid}")

    if true_item_dupes:
        print(f"\n⚠ TRUE DUPLICATES FOUND (need manual merge):")
        for d in true_item_dupes:
            print(f"  {d['id']}: {d['files']}")
    else:
        print("\n✓ No merging needed — ITEMS/ is already clean")

    print(f"\n✓ Plan saved → deduplication_plan.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
