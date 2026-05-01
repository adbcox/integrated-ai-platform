"""Decision Register ingester — `docs/DECISION_REGISTER.md`.

The register is a single markdown file with H2 sections (categories) each
containing a markdown table. Row format:

    | [A-NNN](adr/ADR-A-NNN[-slug].md) | Title | Summary |

We capture every row; the H2 immediately above is the row's category.
The short_id (A-NNN) is the primary key; adr_id is the resolved
`ADR-A-NNN` form for joining against the `adrs` table.
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path


_H2_RE = re.compile(r"^##\s+(?P<name>[^\n]+?)\s*$")
_ROW_RE = re.compile(
    r"^\|\s*\[(?P<short>A-\d+)\]\((?P<link>adr/ADR-A-\d+[^)]*\.md)\)\s*"
    r"\|\s*(?P<title>.+?)\s*"
    r"\|\s*(?P<summary>.+?)\s*"
    r"\|\s*$"
)


def ingest(conn: sqlite3.Connection, register_path: str) -> int:
    p = Path(register_path)
    if not p.is_file():
        return 0

    count = 0
    category = "Uncategorised"
    for line in p.read_text(encoding="utf-8").splitlines():
        m_h2 = _H2_RE.match(line)
        if m_h2:
            category = m_h2.group("name").strip()
            continue

        m_row = _ROW_RE.match(line)
        if not m_row:
            continue

        short = m_row.group("short").upper()
        parts = short.split("-")
        adr_id = f"ADR-{parts[0]}-{parts[1].zfill(3)}" if len(parts) == 2 else f"ADR-{short}"

        title = m_row.group("title").strip()
        summary = m_row.group("summary").strip()
        link_path = f"docs/{m_row.group('link')}"

        conn.execute(
            """
            INSERT INTO decision_register_entries(short_id, adr_id, category,
                                                  title, summary, link_path)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(short_id) DO UPDATE SET
                adr_id=excluded.adr_id,
                category=excluded.category,
                title=excluded.title,
                summary=excluded.summary,
                link_path=excluded.link_path
            """,
            (short, adr_id, category, title, summary, link_path),
        )
        conn.execute(
            "INSERT INTO xindex_fts(kind, ref, title, body) VALUES('register', ?, ?, ?)",
            (short, title, summary),
        )
        count += 1
    return count
