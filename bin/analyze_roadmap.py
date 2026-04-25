#!/usr/bin/env python3
"""Roadmap analyzer — score pending items and recommend execution order.

Usage:
    python3 bin/analyze_roadmap.py                    # quick-wins (default)
    python3 bin/analyze_roadmap.py --mode training-data
    python3 bin/analyze_roadmap.py --mode dependencies
    python3 bin/analyze_roadmap.py --top 30

Output includes a ready-to-paste --filter argument for auto_execute_roadmap.py.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ITEMS_DIR = REPO_ROOT / "docs" / "roadmap" / "ITEMS"

# Must match auto_execute_roadmap.py exactly:
#   EXECUTION_READY_STATUSES = ["Accepted", "Planned"]
#   READY_READINESS           = ["now", "near", "later"]
PENDING_STATUSES   = {"Accepted", "Planned"}
READY_READINESS    = {"now", "near", "later"}

# ── Scoring ───────────────────────────────────────────────────────────────────
# LOE maps to base easiness score
LOE_SCORE = {"S": 10, "M": 7, "L": 3, "XL": 1}

# Execution risk field (1=low … 5=high) — subtract from score
# risk 1-2: good, risk 4-5: bad
def _risk_bonus(risk: int) -> int:
    if risk <= 2: return 2
    if risk >= 4: return -2
    return 0


@dataclass
class Item:
    id: str
    title: str
    category: str
    status: str
    loe: str
    risk: int
    priority: str
    deps: list[str]          # RM-* IDs this item depends on
    file_hints: list[str]    # .py paths mentioned in Expected file families

    @property
    def base_score(self) -> int:
        return LOE_SCORE.get(self.loe, 1)

    @property
    def easiness(self) -> int:
        s = self.base_score
        s += _risk_bonus(self.risk)
        if self.priority == "High": s += 1
        # Title hints at file-creation tasks
        low = self.title.lower()
        if any(w in low for w in ("create", "add", "implement", "integrate", "build")):
            s += 1
        return max(1, s)

    @property
    def training_score(self) -> int:
        """Score for generating clean training data (small new files preferred)."""
        s = self.easiness
        # S-LOE items that create new .py files are the gold standard
        if self.loe == "S" and self.file_hints:
            s += 3
        if self.loe == "M" and self.file_hints:
            s += 1
        return s

    # unlocks_count set externally after reverse-dep analysis
    unlocks_count: int = field(default=0, repr=False)


# ── Parsing ───────────────────────────────────────────────────────────────────

def _field(text: str, name: str) -> str:
    m = re.search(rf"\*\*{name}:\*\*\s*`([^`]+)`", text)
    return m.group(1).strip() if m else ""


def load_items() -> list[Item]:
    items = []
    for md in sorted(ITEMS_DIR.glob("*.md")):
        text = md.read_text()
        status = _field(text, "Status")
        if status not in PENDING_STATUSES:
            continue
        readiness = _field(text, "Readiness")
        if readiness not in READY_READINESS:
            continue

        item_id = _field(text, "ID") or md.stem
        title   = re.search(r"\*\*Title:\*\*\s*(.+)", text)
        title   = title.group(1).strip() if title else item_id

        try:
            risk = int(_field(text, "Execution risk"))
        except ValueError:
            risk = 3

        # Dependencies: RM-* IDs anywhere in text except the item's own ID
        all_refs = set(re.findall(r"`(RM-[A-Z0-9/-]+)`", text))
        deps = sorted(all_refs - {item_id})

        # File hints: .py paths in Expected file families section
        files_section = re.search(r"## Expected file families(.+?)(?:^##|\Z)", text, re.S | re.M)
        file_hints = re.findall(r"`([^`]+\.py)`", files_section.group(1)) if files_section else []

        items.append(Item(
            id=item_id,
            title=title,
            category=_field(text, "Category"),
            status=status,
            loe=_field(text, "LOE") or "M",
            risk=risk,
            priority=_field(text, "Priority"),
            deps=deps,
            file_hints=file_hints,
        ))
    return items


def _pending_ids(items: list[Item]) -> set[str]:
    return {it.id for it in items}


def annotate_unlocks(items: list[Item]) -> None:
    """Set item.unlocks_count = number of other pending items that depend on it."""
    pending = _pending_ids(items)
    by_id = {it.id: it for it in items}
    # For each item, count how many pending items list it as a dep
    reverse: dict[str, int] = {it.id: 0 for it in items}
    for it in items:
        for dep in it.deps:
            if dep in reverse:
                reverse[dep] += 1
    for it in items:
        it.unlocks_count = reverse[it.id]


# ── Output helpers ────────────────────────────────────────────────────────────

def _filter_arg(ids: list[str]) -> str:
    return "|".join(ids)


def _print_section(title: str, items: list[Item], attr: str, n: int) -> list[Item]:
    top = items[:n]
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")
    for i, it in enumerate(top, 1):
        score = getattr(it, attr)
        deps_note = f"  [{it.unlocks_count} unlock]" if it.unlocks_count else ""
        dep_warn  = f"  ⚠ needs: {','.join(it.deps[:2])}" if it.deps else ""
        print(f"  {i:2d}. [{score:2d}pt] {it.id:<18} LOE={it.loe} risk={it.risk}  {it.title[:45]}{deps_note}{dep_warn}")
    return top


def _paste_block(label: str, ids: list[str]) -> None:
    filter_str = _filter_arg(ids)
    print(f"\n  → Paste to run:")
    print(f"    python3 bin/auto_execute_roadmap.py --filter \"{filter_str}\" --max-items {len(ids)}")


# ── Modes ─────────────────────────────────────────────────────────────────────

def mode_quick_wins(items: list[Item], top_n: int) -> None:
    pending_ids = _pending_ids(items)
    # No pending dependencies = true quick wins
    no_dep = [it for it in items if not any(d in pending_ids for d in it.deps)]
    ranked = sorted(no_dep, key=lambda x: x.easiness, reverse=True)

    print(f"\n  Total pending: {len(items)}  |  No-dependency items: {len(no_dep)}")
    selected = _print_section(f"Quick wins — top {top_n} (0 pending deps, highest easiness)", ranked, "easiness", top_n)
    _paste_block("quick-wins", [it.id for it in selected[:20]])

    # Also show the top 5 with deps for awareness
    has_dep = sorted([it for it in items if any(d in pending_ids for d in it.deps)],
                     key=lambda x: x.easiness, reverse=True)[:5]
    if has_dep:
        print(f"\n  Blocked (has pending deps) — resolve first:")
        for it in has_dep:
            still_blocked = [d for d in it.deps if d in pending_ids]
            print(f"    {it.id:<18} waiting on: {', '.join(still_blocked[:3])}")


def mode_training_data(items: list[Item], top_n: int) -> None:
    # S-LOE items with file hints = most likely to generate clean training diffs
    ranked = sorted(items, key=lambda x: x.training_score, reverse=True)

    print(f"\n  Training data strategy: prefer LOE=S items that create new .py files")
    print(f"  (These produce 10-30 line diffs — clean SFT examples)")

    loe_s = [it for it in ranked if it.loe == "S"]
    loe_m = [it for it in ranked if it.loe == "M"]

    print(f"\n  LOE=S (10pt base, ~70s each, best training signal): {len(loe_s)} items")
    for it in loe_s[:10]:
        hint = it.file_hints[0] if it.file_hints else "no file hint"
        print(f"    {it.id:<18} [{it.training_score:2d}pt]  {hint[:40]}")

    print(f"\n  LOE=M (7pt base, acceptable signal): {len(loe_m)} items")
    for it in loe_m[:5]:
        print(f"    {it.id:<18} [{it.training_score:2d}pt]  {it.title[:45]}")

    selected = _print_section(f"Top {top_n} for training data ROI", ranked, "training_score", top_n)
    _paste_block("training-data", [it.id for it in selected[:20]])

    s_count = sum(1 for it in selected if it.loe == "S")
    eta_min = s_count * 80 / 60 + (top_n - s_count) * 120 / 60
    print(f"\n  Estimated runtime: ~{eta_min:.0f} min  |  Expected new quality examples: ~{s_count}")


def mode_dependencies(items: list[Item], top_n: int) -> None:
    ranked = sorted(items, key=lambda x: (x.unlocks_count, x.easiness), reverse=True)

    selected = _print_section(
        f"Top {top_n} by unlock count (completing these unblocks the most other items)",
        ranked, "easiness", top_n,
    )
    # Show detailed unlock map for top 5
    print(f"\n  Detailed unlock map (top 5):")
    pending_ids = _pending_ids(items)
    by_id = {it.id: it for it in items}
    for it in selected[:5]:
        unlocked = [oid for oid, o in by_id.items() if it.id in o.deps]
        print(f"    {it.id}: unlocks {it.unlocks_count} items")
        for uid in unlocked[:4]:
            print(f"      → {uid}: {by_id[uid].title[:50]}")

    _paste_block("dependencies", [it.id for it in selected[:20]])


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Roadmap analyzer — find optimal execution order")
    parser.add_argument("--mode", choices=["quick-wins", "training-data", "dependencies"],
                        default="quick-wins", help="Analysis mode")
    parser.add_argument("--top", type=int, default=20, help="Number of items to recommend")
    args = parser.parse_args()

    items = load_items()
    annotate_unlocks(items)

    loe_dist = {}
    for it in items:
        loe_dist[it.loe] = loe_dist.get(it.loe, 0) + 1

    print(f"Roadmap Analyzer — mode: {args.mode}")
    print(f"Pending/in-progress: {len(items)} items  |  LOE: {loe_dist}")

    if args.mode == "quick-wins":
        mode_quick_wins(items, args.top)
    elif args.mode == "training-data":
        mode_training_data(items, args.top)
    elif args.mode == "dependencies":
        mode_dependencies(items, args.top)


if __name__ == "__main__":
    main()
