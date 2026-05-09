#!/usr/bin/env python3
"""
ollama_score.py — Score an article via local Ollama using the technical-relevance rubric.

Calls Ollama's /api/generate with format=json to force structured output,
then parses + validates dimension scores per rss-technical-relevance-rubric.md.

Dev/test on MacBook uses qwen2.5-coder:7b (per substrate doctrine + locked
model stack). Production will route to qwen3-coder:30b-coding on Mac Studio
via litellm-gateway per orchestrator doctrine; the prompt + parser are
identical, only the endpoint+model differ.

Usage:
    python3 ollama_score.py <db_path> <article_id> [--model MODEL]

Example:
    python3 ollama_score.py prototype.db 1
    python3 ollama_score.py prototype.db 1 --model qwen2.5-coder:7b
"""

import argparse
import json
import sqlite3
import sys
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b"
TECHNICAL_THRESHOLD = 11   # per rss-technical-relevance-rubric.md

# Rubric prompt — condensed inline. Source: docs/architecture-facts/rss-technical-relevance-rubric.md
# Keeps prompt under ~1000 tokens for 7B context efficiency.
RUBRIC_PROMPT_TEMPLATE = """You are a technical-relevance scoring system for an AI workstation operator who runs a self-hosted local AI stack (Ollama, Goose, Aider, OpenCode, Claude Code, Caddy, OPNsense, Vault, Headscale, Mac Studio M3 Ultra, Mac Mini Pro, RTX 4070, QNAP). You score incoming RSS articles by technical relevance to decide which articles enter the technical digest.

Score the article below on each of 7 dimensions. Each dimension is integer 0-3 (or 0-2 for time_sensitivity). Then provide reasoning.

DIMENSIONS:

1. source_quality (0-3): Is the source trusted/established for technical content?
   - 0=unknown publisher, no reputation
   - 1-2=mainstream tech outlet
   - 3=operator's locked sources (Hacker News, official project blogs, arXiv)

2. domain_fit (0-3): Does the article touch the operator's locked technical domains (AI/ML research, local agent stack, model layer, self-hosted infra, hardware platform)?
   - 0=unrelated
   - 1-2=adjacent
   - 3=direct hit on a locked domain

3. actionability (0-3): Can the operator do something concrete (code change, model swap, tool adoption, version pin, benchmark update)?
   - 0=pure background, no action path
   - 3=concrete actionable upgrade/migration/decision

4. novelty (0-3): Is this genuinely new info, or rehash of well-known material?
   - 0=Nth coverage of known territory
   - 3=novel research result, surprising benchmark, new tool

5. depth (0-3): Analytical/detailed vs surface-level?
   - 0=headline announcement only
   - 3=research paper, deep technical walkthrough, comparative analysis

6. operational_impact (0-3): Does this affect systems the operator currently runs or active candidates (Ollama, Goose, OpenCode, OPNsense, Caddy, etc.)?
   - 0=no impact on operator's stack
   - 3=direct effect on locked stack components

7. time_sensitivity (0-2): Does this require attention soon (security advisory, breaking-change release, time-limited)?
   - 0=evergreen
   - 2=urgent (security/breaking change in next 24-48h)

ANTI-PATTERNS (force final_score=0 regardless of dimensions): marketing fluff with no substance, redundant tutorials, pure speculation, closed-source product PR, crypto/blockchain noise, AI doomerism/pure hype, off-stack frontend framework news.

ARTICLE TO SCORE:
Title: {title}
URL: {url}
Summary: {summary}

Respond with ONLY a JSON object, no preamble or explanation, with exactly these keys:
{{
  "source_quality": <int 0-3>,
  "domain_fit": <int 0-3>,
  "actionability": <int 0-3>,
  "novelty": <int 0-3>,
  "depth": <int 0-3>,
  "operational_impact": <int 0-3>,
  "time_sensitivity": <int 0-2>,
  "anti_pattern_triggered": <bool>,
  "anti_pattern_name": <string or null>,
  "reasoning": <string, one sentence>
}}
"""


REQUIRED_KEYS = [
    "source_quality", "domain_fit", "actionability", "novelty",
    "depth", "operational_impact", "time_sensitivity",
    "anti_pattern_triggered", "reasoning",
]
DIM_RANGES = {
    "source_quality":     (0, 3),
    "domain_fit":         (0, 3),
    "actionability":      (0, 3),
    "novelty":            (0, 3),
    "depth":              (0, 3),
    "operational_impact": (0, 3),
    "time_sensitivity":   (0, 2),
}


