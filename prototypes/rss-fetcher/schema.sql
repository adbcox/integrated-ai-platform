-- RSS Fetcher Prototype Schema
-- D-17-136 / D-17-137 minimal smoke-test schema
-- Authored: 2026-05-09 (feat/rss-prototype-fetcher)
--
-- Scope: smoke-test the design docs against real code.
-- This is a minimal subset of the full design — feeds, articles,
-- article_scores. Output routing, pipeline_runs, embeddings, RAG
-- index added in subsequent iterations.
--
-- Apply: sqlite3 prototype.db < schema.sql

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ----------------------------------------------------------------
-- feeds: registry of feed sources (initial seed from
-- docs/architecture-facts/rss-feed-list-curated.md)
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feeds (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL UNIQUE,
    url             TEXT NOT NULL UNIQUE,
    category        TEXT NOT NULL,
    assigned_to     TEXT NOT NULL CHECK (assigned_to IN ('D-17-136', 'D-17-137', 'both')),
    polling_interval TEXT NOT NULL,                  -- '4h' | 'daily' | 'hourly' | 'weekly'
    feed_unavailable INTEGER NOT NULL DEFAULT 0,    -- 0 = active, 1 = marked unavailable
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_polled_at  TEXT
);

-- ----------------------------------------------------------------
-- articles: fetched items from feeds. content_hash enables dedupe
-- across runs without trusting URL alone (some feeds rewrite URLs).
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS articles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    feed_id         INTEGER NOT NULL REFERENCES feeds(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    url             TEXT NOT NULL,
    summary         TEXT,                            -- description / summary from feed XML
    published_at    TEXT,                            -- pubDate from feed (ISO 8601, may be null)
    content_hash    TEXT NOT NULL,                   -- sha256(title + url + summary)
    fetched_at      TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (feed_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_articles_feed_id      ON articles(feed_id);
CREATE INDEX IF NOT EXISTS idx_articles_content_hash ON articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_articles_published_at ON articles(published_at);

-- ----------------------------------------------------------------
-- article_scores: scoring results from the relevance ranker(s).
-- One article can have BOTH a technical score (D-17-136) and a
-- personal score (D-17-137) since some feeds are assigned to both.
-- ----------------------------------------------------------------
CREATE TABLE IF NOT EXISTS article_scores (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    article_id      INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    scorer          TEXT NOT NULL CHECK (scorer IN ('technical', 'personal')),
    model           TEXT NOT NULL,                   -- e.g., 'qwen2.5-coder:7b' or 'gemma2:27b'

    -- Per-dimension scores (NULL when not applicable to this scorer).
    -- Technical scorer uses 7 dimensions per rss-technical-relevance-rubric.md.
    -- Personal scorer uses 6 dimensions per rss-personal-relevance-rubric.md.
    dim_source_quality      INTEGER,                 -- both: 0-3
    dim_domain_fit          INTEGER,                 -- both: 0-3 (technical-domain or personal-interest)
    dim_actionability       INTEGER,                 -- both: 0-3
    dim_novelty             INTEGER,                 -- both: 0-3
    dim_depth               INTEGER,                 -- both: 0-3
    dim_operational_impact  INTEGER,                 -- technical only: 0-3
    dim_time_sensitivity    INTEGER,                 -- both: 0-2

    final_score     INTEGER NOT NULL,                -- sum of applicable dimensions + boost
    threshold       INTEGER NOT NULL,                -- 11 for technical, 10 for personal
    threshold_pass  INTEGER NOT NULL CHECK (threshold_pass IN (0, 1)),
    boost_applied   TEXT,                            -- 'multi_domain', 'locked_source', NULL

    raw_response    TEXT,                            -- full Ollama response for audit
    reasoning       TEXT,                            -- model's reasoning text (extracted)
    scored_at       TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE (article_id, scorer, model)
);

CREATE INDEX IF NOT EXISTS idx_article_scores_article_id ON article_scores(article_id);
CREATE INDEX IF NOT EXISTS idx_article_scores_threshold_pass ON article_scores(threshold_pass);

-- ----------------------------------------------------------------
-- Sanity views for quick inspection during development
-- ----------------------------------------------------------------
CREATE VIEW IF NOT EXISTS v_recent_articles AS
SELECT
    f.name      AS feed_name,
    a.title,
    a.url,
    a.published_at,
    a.fetched_at,
    a.id        AS article_id
FROM articles a
JOIN feeds f ON f.id = a.feed_id
ORDER BY a.fetched_at DESC;

CREATE VIEW IF NOT EXISTS v_scored_articles AS
SELECT
    f.name              AS feed_name,
    a.title,
    s.scorer,
    s.model,
    s.final_score,
    s.threshold,
    s.threshold_pass,
    s.scored_at
FROM article_scores s
JOIN articles a ON a.id = s.article_id
JOIN feeds f    ON f.id = a.feed_id
ORDER BY s.scored_at DESC;
