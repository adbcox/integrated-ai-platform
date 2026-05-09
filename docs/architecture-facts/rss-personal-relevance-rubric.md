# D-17-137 Personal Briefing Engine: Personal Relevance Scoring Rubric

**Status:** DRAFT — first iteration (refine after first week of results, see Open Questions)
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source of truth:** Operator's stated interest domains (KI-B-01); substrate doctrine scoring criteria
**Consumer:** D-17-137 (Personal Briefing Engine)
**Related:** `rss-intelligence-substrate-doctrine.md` (pipeline, anti-patterns: outrage-framing rejected)

## Purpose

This rubric defines how the D-17-137 pipeline scores ingested articles for personal relevance. Each candidate article is rated across six dimensions; scores combine (equal weighting, see below) to produce a final relevance rank (0–15) that determines whether the article appears in the daily briefing. The rubric becomes prompt context for the local LLM scoring stage (Ollama, model TBD) in the canonical pipeline: *Miniflux → raw archive → normalizer → SQLite metadata → story clustering → source/perspective scoring → **personal relevance ranker** → daily briefing*.

## Scoring Dimensions

### 1. Source Quality (0–3 scale)

**Definition:** Is this source one you already trust, or unknown?

Examples:
- **Low (0):** First-time publisher, no reputation signals, unsourced claims.
- **Mid (1–2):** Established tech news outlet (Ars Technica, Engadget), reputable specialist blogs (Home Assistant, Blender Nation), academic preprints (arXiv).
- **High (3):** Operator's locked RSS feeds (Hacker News via hnrss, ByteByteGo, Anthropic blog, official project releases).

### 2. Personal Interest Fit (0–3 scale)

**Definition:** Does the article touch one of your six locked interest domains?

Examples:
- **Low (0):** Celebrity gossip, sports, politics not explicitly tied to your domains, unrelated finance.
- **Mid (1–2):** Adjacent to but not directly in scope (e.g., semiconductor supply chain touches hardware but is not hardware news; blockchain touch AI/research but not directly).
- **High (3):** Directly in one of: AI/research, system-design, home-automation, self-hosting/ARR, hardware, 3D-design. Multiple domain hits get boost (see below).

### 3. Actionability (0–3 scale)

**Definition:** Can you do something with this? Or is it pure background?

Examples:
- **Low (0):** "10 Surprising Facts About Coffee" — entertainment, no action path.
- **Mid (1–2):** "Kubernetes 1.30 Released — Here's What's New" — you track Kubernetes but don't run clusters; useful awareness, limited action.
- **High (3):** "Jellyfin 10.9 with AV1 Transcoding" — you run Jellyfin; actionable upgrade decision. "New ArduinoIDE Supports ESP32-S3" — you do hardware DIY.

### 4. Novelty (0–3 scale)

**Definition:** Is this genuinely new information, or a rehash?

Examples:
- **Low (0):** Article repeats conclusions already known (e.g., fourth coverage of "AI is improving rapidly" with no new data).
- **Mid (1–2):** New angle or new data, but not urgent (e.g., another writeup of Transformer architecture variants; useful but familiar pattern).
- **High (3):** Novel research result, surprising benchmark, new feature/tool, first coverage of a trend, substantively different analysis from prior coverage.

### 5. Depth (0–3 scale)

**Definition:** Analytical and detailed, or surface-level?

Examples:
- **Low (0):** Headline summary only ("X announced Y feature"). Listicles with no substance ("Top 5 Python Tricks").
- **Mid (1–2):** Summary + explanation ("X announced Y; here's why it matters" or "Tutorial: How to set up Z in 5 steps").
- **High (3):** Research paper, deep technical walkthrough, comparative analysis, well-reasoned opinion piece with evidence.

### 6. Time Sensitivity (0–2 scale)

**Definition:** Does this require attention in the next 24–48h, or is it evergreen?

