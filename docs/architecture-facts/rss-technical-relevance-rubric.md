# D-17-136 Technical Intelligence RSS: Technical Relevance Scoring Rubric

**Status:** DRAFT — first iteration (refine after first week of results, see Open Questions)
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source of truth:** Master log Section 16 (D-17-136 goals); operator's locked technical stack; substrate doctrine scoring criteria
**Consumer:** D-17-136 (Technical Intelligence RSS)
**Related:** `rss-intelligence-substrate-doctrine.md` (pipeline, substrate shared with D-17-137); `rss-personal-relevance-rubric.md` (parallel structure)

## Purpose

This rubric defines how the D-17-136 pipeline scores ingested articles for technical relevance. Each candidate article is rated across seven dimensions; scores combine (equal weighting, see below) to produce a final relevance rank (0–18) that determines whether the article merits ingestion into the technical digest. The rubric becomes prompt context for the local LLM scoring stage (Ollama, model TBD) in the canonical pipeline: *Miniflux → raw archive → normalizer → SQLite metadata → story clustering → source/perspective scoring → **technical relevance ranker** → daily/weekly digest → [downstream output classifier routes to OpenProject WPs vs benchmark prompts vs Aider/OpenCode task briefs]*.

Per master log §16, D-17-136's goals are: freshness, retrieval grounding, technical awareness, release tracking, benchmark/tool candidate discovery, weekly synthesis. This rubric decides *ingestion-worthiness*; a separate downstream classifier (future WP) routes qualifying items to their output sink.

## Scoring Dimensions

### 1. Source Quality (0–3 scale)

**Definition:** Is this source one you already trust for technical accuracy and completeness?

Examples:
- **Low (0):** Unknown publisher, unverified technical claims, no peer review signal.
- **Mid (1–2):** Established tech publication (Ars Technica, The Register), reputable tool blogs (Ollama docs, Hugging Face blog), academic preprints (arXiv).
- **High (3):** Operator's locked technical feeds (official Anthropic/OpenAI/Google blogs, GitHub release atoms, arXiv cs.AI, system-design bloggers like ByteByteGo).

### 2. Technical-Domain Fit (0–3 scale)

**Definition:** Does this article touch one of your locked technical domains?

Examples:
- **Low (0):** Frontend framework trends (React, Vue), generic SaaS news, marketing/business content.
- **Mid (1–2):** Related but not directly in scope (e.g., GPU memory optimization touches model layer but is academic theory only; Kubernetes news is system-design adjacent but you don't run clusters).
- **High (3):** Directly in your stack: AI/ML research (LLM training, benchmarks, papers), local agent ecosystem (Aider, Cline, OpenCode, Goose, Continue, Serena MCP, OpenHands), model layer (Ollama, Gemma, Qwen3-Coder, Claude, deepseek), self-hosted infra (OPNsense, Caddy, Vault, Headscale, Restic, Zabbix, MinIO), hardware platform (MS-01, Mac Studio M3 Ultra, Mac Mini Pro, RTX 4070, QNAP).

### 3. Actionability (0–3 scale)

**Definition:** Can you materially change something: code, model, tool, benchmark version, or config?

Examples:
- **Low (0):** "The History of ML Optimization" — background reading, no concrete action.
- **Mid (1–2):** "New Claude 4.1 API Features" — you may use Claude but don't run the model; useful awareness, limited direct action.
- **High (3):** "Ollama v0.4 Supports Quantization" — you run Ollama; actionable model optimization. "Aider 0.50 Release" — direct tool adoption or upgrade decision.

### 4. Novelty (0–3 scale)

**Definition:** Is this genuinely new research, release, or analysis?

Examples:
- **Low (0):** Nth coverage of "transformers are powerful" with no new data or insight.
- **Mid (1–2):** New model release (already announced elsewhere), but comparison to prior versions is useful context; familiar pattern, new instance.
- **High (3):** Novel benchmark result, breakthrough paper, first coverage of a release, substantively different comparative analysis (e.g., "Why Local LLMs Beat API Calls for Latency-Sensitive Tasks").

### 5. Depth (0–3 scale)

**Definition:** Research-grade or hands-on deep dive, or surface announcement?

Examples:
- **Low (0):** Headline only ("OpenAI released GPT-5"). Shallow listicles ("5 AI Tools to Try").
- **Mid (1–2):** Explanation + context ("Model X released; here are the improvements and benchmark gains").
- **High (3):** Research paper, detailed benchmark analysis, deep technical walkthrough of architecture, well-reasoned architectural post with code examples.

### 6. Operational Impact (0–3 scale)

**Definition:** Does this affect systems you currently run or active tool candidates?

Examples:
- **Low (0):** Affects other organizations' stacks (e.g., Kubernetes security fix if you don't run K8s).
- **Mid (1–2):** Affects adjacent tools you're aware of but don't actively use (e.g., Radarr bug fix if you run Sonarr).
- **High (3):** Directly impacts your platform (Ollama security update, Aider breaking change, QNAP firmware release, Mac Studio M3 performance tips, Zabbix monitoring rule update).

### 7. Time Sensitivity (0–2 scale)

**Definition:** Does this require action or awareness in the next 7 days?

Examples:
- **Low (0):** Evergreen ("How to Optimize LLM Inference — Part 1"). Historical analysis.
- **High (2):** Security advisory, breaking change in a tool you use, deprecation timeline beginning, benchmark opportunity (e.g., VRAM optimization contest deadline).

