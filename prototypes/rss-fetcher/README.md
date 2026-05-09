# RSS Fetcher Prototype

First-iteration runnable code for D-17-136 / D-17-137 RSS pipeline.
Validates the design docs in `docs/architecture-facts/rss-*.md` against
real Ollama and real RSS feeds.

## Files

| File | Purpose |
|---|---|
| `schema.sql` | SQLite DDL: feeds, articles, article_scores + 2 views |
| `fetch_feed.py` | Fetch one RSS feed, parse, dedupe, insert articles |
| `ollama_score.py` | Score one article via Ollama `/api/generate` with `format=json` |
| `smoke_test.py` | End-to-end orchestrator: fetch + score + report |
| `FINDINGS.md` | What this prototype validated and what it surfaced as defects |

## Quickstart

```bash
# 1. Initialize DB
sqlite3 prototype.db < schema.sql

# 2. Seed a feed (e.g., HN frontpage — always has content)
sqlite3 prototype.db "INSERT INTO feeds (name, url, category, assigned_to, polling_interval) VALUES ('Hacker News', 'https://hnrss.org/frontpage', 'Industry/system design', 'both', 'hourly');"

# 3. Run smoke test (fetch + score 6 articles)
python3 smoke_test.py prototype.db 1 --limit 6

# 4. Inspect results
sqlite3 -header -column prototype.db "SELECT * FROM v_scored_articles;"
```

## Requirements

- Python 3.10+ (stdlib-only; no external deps)
- Local Ollama with `qwen2.5-coder:7b` model pulled
- Network access to chosen feeds

## Production gap

This prototype runs in plain Python on MacBook against MacBook's Ollama.
Production per `rss-orchestrator-doctrine.md`:

- Replace `smoke_test.py` orchestrator with Goose recipe set
- Route Ollama calls through `litellm-gateway` to Mac Studio (qwen3-coder:30b-coding for technical scoring, gemma2:27b for personal)
- Add embedding stage (nomic-embed-text → SQLite or chromadb)
- Add output classifier stage routing to OpenProject WP / benchmark prompt / Aider task brief
- Add personal-relevance scorer (D-17-137) parallel to technical
- Add story clustering, source/perspective scoring (D-17-137)
- Deploy on Mac Mini Pro (.145) with launchd timer for scheduling
- Wire to Zabbix for failure monitoring

See `FINDINGS.md` for what this prototype already exposed as missing or miscalibrated in the design.
