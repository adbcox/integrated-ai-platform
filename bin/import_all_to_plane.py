#!/usr/bin/env python3
"""Cross-reference ITEMS/ against Plane and import any missing issues.

Strategy:
  1. Fetch all existing Plane issues (paginated)
  2. Extract the RM-xxx ID from each issue name (prefix pattern [RM-xxx])
  3. Compare against 601 ITEMS/ files
  4. Import only items whose ID is not already in Plane
  5. Rate-limit: 1 req/s, backoff on 429
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

_REPO = Path(__file__).parent.parent

# ── Plane config ─────────────────────────────────────────────────────────────

def _load_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_file = _REPO / "docker" / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k.startswith("PLANE")})
    return env

_ENV            = _load_env()
PLANE_BASE      = _ENV.get("PLANE_URL", "http://localhost:8000")
PLANE_TOKEN     = _ENV.get("PLANE_API_TOKEN", "")
PLANE_SLUG      = _ENV.get("PLANE_WORKSPACE", "iap")
PLANE_PROJ_ID   = _ENV.get("PLANE_PROJECT_ID", "dbcd4476-1e37-4812-a443-0914ec8380fc")

# State name → ID mapping (populated at runtime)
_STATE_IDS: dict[str, str] = {}

_STATUS_TO_STATE = {
    "Backlog":     "Backlog",
    "Todo":        "Todo",
    "Accepted":    "Backlog",       # map Accepted → Backlog
    "In Progress": "In Progress",
    "Done":        "Done",
    "Deferred":    "Deferred",
    "Cancelled":   "Cancelled",
    "Ready":       "Ready",
}

_PRIORITY_MAP = {
    "urgent": "urgent", "high": "high", "medium": "medium",
    "low": "low", "none": "none",
}


# ── Plane API helpers ─────────────────────────────────────────────────────────

def _api(method: str, path: str, data: dict | None = None, retries: int = 5) -> dict:
    url = f"{PLANE_BASE}/api/v1/{path}"
    body = json.dumps(data).encode() if data else None
    headers = {"X-Api-Key": PLANE_TOKEN, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 65 * (attempt + 1)
                print(f"    429 — waiting {wait}s…", flush=True)
                time.sleep(wait)
                continue
            body_text = e.read().decode(errors="replace")[:200]
            raise RuntimeError(f"HTTP {e.code} on {method} {path}: {body_text}") from e
    raise RuntimeError(f"Exceeded retries on {method} {path}")


def fetch_all_issues() -> list[dict]:
    """Paginate through all Plane issues. Returns flat list."""
    issues: list[dict] = []
    cursor = None
    page = 1
    while True:
        params = "per_page=100"
        if cursor:
            params += f"&cursor={cursor}"
        data = _api("GET", f"workspaces/{PLANE_SLUG}/projects/{PLANE_PROJ_ID}/issues/?{params}")
        batch = data.get("results", [])
        issues.extend(batch)
        print(f"  Fetched page {page}: {len(batch)} issues (total so far: {len(issues)})")
        if not data.get("next_page_results"):
            break
        cursor = data.get("next_cursor")
        page += 1
        time.sleep(1)
    return issues


def load_states() -> None:
    data = _api("GET", f"workspaces/{PLANE_SLUG}/projects/{PLANE_PROJ_ID}/states/")
    for st in data.get("results", []):
        _STATE_IDS[st["name"]] = st["id"]
    print(f"  States loaded: {list(_STATE_IDS.keys())}")


def _state_id(status: str) -> str:
    target = _STATUS_TO_STATE.get(status, "Backlog")
    sid = _STATE_IDS.get(target) or _STATE_IDS.get("Backlog", "")
    return sid


# ── Item parsing ──────────────────────────────────────────────────────────────

_STATUS_MAP = {
    "accepted": "Accepted", "backlog": "Backlog", "todo": "Todo",
    "in progress": "In Progress", "in-progress": "In Progress",
    "done": "Done", "complete": "Done", "completed": "Done",
    "deferred": "Deferred", "cancelled": "Cancelled", "canceled": "Cancelled",
    "pending": "Backlog", "ready": "Ready",
}
_PRI_MAP = {
    "p0": "urgent", "p1": "high", "p2": "medium", "p3": "low", "p4": "none",
    "critical": "urgent", "high": "high", "medium": "medium", "low": "low",
}


def _find(pattern: str, text: str, flags: int = re.IGNORECASE) -> str:
    m = re.search(pattern, text, flags)
    return m.group(1).strip() if m else ""


def parse_item_file(fp: Path) -> dict:
    text = fp.read_text(encoding="utf-8", errors="replace")

    item_id = fp.stem  # e.g. RM-A11Y-001
    title = (_find(r'\*\*Title:\*\*\s*(.+)', text)
             or _find(r'^#\s+(.+)$', text, re.MULTILINE)
             or item_id)
    title = re.sub(r'^#+\s*', '', title).strip()

    raw_status = (_find(r'\*\*Status:\*\*\s*`?([^`\n]+)`?', text)
                  or _find(r'^[-*]\s+\*\*Status:\*\*\s*(.+)$', text, re.MULTILINE))
    status = _STATUS_MAP.get(raw_status.lower().strip(), "Backlog")

    raw_pri = (_find(r'\*\*Priority:\*\*\s*`?([^`\n]+)`?', text)
               or _find(r'\*\*Priority class:\*\*\s*`?([^`\n]+)`?', text))
    priority = _PRI_MAP.get(raw_pri.lower().strip(), "medium")

    # Description: content after first heading before first ##
    desc_m = re.search(r'^#{1,2}[^#].+?\n\n(.*?)(?=\n##|\Z)', text,
                       re.MULTILINE | re.DOTALL)
    description = desc_m.group(1).strip()[:1000] if desc_m else text[:500]

    plane_name = f"[{item_id}] {title}"

    return {
        "id": item_id,
        "name": plane_name,
        "title": title,
        "status": status,
        "priority": priority,
        "description": description,
    }


# ── ID extraction from Plane issue names ──────────────────────────────────────

_ID_RE = re.compile(r'\[(RM-[A-Z0-9]+-\d+)\]')

def extract_id_from_name(name: str) -> str | None:
    m = _ID_RE.search(name)
    return m.group(1) if m else None


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    if not PLANE_TOKEN:
        print("ERROR: PLANE_API_TOKEN not set in docker/.env")
        return 1

    print("Phase 1 — Loading Plane states…")
    load_states()
    time.sleep(1)

    print("\nPhase 2 — Fetching all existing Plane issues…")
    existing_issues = fetch_all_issues()
    print(f"  Total in Plane: {len(existing_issues)}")

    # Build set of IDs already in Plane
    plane_ids: set[str] = set()
    for issue in existing_issues:
        rid = extract_id_from_name(issue.get("name", "") or issue.get("sequence_id", ""))
        if rid:
            plane_ids.add(rid)
    print(f"  Issues with RM-xxx ID prefix: {len(plane_ids)}")
    time.sleep(1)

    print("\nPhase 3 — Scanning ITEMS/ directory…")
    items_dir = _REPO / "docs" / "roadmap" / "ITEMS"
    item_files = sorted(items_dir.glob("RM-*.md"))
    print(f"  Found {len(item_files)} ITEM files")

    # Find missing IDs
    missing_files = [f for f in item_files if f.stem not in plane_ids]
    already_have = len(item_files) - len(missing_files)
    print(f"  Already in Plane: {already_have}")
    print(f"  Missing from Plane: {len(missing_files)}")

    if not missing_files:
        print("\n✓ All ITEMS already exist in Plane — nothing to import")
        _print_final_count(existing_issues)
        return 0

    print(f"\nPhase 4 — Importing {len(missing_files)} missing items…")
    imported = 0
    errors: list[dict] = []

    for i, fp in enumerate(missing_files, 1):
        try:
            item = parse_item_file(fp)
        except Exception as e:
            print(f"  [{i}/{len(missing_files)}] PARSE ERROR {fp.stem}: {e}")
            errors.append({"id": fp.stem, "error": f"parse: {e}"})
            continue

        payload = {
            "name": item["name"],
            "description_html": f"<p>{item['description']}</p>",
            "state": _state_id(item["status"]),
            "priority": _PRIORITY_MAP.get(item["priority"], "medium"),
        }

        try:
            result = _api(
                "POST",
                f"workspaces/{PLANE_SLUG}/projects/{PLANE_PROJ_ID}/issues/",
                data=payload,
            )
            print(f"  [{i}/{len(missing_files)}] ✓ {item['id']}: {item['title'][:60]}")
            imported += 1
        except Exception as e:
            print(f"  [{i}/{len(missing_files)}] ✗ {item['id']}: {e}")
            errors.append({"id": item["id"], "error": str(e)[:200]})

        time.sleep(1.1)  # stay well under 60 req/min

    print(f"\n{'='*60}")
    print(f"IMPORT COMPLETE")
    print(f"{'='*60}")
    print(f"  Imported: {imported}")
    print(f"  Skipped (already existed): {already_have}")
    print(f"  Errors:   {len(errors)}")

    if errors:
        err_file = _REPO / "import_errors.json"
        err_file.write_text(json.dumps(errors, indent=2))
        print(f"\n  Error details → import_errors.json")

    # Final count
    time.sleep(2)
    _print_final_count()
    return 0 if not errors else 1


def _print_final_count(cached: list | None = None) -> None:
    try:
        if cached is not None:
            total = len(cached)
        else:
            data = _api("GET",
                        f"workspaces/{PLANE_SLUG}/projects/{PLANE_PROJ_ID}/issues/?per_page=1")
            total = data.get("total_count", "?")
        print(f"\nFINAL PLANE COUNT: {total} issues")
    except Exception as e:
        print(f"\nCould not fetch final count: {e}")


if __name__ == "__main__":
    sys.exit(main())