*Note: 0–2 scale (not 0–3) to prevent over-weighting urgency.*

## Weighting and Final Score

**Equal weighting by default:** Sum all dimensions without additional multipliers. Final score = Source (0–3) + Domain (0–3) + Actionability (0–3) + Novelty (0–3) + Depth (0–3) + Impact (0–3) + TimeSensitivity (0–2) = **0–18 scale**.

**Threshold for inclusion:** Articles scoring 11+ are candidates for the technical digest. Operator may adjust threshold after first week of results; start at 11 as baseline.

**Reasoning for equal weighting:** No single dimension dominates. A high-depth research paper from an untrusted source scores mid; high novelty in an unrelated domain is noise; high impact on inactive systems is background. Actionability + domain fit + operational impact should reinforce, not override, source quality.

## Anti-Patterns (Suppress Regardless of Scores)

Regardless of dimensional scores, apply these hard filters:

1. **Marketing fluff / product PR** — vendor announcement with no technical substance, closed-source product overview with no depth.
2. **Redundant tutorials** — yet another "Getting Started with Tool X" with no novel angles.
3. **Pure speculation** — no data, no code, no evidence ("AI Will Destroy Jobs"; "Blockchain Will Revolutionize Everything").
4. **Closed-source product news with no value signal** — commercial AI startup funding rounds, proprietary tool releases without benchmark data.
5. **Crypto / blockchain noise** — cryptocurrency price news, NFT hype, unrelated to your technical stack.
6. **AI doomerism / pure hype** — existential risk speculation, unrealistic timelines, no technical grounding.
7. **Off-stack frontend framework news** — React/Vue/Angular updates if they don't touch your local agent stack or UI automation needs.

**Implementation:** Pre-filter before scoring (if any anti-pattern detected, score = 0 regardless of dimension scores).

## Boost Conditions (Reward High Scores)

1. **Operator's locked technical stack:** If an article comes from one of your curated technical feeds (official GitHub releases for your tools, arXiv cs.AI, Anthropic/OpenAI official blogs, ByteByteGo, system-design specialists), floor score at 11 (always ingested unless anti-pattern triggered).
2. **Multi-dimension hits:** If an article scores 3 on both Actionability and Operational Impact (your current stack + you can act), add +2 to final score.

## Output Signal Vector

The rubric emits per-dimension scores (not just final rank) into SQLite metadata. A downstream output classifier (separate WP, not this one) uses these signals to route qualifying items to their sink:

- **OpenProject WP (technical digest):** High Depth + High Novelty + High Source Quality → deep-dive documentation ticket
- **Benchmark prompt:** High Novelty + High Domain Fit + Medium/High Depth → "evaluate this new model on our benchmarks"
- **Aider/OpenCode task brief:** High Actionability + High Operational Impact → "implement this feature / fix this bug"

The routing logic is deferred to the output-classifier WP (not designed here).

## Open Questions for Operator Validation

1. **Operational Impact vs Domain Fit:** If an article scores high on domain fit but low on operational impact (e.g., novel academic AI research not yet productized), should it still be ingested? Current rubric treats them equally; may need weighting adjustment.

2. **Model-layer specificity:** Your model layer includes Ollama, Gemma, Qwen3-Coder, Claude, deepseek. Should articles about closed-source models (Claude, GPT-5) score differently than open-source? (Privacy/control angle might matter.)

3. **Release-frequency handling:** Tools in your stack (Aider, Cline, Zabbix, Ollama) release frequently. Should high-frequency releases get discount (noise reduction) or stay high-scored? (Weekly Ollama updates might fatigue.)

4. **Hardware platform coverage:** MS-01, Mac Studio M3 Ultra, RTX 4070 are specialized. Articles on GPU optimization for NVIDIA might not apply to Apple Silicon. Should technical-domain fit penalize "wrong hardware" even if the research is deep?

5. **Competitor intelligence:** Should closed-source competitor products (other AI companies' models) score differently? (Potential learning source vs outside your stack.)

## Pipeline Integration

The rubric is embedded as **prompt context** in the technical-relevance-ranker stage of the D-17-136 pipeline. The local LLM (Ollama, model **TBD — dependency on LLM model selection**) is instructed: "Score this article against the rubric dimensions; return final score + per-dimension breakdown + reasoning." Current candidates: `qwen2.5-coder-7b` (optimized for code, may underweight non-code research papers), `gemma2:27b` (balanced reasoning, slower). Operator should validate model choice after first week of rubric application.

Score, per-dimension breakdown, and reasoning cached in SQLite metadata for human audit (operator can review why each article scored high/low, identify rubric gaps, refine iteratively).

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — pipeline context, substrate shared with D-17-137
- `docs/architecture-facts/rss-personal-relevance-rubric.md` — parallel structure (sibling rubric for D-17-137)
- `docs/PROJECT_FRAMEWORK.md` D-17-136 — Technical Intelligence RSS framework row (outputs: OpenProject WPs, benchmark prompts, task briefs)
- `docs/architecture-facts/rss-feed-list-curated.md` — operator's locked technical feed sources
- Master log Section 16 (RSS intelligence ingestion, 2026-05-06) — goals: freshness, retrieval grounding, technical awareness, release tracking, benchmark candidate discovery, weekly synthesis
