"""ADR ingester.

ADRs in this repo use one of two header styles:

  Style 1 (most common — A-001/2/3/4/5/6/8/10/11/12/13/14/15/16):
      # ADR-A-NNN[-slug] — Title
      **Status:** Accepted
      **Date:** YYYY-MM-DD
      **Phase:** N        (or **Source:** ...)

  Style 2 (A-007, A-009 partially):
      # ADR-A-NNN[-slug]: Title
      ## Status
      Accepted (YYYY-MM-DD)

We parse both. After the header block we split on H2 to capture sections.
"""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path

import frontmatter


_ID_RE = re.compile(r"ADR-(A-\d+)", re.IGNORECASE)
# H1 forms:
#   "# ADR-A-014 — NetBox as Authoritative CMDB"
#   "# ADR-A-007: Syncthing replaces rclone SFTP ..."
_H1_RE = re.compile(
    r"^#\s+ADR-A-\d+(?:-[\w-]+)?\s*[—:\-–]\s*(?P<title>.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_BOLD_FIELD_RE = re.compile(
    # Matches both **Status:** Accepted (colon inside bold) and **Status**: Accepted
    # (colon outside). Key is captured without the trailing colon.
    r"^\*\*(?P<key>Status|Date|Phase|Source|Deciders):?\*\*\s*:?\s*(?P<val>.+?)\s*$",
    re.MULTILINE,
)
_SECTION_RE = re.compile(r"^##\s+(?P<name>[^\n]+?)\s*$", re.MULTILINE)
_STATUS_DATE_FALLBACK_RE = re.compile(
    r"^(?P<status>Accepted|Proposed|Superseded|Deprecated)\s*\((?P<date>\d{4}-\d{2}-\d{2})\)",
    re.IGNORECASE,
)


def _adr_id_from_filename(p: Path) -> str | None:
    m = _ID_RE.search(p.stem)
    if not m:
        return None
    short = m.group(1).upper()
    parts = short.split("-")
    if len(parts) == 2:
        return f"ADR-{parts[0]}-{parts[1].zfill(3)}"
    return f"ADR-{short}"


def _parse_sections(body: str) -> dict[str, str]:
    """Split markdown body into {section-name: content} keyed on H2 lines.

    Content is everything after the H2 up to the next H2 or end-of-file.
    """
    matches = list(_SECTION_RE.finditer(body))
    if not matches:
        return {}

    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = m.group("name").strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        chunk = body[start:end].strip()
        if name:
            sections[name] = chunk
    return sections


def _parse_meta(body: str, sections: dict[str, str]) -> dict[str, str]:
    """Extract Status / Date / Phase / Source from body or section content.

    Bolded field lines win when present. Otherwise we fall back to a
    parenthesized "Accepted (YYYY-MM-DD)" line in the Status section.
    """
    out: dict[str, str] = {}
    for m in _BOLD_FIELD_RE.finditer(body):
        out[m.group("key").lower()] = m.group("val").strip()

    if "status" not in out and "Status" in sections:
        m = _STATUS_DATE_FALLBACK_RE.match(sections["Status"].strip())
        if m:
            out["status"] = m.group("status").title()
            out.setdefault("date", m.group("date"))
        else:
            first_line = sections["Status"].strip().splitlines()[0].strip()
            if first_line:
                out["status"] = first_line
    return out


def _title_from_h1(body: str, fallback: str) -> str:
    m = _H1_RE.search(body)
    if m:
        return m.group("title").strip()
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def ingest(conn: sqlite3.Connection, adr_dir: str) -> int:
    """Walk an ADR directory and upsert each `ADR-A-*.md` file.

    Returns the number of ADRs ingested. Files that don't match the
    naming convention are skipped (e.g. README.md inside docs/adr/).
    """
    count = 0
    root = Path(adr_dir)
    if not root.is_dir():
        return 0

    for path in sorted(root.glob("ADR-A-*.md")):
        adr_id = _adr_id_from_filename(path)
        if not adr_id:
            continue

        post = frontmatter.load(path)
        body = post.content
        sections = _parse_sections(body)
        meta = _parse_meta(body, sections)
        title = _title_from_h1(body, fallback=adr_id)
        short_id = adr_id.replace("ADR-", "", 1)

        # python-frontmatter only finds YAML blocks; if the file has none,
        # post.metadata is empty. Bolded fields above carry the metadata.
        for k, v in (post.metadata or {}).items():
            if isinstance(v, (str, int)):
                meta.setdefault(k.lower(), str(v))

        sections_json_safe = {k: v for k, v in sections.items() if v}

        rel_path = str(path.relative_to(root.parent.parent.parent)) \
            if root.parent.parent.parent in path.parents \
            else str(path)

        conn.execute(
            """
            INSERT INTO adrs(id, short_id, title, status, date, phase, source,
                             path, body, sections_json)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, json(?))
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                status=excluded.status,
                date=excluded.date,
                phase=excluded.phase,
                source=excluded.source,
                path=excluded.path,
                body=excluded.body,
                sections_json=excluded.sections_json
            """,
            (
                adr_id,
                short_id,
                title,
                meta.get("status"),
                meta.get("date"),
                meta.get("phase"),
                meta.get("source") or meta.get("deciders"),
                rel_path,
                body,
                _json_dumps(sections_json_safe),
            ),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('adr', ?, ?, ?)",
            (adr_id, title, body),
        )
        count += 1
    return count


def _json_dumps(d: dict) -> str:
    import json

    return json.dumps(d, ensure_ascii=False)
