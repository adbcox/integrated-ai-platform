#!/usr/bin/env python3
"""
smoke_test.py — End-to-end pipeline test: fetch one feed, score all articles, report.

This is the orchestrator equivalent of the "master-orchestrator" Goose recipe
from rss-orchestrator-doctrine.md. Plain Python (no Goose) for prototype
purposes; once Goose recipes are written, this script becomes the reference
implementation they replace.

Usage:
    python3 smoke_test.py <db_path> <feed_id> [--model MODEL] [--limit N]
"""

import argparse
import json
import sys
import time

import fetch_feed
import ollama_score


def run(db_path: str, feed_id: int, model: str, limit: int) -> dict:
    print("═" * 60, file=sys.stderr)
    print(f"STAGE 1: Fetch feed {feed_id}", file=sys.stderr)
    print("═" * 60, file=sys.stderr)
    fetch_result = fetch_feed.fetch_and_store(db_path, feed_id)
    print(json.dumps(fetch_result, indent=2), file=sys.stderr)

    print("\n" + "═" * 60, file=sys.stderr)
    print(f"STAGE 2: Score up to {limit} unscored articles from feed {feed_id}", file=sys.stderr)
    print("═" * 60, file=sys.stderr)
    conn = fetch_feed.open_db(db_path)
    try:
        rows = conn.execute(
            """
            SELECT a.id
            FROM articles a
            LEFT JOIN article_scores s
              ON s.article_id = a.id AND s.scorer = 'technical' AND s.model = ?
            WHERE a.feed_id = ? AND s.id IS NULL
            ORDER BY a.id
            LIMIT ?
            """,
            (model, feed_id, limit),
        ).fetchall()
    finally:
        conn.close()

    article_ids = [r["id"] for r in rows]
    print(f"  {len(article_ids)} unscored articles to process", file=sys.stderr)

    scored = []
    t0 = time.time()
    for aid in article_ids:
        try:
            result = ollama_score.score_article(db_path, aid, model)
            scored.append(result)
            marker = "✓ PASS" if result["threshold_pass"] else ("⚠ ANTI" if result["anti_pattern_triggered"] else "  fail")
            print(f"  [{marker}] aid={aid} score={result['final_score']:>2}/threshold={result['threshold']} — {result['title'][:55]}", file=sys.stderr)
        except Exception as e:
            print(f"  [✗ ERR ] aid={aid}: {e}", file=sys.stderr)
    dt = time.time() - t0

    print("\n" + "═" * 60, file=sys.stderr)
    print("STAGE 3: Summary", file=sys.stderr)
    print("═" * 60, file=sys.stderr)
    pass_count = sum(1 for r in scored if r["threshold_pass"])
    anti_count = sum(1 for r in scored if r["anti_pattern_triggered"])
    avg_score = sum(r["final_score"] for r in scored) / len(scored) if scored else 0

    summary = {
        "fetch":             fetch_result,
        "scored":            len(scored),
        "passed_threshold":  pass_count,
        "anti_patterns":     anti_count,
        "avg_final_score":   round(avg_score, 2),
        "model":             model,
        "elapsed_seconds":   round(dt, 1),
        "avg_seconds_per_article": round(dt / len(scored), 1) if scored else None,
    }
    return summary


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("db_path")
    ap.add_argument("feed_id", type=int)
    ap.add_argument("--model", default=ollama_score.DEFAULT_MODEL)
    ap.add_argument("--limit", type=int, default=10)
    args = ap.parse_args()

    summary = run(args.db_path, args.feed_id, args.model, args.limit)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
