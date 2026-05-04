#!/usr/bin/env python3
"""D-17-55 WP-04 — OpenProject metadata enrichment from framework/doctrine sources.

Read model:
- docs/PROJECT_FRAMEWORK.md deliverable rows are canonical.
- Optional closeout/results docs augment description.

Write model:
- Enriches existing D-* work packages only (matched by External ID custom field).
- Idempotent delta patching.
- Preserves manual edits by default: non-empty conflicting target fields are skipped.
- --force overrides manual-edit protection for managed fields.

Managed fields:
- description
- percentageDone
- customField<phase>
- customField<deliverable_class>
- customField<finding_refs>
- customField<dependencies>

Never managed:
- dueDate
- customField1 (Plane RM ID)
- customField2 (External ID)
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK_MD = REPO_ROOT / "docs" / "PROJECT_FRAMEWORK.md"
CLASS_TAXONOMY_MD = REPO_ROOT / "docs" / "architecture-facts" / "class-taxonomy.md"

OPENPROJECT_URL = "http://192.168.10.145:8086"
PROJECT_IDENTIFIER = "roadmap"

PHASE_HEADING_RE = re.compile(r"^##\s+\d+\.\s+Phase\s+(?P<n>\d+)\b")
ROW_RE = re.compile(
    r"^\|\s*(?P<extid>D-(?P<phase>\d+)-[\w.\-]+)(?:\s+\(historical:[^)]+\))?\s*:\s*(?P<title>.+?)\s*\|\s*(?P<status>[^|]+?)\s*\|\s*(?P<reference>[^|]+?)\s*\|\s*$"
)
STATUS_RE = re.compile(r"^(DONE|IN PROGRESS|NOT STARTED|DEFERRED)\b", re.I)
WP_ID_RE = re.compile(r"\bWP-[0-9A-Za-z.\-]+\b")
WP_DONE_NEAR_RE = re.compile(r"\b(WP-[0-9A-Za-z.\-]+)\b(?=[^|\n]{0,60}\bDONE\b)", re.I)
FINDING_RE = re.compile(r"\bF\d+\b|\bFinding\s+\d+\b", re.I)
DEP_RE = re.compile(r"\bD-\d+-[\w.\-]+\b")


@dataclass
class DeliverableRow:
    external_id: str
    phase: int
    title: str
    status_word: str
    reference: str


def _status_word(raw: str) -> str | None:
    m = STATUS_RE.match(raw.strip())
    return m.group(1).upper() if m else None


def parse_framework_rows(path: Path) -> list[DeliverableRow]:
    rows: list[DeliverableRow] = []
    current_phase: int | None = None
    for line in path.read_text().splitlines():
        hm = PHASE_HEADING_RE.match(line)
        if hm:
            current_phase = int(hm.group("n"))
            continue
        m = ROW_RE.match(line)
        if not m:
            continue
        sw = _status_word(m.group("status"))
        if not sw:
            continue
        phase = int(m.group("phase"))
        if current_phase is not None and current_phase != phase:
            continue
        rows.append(
            DeliverableRow(
                external_id=m.group("extid"),
                phase=phase,
                title=m.group("title").strip(),
                status_word=sw,
                reference=m.group("reference").strip(),
            )
        )
    return rows


def fetch_op_token() -> str:
    candidates: list[str] = []
    vt = Path.home() / ".vault-token"
    if vt.is_file() and vt.read_text().strip():
        candidates.append(vt.read_text().strip())
    fallback = Path.home() / "vault-init-keys-NEW-20260430.txt"
    if fallback.is_file():
        for ln in fallback.read_text().splitlines():
            if ln.startswith("Initial Root Token:"):
                candidates.append(ln.split(":", 1)[1].strip())
                break
    last_err = ""
    for tok in candidates:
        try:
            out = subprocess.check_output(
                [
                    "/opt/homebrew/bin/docker", "exec",
                    "-e", f"VAULT_TOKEN={tok}",
                    "-e", "VAULT_ADDR=http://127.0.0.1:8200",
                    "vault-server",
                    "vault", "kv", "get", "-field=token", "secret/openproject/api",
                ],
                text=True,
                stderr=subprocess.PIPE,
            ).strip()
            if out:
                return out
        except subprocess.CalledProcessError as exc:
            last_err = (exc.stderr or "").strip()
    raise RuntimeError(f"could not read OpenProject token from Vault: {last_err or '(none)'}")


def op_request(method: str, path: str, token: str, *, params: dict[str, Any] | None = None, payload: dict[str, Any] | None = None) -> Any:
    url = f"{OPENPROJECT_URL}/api/v3{path}"
    if params:
        url += "?" + urlencode(params)
    req = Request(url, method=method)
    basic = base64.b64encode(f"apikey:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {basic}")
    req.add_header("Content-Type", "application/json")
    data = None
    if payload is not None:
        data = json.dumps(payload).encode()
    with urlopen(req, data=data, timeout=30) as resp:
        raw = resp.read()
    if not raw:
        return {}
    return json.loads(raw.decode())


def project_id(token: str) -> int:
    p = op_request("GET", f"/projects/{PROJECT_IDENTIFIER}", token)
    return int(p["id"])


def list_project_wps(token: str, pid: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    page = 200
    offset = 1
    while True:
        filters = json.dumps([{"project": {"operator": "=", "values": [str(pid)]}}])
        data = op_request("GET", "/work_packages", token, params={"filters": filters, "pageSize": page, "offset": offset})
        elems = data.get("_embedded", {}).get("elements", [])
        out.extend(elems)
        total = int(data.get("total", 0))
        if offset * page >= total:
            break
        offset += 1
    return out


def get_schema_custom_fields(token: str, pid: int) -> dict[str, int]:
    form = op_request("POST", f"/projects/{pid}/work_packages/form", token, payload={})
    schema = form.get("_embedded", {}).get("schema", {})
    mapping: dict[str, int] = {}
    for key, desc in schema.items():
        if not str(key).startswith("customField"):
            continue
        name = (desc.get("name") or "").strip()
        if not name:
            continue
        try:
            cfid = int(str(key).replace("customField", ""))
        except ValueError:
            continue
        mapping[name] = cfid
    return mapping


def closeout_excerpt(external_id: str) -> str:
    did = external_id.lower()
    candidates = list((REPO_ROOT / "docs").glob(f"phase-*/{did}/CLOSEOUT*.md"))
    candidates += list((REPO_ROOT / "docs").glob(f"phase-*/{did}/RESULTS*.md"))
    if not candidates:
        return ""
    text = candidates[0].read_text(errors="ignore")
    # first non-heading paragraph line cluster
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]
    if not lines:
        return ""
    excerpt = " ".join(lines[:3])
    return excerpt[:500]


def description_for(row: DeliverableRow) -> str:
    excerpt = closeout_excerpt(row.external_id)
    parts = [
        f"Canonical source: PROJECT_FRAMEWORK.md §9 row {row.external_id}.",
        f"Reference: {row.reference}",
    ]
    if excerpt:
        parts.append(f"Closeout excerpt: {excerpt}")
    return "\n\n".join(parts)


def percentage_done_for(row: DeliverableRow) -> int | None:
    # Preferred: derive from WP-* DONE ratio in reference.
    all_ids = set(WP_ID_RE.findall(row.reference))
    done_ids = set(WP_DONE_NEAR_RE.findall(row.reference))
    if all_ids:
        done = len(done_ids & all_ids)
        total = len(all_ids)
        return int(round((done * 100.0) / total))

    # Fallback when no explicit WP markers in reference.
    if row.status_word == "DONE":
        return 100
    if row.status_word == "IN PROGRESS":
        return 50
    return 0


def load_class_rules(path: Path) -> list[tuple[str, re.Pattern[str]]]:
    names: list[str] = []
    for ln in path.read_text().splitlines():
        m = re.match(r"^###\s+(C\d+)\s+—", ln)
        if m:
            names.append(m.group(1))
    # heuristic keyword rules (ordered)
    rules: list[tuple[str, re.Pattern[str]]] = [
        ("C10", re.compile(r"\bscript|launchd|daemon|provision|sweep|sync\b", re.I)),
        ("C4", re.compile(r"\bdoctrine|ADR|chronicle\b", re.I)),
        ("C1", re.compile(r"\bdashboard|runbook|documentation|docs\b", re.I)),
        ("C3", re.compile(r"\bfix|patch|update\b", re.I)),
    ]
    existing = {c for c in names}
    return [(c, rx) for c, rx in rules if c in existing]


def class_for(row: DeliverableRow, rules: list[tuple[str, re.Pattern[str]]]) -> str:
    txt = f"{row.title} {row.reference}"
    for cname, rx in rules:
        if rx.search(txt):
            return cname
    return "C1"


def findings_for(row: DeliverableRow) -> str:
    tokens = sorted({m.group(0).replace("Finding ", "F") for m in FINDING_RE.finditer(row.reference)})
    return ",".join(tokens)


def dependencies_for(row: DeliverableRow) -> str:
    deps = sorted({d for d in DEP_RE.findall(row.reference) if d != row.external_id})
    return ",".join(deps)


def is_empty_value(v: Any) -> bool:
    if v is None:
        return True
    if v == "" or v == []:
        return True
    if isinstance(v, dict):
        # OpenProject sometimes returns empty text fields as {}.
        if not v:
            return True
        # Treat {"raw": ""} / {"html": ""} as empty too.
        if set(v.keys()).issubset({"raw", "html", "format"}):
            return not (v.get("raw") or v.get("html"))
    return False


def normalize_compare_value(v: Any) -> Any:
    """Normalize OpenProject values for stable idempotent comparison."""
    if isinstance(v, dict):
        # Rich-text custom fields and description may return as {raw, html, format}.
        if "raw" in v and isinstance(v.get("raw"), str):
            return v.get("raw")
        if "html" in v and isinstance(v.get("html"), str):
            return v.get("html")
        if not v:
            return ""
    return v


def status_name(wp: dict[str, Any]) -> str:
    return ((wp.get("_links", {}).get("status", {}) or {}).get("title") or "")


def main() -> int:
    ap = argparse.ArgumentParser(description="OpenProject enrichment from PROJECT_FRAMEWORK")
    ap.add_argument("--dry-run", action="store_true", help="print diffs only; no PATCH")
    ap.add_argument("--force", action="store_true", help="overwrite conflicting non-empty managed fields")
    ap.add_argument("--limit", type=int, default=0, help="limit number of candidate WPs")
    args = ap.parse_args()

    rows = {r.external_id: r for r in parse_framework_rows(FRAMEWORK_MD)}
    token = fetch_op_token()
    pid = project_id(token)
    wps = list_project_wps(token, pid)
    cf_map = get_schema_custom_fields(token, pid)

    needed = ["phase", "deliverable_class", "finding_refs", "dependencies", "External ID", "Plane RM ID"]
    missing = [n for n in ["phase", "deliverable_class", "finding_refs", "dependencies"] if n not in cf_map]
    if missing:
        print("ERROR: missing custom fields in OpenProject schema:", ", ".join(missing))
        print("Run scripts/openproject-bootstrap-enrichment-fields.sh first.")
        return 3

    ext_cf = cf_map["External ID"]
    c_phase = cf_map["phase"]
    c_class = cf_map["deliverable_class"]
    c_find = cf_map["finding_refs"]
    c_deps = cf_map["dependencies"]

    class_rules = load_class_rules(CLASS_TAXONOMY_MD)

    candidates: list[tuple[dict[str, Any], DeliverableRow]] = []
    for wp in wps:
        ext = wp.get(f"customField{ext_cf}") or ""
        if not ext or not str(ext).startswith("D-"):
            continue
        row = rows.get(str(ext))
        if not row:
            continue
        candidates.append((wp, row))

    if args.limit > 0:
        candidates = candidates[: args.limit]

    creates = 0
    skips = 0
    conflicts = 0
    patches = 0

    for wp, row in candidates:
        wp_id = int(wp["id"])
        cur_desc = (wp.get("description") or {}).get("raw") if isinstance(wp.get("description"), dict) else (wp.get("description") or "")
        cur_pct = wp.get("percentageDone")
        desired_desc = description_for(row)
        desired_pct = percentage_done_for(row)
        desired_phase = f"Phase {row.phase}"
        desired_class = class_for(row, class_rules)
        desired_find = findings_for(row)
        desired_deps = dependencies_for(row)

        desired_fields = {
            "description": desired_desc,
            "percentageDone": desired_pct,
            f"customField{c_phase}": desired_phase,
            f"customField{c_class}": desired_class,
            f"customField{c_find}": desired_find,
            f"customField{c_deps}": desired_deps,
        }
        current_fields = {
            "description": cur_desc,
            "percentageDone": cur_pct,
            f"customField{c_phase}": wp.get(f"customField{c_phase}"),
            f"customField{c_class}": wp.get(f"customField{c_class}"),
            f"customField{c_find}": wp.get(f"customField{c_find}"),
            f"customField{c_deps}": wp.get(f"customField{c_deps}"),
        }

        delta: dict[str, Any] = {}
        local_conflicts: list[str] = []
        for k, want in desired_fields.items():
            have = current_fields.get(k)
            if normalize_compare_value(have) == normalize_compare_value(want):
                continue
            # Preserve manual edits by default if field is non-empty and differs.
            if not args.force and not is_empty_value(have):
                local_conflicts.append(k)
                continue
            delta[k] = want

        if local_conflicts:
            conflicts += 1
            print(f"CONFLICT wp={wp_id} ext={row.external_id} fields={','.join(local_conflicts)}")

        if not delta:
            skips += 1
            continue

        # Need lockVersion for PATCH.
        full = op_request("GET", f"/work_packages/{wp_id}", token)
        payload = {"lockVersion": int(full.get("lockVersion", 0))}

        # description in OP expects object
        if "description" in delta:
            payload["description"] = {"format": "markdown", "raw": delta.pop("description")}
        # OpenProject text custom fields expect rich-text shape.
        for k, v in list(delta.items()):
            if k.startswith("customField") and isinstance(current_fields.get(k), dict) and isinstance(v, str):
                delta[k] = {"format": "markdown", "raw": v}
        payload.update(delta)

        patches += 1
        print(f"PATCH wp={wp_id} ext={row.external_id} keys={','.join(k for k in payload.keys() if k!='lockVersion')}")
        if not args.dry_run:
            op_request("PATCH", f"/work_packages/{wp_id}", token, payload=payload)

    print(f"SUMMARY candidates={len(candidates)} patches={patches} skips={skips} conflicts={conflicts} dry_run={args.dry_run} force={args.force}")
    return 2 if args.dry_run and patches > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
