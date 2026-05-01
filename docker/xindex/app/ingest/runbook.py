"""Runbook ingester — `docs/runbooks/*.md`.

Each runbook is a single markdown file. We store filename (without .md)
as the primary key, the H1 as the title, and the full body as the
searchable content.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import frontmatter


_H1_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$", re.MULTILINE)


def _title_from_body(body: str, fallback: str) -> str:
    m = _H1_RE.search(body)
    return m.group("title").strip() if m else fallback


def ingest(conn: sqlite3.Connection, runbook_dir: str) -> int:
    count = 0
    root = Path(runbook_dir)
    if not root.is_dir():
        return 0

    for path in sorted(root.glob("*.md")):
        name = path.stem
        post = frontmatter.load(path)
        body = post.content
        title = _title_from_body(body, fallback=name)

        rel_path = str(path.relative_to(root.parent.parent)) \
            if root.parent.parent in path.parents \
            else str(path)

        conn.execute(
            """
            INSERT INTO runbooks(name, title, path, body)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
                title=excluded.title,
                path=excluded.path,
                body=excluded.body
            """,
            (name, title, rel_path, body),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('runbook', ?, ?, ?)",
            (name, title, body),
        )
        count += 1
    return count
