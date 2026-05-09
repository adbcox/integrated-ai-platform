#!/usr/bin/env python3
"""
fetch_feed.py — Fetch one RSS feed, parse, and insert articles into SQLite.

Prototype for D-17-136/D-17-137 design validation. Stdlib-only (no feedparser
dependency).  Uses content_hash dedupe (sha256 of title + url + summary), so
re-running the fetcher on the same feed is idempotent — only new items insert.

Usage:
    python3 fetch_feed.py <db_path> <feed_id>

Example:
    python3 fetch_feed.py prototype.db 1
"""

import hashlib
import sqlite3
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime


# RSS 2.0 / Atom namespaces — arXiv uses RSS 1.0 (RDF) which has its own ns
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "rdf":  "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "rss":  "http://purl.org/rss/1.0/",
    "dc":   "http://purl.org/dc/elements/1.1/",
}


def open_db(db_path: str) -> sqlite3.Connection:
    """Open SQLite connection with foreign keys enforced."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def fetch_url(url: str, timeout: int = 15) -> bytes:
    """HTTP GET the feed URL with a polite User-Agent."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "rss-fetcher-prototype/0.1 (D-17-136/D-17-137 smoke test)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def parse_feed(xml_bytes: bytes) -> list[dict]:
    """
    Parse RSS 1.0 (RDF) / RSS 2.0 / Atom feeds.  Returns list of items with
    keys: title, url, summary, published_at.

    arXiv specifically returns RSS 1.0 (RDF) format. Standard <channel><item>
    parsing in plain RSS 2.0 hits the channel as the root child but arXiv's
    RDF wraps differently.  We try a few common patterns.
    """
    root = ET.fromstring(xml_bytes)
    items = []

    # Strategy 1: RSS 2.0 — <rss><channel><item>...</item></channel></rss>
    for item in root.findall(".//item"):
        title  = (item.findtext("title") or "").strip()
        url    = (item.findtext("link")  or "").strip()
        # Description is the most common; some feeds use content:encoded
        summary = (item.findtext("description") or "").strip()
        if not summary:
            summary = (item.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "").strip()
        # Published — pubDate (RSS 2.0) or dc:date (RSS 1.0/RDF)
        pub = item.findtext("pubDate") or item.findtext("dc:date", namespaces=NS)
        if title and url:
            items.append({
                "title": title,
                "url":   url,
                "summary": summary,
                "published_at": pub.strip() if pub else None,
            })

    # Strategy 2: Atom — <feed><entry>...</entry></feed>
    if not items:
        for entry in root.findall(".//atom:entry", NS):
            title = (entry.findtext("atom:title", namespaces=NS) or "").strip()
            link_el = entry.find("atom:link", NS)
            url = link_el.get("href").strip() if link_el is not None and link_el.get("href") else ""
            summary = (entry.findtext("atom:summary", namespaces=NS) or "").strip()
            if not summary:
                summary = (entry.findtext("atom:content", namespaces=NS) or "").strip()
            pub = entry.findtext("atom:published", namespaces=NS) or entry.findtext("atom:updated", namespaces=NS)
            if title and url:
                items.append({
                    "title": title,
                    "url":   url,
                    "summary": summary,
                    "published_at": pub.strip() if pub else None,
                })

    return items


def content_hash(item: dict) -> str:
    """Stable hash for dedupe across runs."""
    h = hashlib.sha256()
    h.update(item["title"].encode("utf-8"))
    h.update(b"\x00")
    h.update(item["url"].encode("utf-8"))
    h.update(b"\x00")
    h.update((item["summary"] or "").encode("utf-8"))
    return h.hexdigest()


def insert_article(conn: sqlite3.Connection, feed_id: int, item: dict) -> bool:
    """Insert article; return True if inserted, False if duplicate."""
    h = content_hash(item)
    try:
        conn.execute(
            """
            INSERT INTO articles (feed_id, title, url, summary, published_at, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (feed_id, item["title"], item["url"], item["summary"], item["published_at"], h),
        )
        return True
    except sqlite3.IntegrityError:
        # UNIQUE(feed_id, content_hash) violation = already seen this article
        return False


def fetch_and_store(db_path: str, feed_id: int) -> dict:
    """Main entry: fetch one feed by ID, parse, insert new articles, update last_polled_at."""
    conn = open_db(db_path)
    try:
        feed = conn.execute("SELECT * FROM feeds WHERE id = ?", (feed_id,)).fetchone()
        if feed is None:
            raise ValueError(f"No feed with id={feed_id}")
        if feed["feed_unavailable"] == 1:
            return {"feed": feed["name"], "skipped": True, "reason": "feed_unavailable=1"}

        print(f"Fetching: {feed['name']} → {feed['url']}", file=sys.stderr)
        xml_bytes = fetch_url(feed["url"])
        print(f"  got {len(xml_bytes)} bytes", file=sys.stderr)

        items = parse_feed(xml_bytes)
        print(f"  parsed {len(items)} items", file=sys.stderr)

        inserted = 0
        duplicates = 0
        for item in items:
            if insert_article(conn, feed_id, item):
                inserted += 1
            else:
                duplicates += 1

        conn.execute("UPDATE feeds SET last_polled_at = datetime('now') WHERE id = ?", (feed_id,))
        conn.commit()

        return {
            "feed": feed["name"],
            "fetched": len(items),
            "inserted": inserted,
            "duplicates": duplicates,
            "polled_at": datetime.now().isoformat(timespec="seconds"),
        }
    finally:
        conn.close()


def main():
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    db_path = sys.argv[1]
    try:
        feed_id = int(sys.argv[2])
    except ValueError:
        print(f"feed_id must be integer; got {sys.argv[2]!r}", file=sys.stderr)
        sys.exit(2)

    result = fetch_and_store(db_path, feed_id)
    import json
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