Examples:
- **Low (0):** Evergreen content ("The History of RSS"; "How to Choose a Notebook").
- **High (2):** Security advisory, product release you'll want to try soon, time-limited offer, event announcement happening within a week.

*Note: 0–2 scale (not 0–3) to prevent over-weighting urgency.*

## Weighting and Final Score

**Equal weighting by default:** Sum all dimensions without additional multipliers. Final score = Source (0–3) + Interest (0–3) + Actionability (0–3) + Novelty (0–3) + Depth (0–3) + TimeSensitivity (0–2) = **0–17 scale**.

**Threshold for inclusion:** Articles scoring 10+ appear in the daily briefing. Operator may adjust threshold after first week of results; start at 10 as baseline.

**Reasoning for equal weighting:** No one dimension should dominate. A high-depth article from a low-trust source should not automatically rank high; actionability without personal interest fit is noise; novelty in an unrelated domain is off-topic.

## Anti-Patterns (Suppress Regardless of Scores)

Regardless of dimensional scores, apply these hard filters:

1. **Outrage-framing narrative** — articles designed to provoke emotional reaction ("This Will SHOCK You", "They Don't Want You to Know", manufactured controversy).
2. **Clickbait with no substance** — sensational headline with empty or misleading content.
3. **Paywalled with no preview** — article requires subscription; preview is insufficient to evaluate.
4. **Duplicate/low-quality rehash** — same story covered identically by multiple sources; low-quality source takes precedence (suppress higher-volume noise).
5. **Unsubstantiated claims** — no sources, no data, pure speculation presented as fact.
6. **Off-topic spam** — crypto/NFT promotions, dropshipping links, unrelated affiliate content.

**Implementation:** Pre-filter before scoring (if any anti-pattern detected, score = 0 regardless of dimension scores).

## Boost Conditions (Reward High Scores)

1. **Multi-domain hit:** If an article touches 2+ of your locked domains, add +2 to final score. (E.g., "DIY NAS Build with AI Training" touches home-automation + hardware + AI/research → boost.)
2. **Operator-locked sources:** If the article comes from one of your curated feeds (Hacker News, ByteByteGo, official Anthropic/OpenAI/Hugging Face blogs, GitHub releases), floor score at 10 (always appears unless anti-pattern triggered).

## Open Questions for Operator Validation

1. **Novelty vs Depth:** If an article is highly novel but shallow, vs deep but somewhat familiar, which wins? Current rubric treats them equally.

2. **Political news scope:** System-design articles sometimes touch policy/regulations (e.g., "New EU Regulations on AI Training Data"). Should these get political interest boost or avoided entirely?

3. **Niche depth:** Deeply technical articles on obscure tools you don't use (e.g., "Advanced CadQuery for Computational Geometry"). High depth, low actionability. Score correctly as mid-relevance, or suppress?

4. **Source quality decay:** Should an article from a usually-trusted source that makes a sensational claim score lower than normal? (Trade-off: trust the source or penalize the claim?)

## Pipeline Integration

The rubric is embedded as **prompt context** in the personal-relevance-ranker stage of the D-17-137 pipeline. The local LLM (Ollama, model **TBD — dependency on LLM model selection**) is instructed: "Score this article against the rubric dimensions; return final score + reasoning." Current candidates: `qwen2.5-coder-7b` (fast, coding-oriented, may underweight humanities news), `gemma2:27b` (larger, better reasoning, slower). Operator should validate model choice after first week of rubric application.

Score + reasoning cached in SQLite metadata for human audit (operator can review why each article scored high/low, refine rubric iteratively).

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — pipeline context, anti-patterns (outrage-framing), substrate shared with D-17-136
- `docs/PROJECT_FRAMEWORK.md` D-17-137 — Personal Briefing Engine framework row
- `docs/architecture-facts/rss-feed-list-curated.md` — operator's six locked interest domains
- Master log Section 17 (Roca-style Personal Briefing Engine, 2026-05-06)