def open_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def call_ollama(prompt: str, model: str, timeout: int = 90) -> dict:
    """Call Ollama generate API with format=json. Returns parsed Ollama response dict."""
    body = json.dumps({
        "model":   model,
        "prompt":  prompt,
        "format":  "json",
        "stream":  False,
        "options": {"temperature": 0, "num_ctx": 4096},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def parse_score_response(ollama_resp: dict) -> tuple[dict, str]:
    """Extract + validate the structured score JSON from Ollama's response.

    Returns (parsed_score, raw_response_text).
    Raises ValueError if response is malformed.
    """
    raw = ollama_resp.get("response", "")
    if not raw:
        raise ValueError("Empty response from Ollama")

    # format=json should give valid JSON in 'response' field
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ollama returned invalid JSON: {e}; raw={raw[:200]!r}")

    missing = [k for k in REQUIRED_KEYS if k not in parsed]
    if missing:
        raise ValueError(f"Missing keys in score response: {missing}; got {list(parsed.keys())}")

    # Range validation
    for dim, (lo, hi) in DIM_RANGES.items():
        v = parsed[dim]
        if not isinstance(v, int) or v < lo or v > hi:
            raise ValueError(f"Dimension {dim} out of range: {v!r} (expected int {lo}-{hi})")

    return parsed, raw


def compute_final_score(scores: dict) -> int:
    if scores.get("anti_pattern_triggered"):
        return 0
    return sum(scores[d] for d in DIM_RANGES.keys())


def score_article(db_path: str, article_id: int, model: str = DEFAULT_MODEL) -> dict:
    conn = open_db(db_path)
    try:
        article = conn.execute(
            "SELECT id, title, url, summary FROM articles WHERE id = ?",
            (article_id,),
        ).fetchone()
        if article is None:
            raise ValueError(f"No article with id={article_id}")

        prompt = RUBRIC_PROMPT_TEMPLATE.format(
            title=article["title"],
            url=article["url"],
            summary=(article["summary"] or "")[:1500],   # cap summary to keep prompt lean
        )
        print(f"Scoring article {article_id} with {model}...", file=sys.stderr)
        ollama_resp = call_ollama(prompt, model)
        scores, raw = parse_score_response(ollama_resp)

        final = compute_final_score(scores)
        passed = 1 if final >= TECHNICAL_THRESHOLD else 0

        # Idempotent: REPLACE on (article_id, scorer, model) conflict
        conn.execute(
            """
            INSERT INTO article_scores (
                article_id, scorer, model,
                dim_source_quality, dim_domain_fit, dim_actionability,
                dim_novelty, dim_depth, dim_operational_impact, dim_time_sensitivity,
                final_score, threshold, threshold_pass, raw_response, reasoning
            ) VALUES (?, 'technical', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_id, scorer, model) DO UPDATE SET
                dim_source_quality     = excluded.dim_source_quality,
                dim_domain_fit         = excluded.dim_domain_fit,
                dim_actionability      = excluded.dim_actionability,
                dim_novelty            = excluded.dim_novelty,
                dim_depth              = excluded.dim_depth,
                dim_operational_impact = excluded.dim_operational_impact,
                dim_time_sensitivity   = excluded.dim_time_sensitivity,
                final_score            = excluded.final_score,
                threshold              = excluded.threshold,
                threshold_pass         = excluded.threshold_pass,
                raw_response           = excluded.raw_response,
                reasoning              = excluded.reasoning,
                scored_at              = datetime('now')
            """,
            (
                article_id, model,
                scores["source_quality"], scores["domain_fit"], scores["actionability"],
                scores["novelty"], scores["depth"], scores["operational_impact"], scores["time_sensitivity"],
                final, TECHNICAL_THRESHOLD, passed, raw, scores["reasoning"],
            ),
        )
        conn.commit()

        return {
            "article_id": article_id,
            "title":      article["title"],
            "model":      model,
            "scores":     {d: scores[d] for d in DIM_RANGES.keys()},
            "anti_pattern_triggered": scores["anti_pattern_triggered"],
            "anti_pattern_name":      scores.get("anti_pattern_name"),
            "final_score":  final,
            "threshold":    TECHNICAL_THRESHOLD,
            "threshold_pass": bool(passed),
            "reasoning":    scores["reasoning"],
            "ollama_eval_count": ollama_resp.get("eval_count"),
            "ollama_total_duration_ms": ollama_resp.get("total_duration", 0) // 1_000_000,
        }
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("db_path")
    ap.add_argument("article_id", type=int)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    result = score_article(args.db_path, args.article_id, args.model)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
