# RSS Fetcher Prototype — Findings

**Date:** 2026-05-09 (Tokyo, MacBook Pro qwen2.5-coder:7b)
**Branch:** `feat/rss-prototype-fetcher`
**Status:** Smoke-test complete; design validated end-to-end with real findings

## What this prototype actually does

End-to-end runnable pipeline:

1. `schema.sql` — SQLite DDL (3 tables, 2 views, foreign keys, WAL mode)
2. `fetch_feed.py` — fetches one RSS feed by ID, parses RSS 2.0/RSS 1.0/Atom, dedupes via content_hash, writes articles
3. `ollama_score.py` — calls local Ollama `/api/generate` with `format=json`, scores against the 7-dimension technical-relevance rubric, validates ranges, upserts into `article_scores`
4. `smoke_test.py` — orchestrates fetch → score-N → summary; the plain-Python equivalent of the Goose `master-orchestrator` recipe in `rss-orchestrator-doctrine.md`

Stdlib-only Python (no feedparser, no requests, no ollama-python). Runs on MacBook with `qwen2.5-coder:7b` against any of the verified feeds from `rss-feed-list-curated.md`.

## What the design validated correctly

- **SQLite schema is sufficient for the smoke-test scope.** 3 tables (feeds, articles, article_scores) + 2 views handle the canonical pipeline up through scoring. Idempotent upsert via `ON CONFLICT(article_id, scorer, model)` works as designed.
- **Content-hash dedupe works.** `sha256(title + url + summary)`. Re-running fetch on the same feed produces 0 new inserts; 20 duplicates correctly identified.
- **Ollama `format=json` is reliable for structured output on 7B.** All scoring calls returned valid JSON; no parser fallback needed across 6 articles.
- **Range validation catches malformed scores.** Code hardened against the model returning out-of-scale values (didn't happen in this run, but the guardrail is in place).
- **Performance is workable on MacBook 7B.** ~6.8s per article on average (40.6s for 6 articles). Production scoring on Mac Studio with `qwen3-coder:30b-coding` should be slower per article but with parallelism via Goose recipe orchestration, not a bottleneck.

## What the design got WRONG (calibration issues only visible in real execution)

These are real defects in the technical-relevance rubric prompt that were invisible in the design docs and surfaced only after running against actual articles:

### Issue 1 — Locked-stack tool name recognition fails

The prompt lists "Claude Code" explicitly under the operator's locked agent stack. An article titled **"Using Claude Code: The unreasonable effectiveness of HTML"** scored:
- `domain_fit`: **0** (should be 3 — direct hit on locked agent stack)
- `operational_impact`: **0** (should be 2-3 — Claude Code is the operator's locked default for high-judgment coding)
- Final: **4 / threshold 11** → fail

The 7B model isn't connecting "article title contains 'Claude Code'" with "Claude Code is in the locked stack." It's reading the rubric description but not pattern-matching tool names.

**Fix candidates:**
- Add a pre-pass that detects locked-stack tool names in title/summary before scoring (programmatic, not LLM)
- Add explicit examples in the rubric prompt: "Article titled 'Using Claude Code: ...' → domain_fit=3, operational_impact=2-3"
- Use a larger model for production scoring (qwen3-coder:30b-coding or gemma2:27b should be more reliable)

### Issue 2 — Anti-pattern labels are nearest-match, not accurate-match

An article about **"EU calls VPNs a loophole that needs closing"** correctly triggered the anti-pattern (article isn't technically substantive for the operator's pipeline) but was labeled **"off-stack frontend framework news"** — the closest anti-pattern in the list, not an accurate description.

The model is forced to pick from the 7 anti-patterns enumerated. When none fit, it picks the closest. Not catastrophic (the article was correctly excluded) but the label is misleading for audit.

**Fix candidates:**
- Add an "off-topic / not technically substantive" catch-all anti-pattern
- Make `anti_pattern_name` free-text instead of constrained to the 7-item list
- Accept this as cosmetic (the routing decision was correct)

### Issue 3 — Threshold of 11 may be too high for 7B baseline

Of 6 HN frontpage articles scored:
- 3 triggered anti-patterns (final 0)
- 3 scored 4-5 / 18 (failed threshold)
- **0 passed threshold of 11**

This is consistent with HN frontpage being mostly low-signal-for-this-operator; the rubric is correctly suppressing noise. But it makes it impossible to validate the "high-score path" without curated test articles.

**Fix candidates:**
- Test against a feed with known-relevant content (e.g., GitHub release atoms for Goose, OpenCode, Aider — these are direct stack hits)
- Author a tiny corpus of "ground-truth" articles with expected scores; validate model output against them
- Lower threshold to 8-9 with better calibration if Issue 1 is fixed

## Lessons for the orchestrator doctrine

The orchestrator doctrine assumed scoring would be a single-stage operation. The smoke test shows it should be:

1. **Pre-pass:** programmatic detection of locked-stack tool names in title/summary → boost domain_fit and operational_impact floors
2. **Score:** LLM scores remaining dimensions using rubric prompt
3. **Validate:** range check + ground-truth-corpus regression test (when corpus exists)
4. **Audit log:** raw response + reasoning preserved (already done — `raw_response` column)

This is a real architectural addition that was not in the orchestrator doctrine and would have been invented post-deploy under pressure. Surfacing it in prototype phase is the win.

## Open questions for next session

1. **Ground-truth corpus:** should we hand-score 20-30 articles to use as a regression suite when refining prompts and swapping models?
2. **Tool-name pre-pass:** add as a separate Python module, or fold into `ollama_score.py`?
3. **Model swap test:** how does `gemma2:27b` (Mac Studio) score the same articles? Worth running once home-network is available to validate the production-path model assumption.
4. **Personal-relevance scorer:** parallel implementation needed for D-17-137; mostly the same code with the personal rubric prompt + 6 dimensions.
5. **Embeddings stage:** not yet built; `nomic-embed-text:latest` is available locally. Article embedding for RAG is a next prototype.
6. **OpenProject sink:** mock or real? Real requires home-network access; mock can validate the routing logic.

## What this means for the design phase

The design docs are NOT wrong — they describe a valid system. But:

- They were too high-level to surface calibration issues
- Continuing to add design WPs (story clustering, briefing card, etc.) without prototyping the scoring stage first would have built more layers on a flawed scoring foundation
- The operator's instinct to pivot to building was correct: 30 minutes of real code surfaced 3 real defects that would have wasted hours of design iteration

**Recommendation for the operator:** before authoring more D-17-137 design WPs, decide if calibration fix (Issue 1) is a prompt-tweak or a pre-pass module. That decision shapes story clustering and source/perspective scoring designs.
