# RSS Pipeline Orchestrator Doctrine

**Status:** DRAFT — first iteration (recipe definitions iterate after first deploy)
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source of truth:** Goose capability boundary (D-17-13), substrate doctrine, circulatory doctrine (Mac Mini Pro orchestration / Mac Studio inference), userMemories "Goose+Ollama for non-coding agentic tasks"
**Consumers:** D-17-136 (Technical Intelligence RSS), D-17-137 (Personal Briefing Engine)
**Related:** `rss-intelligence-substrate-doctrine.md` (pipeline plumbing), `rss-technical-relevance-rubric.md` (signals produced), `rss-personal-relevance-rubric.md` (signals produced), `rss-technical-output-classifier.md` (routing logic), `goose-capability-boundary.md` (Goose posture)

## Purpose

This doctrine closes the orchestrator-layer gap in the existing RSS design. The substrate doctrine, rubrics, and output classifier define *what* the pipeline does but not *who calls whom* or *how state flows*. This document specifies the Goose recipe set that executes the RSS pipeline end-to-end: which stage runs as which recipe, how models are routed, how state persists, how scheduling works, and how failures are handled.

## Orchestrator selection: Goose + Ollama

**Locked choice:** Goose (Block/AAIF Apache-2.0 Rust agent with MCP extensions and recipe support) orchestrates the RSS pipeline. Models run via Ollama, routed through litellm-gateway. Justification: per userMemories ("Goose+Ollama for non-coding agentic tasks") and locked posture in `goose-capability-boundary.md` (capability-validation phase, read-only MCP extensions enabled, developer extension disabled). Substrate doctrine explicitly excludes n8n (fair-code, not true OSS) for the RSS pipeline.

Parallel evaluation (B2.2 Goose evaluation, referenced in full-upgrade-master-project-plan tracks B2.2/B2.8/B4) is independent work. This recipe set proceeds in design phase regardless of B2.2 outcome. If B2.2 rejects Goose for broader workstation use, RSS recipes can remain as a bounded Goose deployment on Mac Mini Pro, OR recipes can be ported to whatever agent wins B2.2 (recipes are portable; the pipeline logic is agnostic to orchestrator implementation).

## Recipe structure

**One master recipe + stage recipes:** The pipeline is implemented as a Goose recipe set with one orchestrator recipe (chains stage recipes) plus individual recipes for each pipeline stage. This mirrors the precedent of parallel D-17-160 media-ops recipes (design complete; same orchestration host, separate domains).

**Recipe set definition:**
1. `poll-feeds` — invoke Miniflux API, fetch new articles, write raw articles to QNAP archive
2. `normalize-dedupe-classify` — read raw archive, idempotent normalizer (dedupe by URL hash), write metadata to SQLite
3. `embed-summarize` — read SQLite articles, call Ollama embedding + summarization stage, write embeddings to SQLite
4. `score-technical-relevance` — read SQLite, call Ollama with technical-relevance rubric, cache per-dimension scores + final rank
5. `score-personal-relevance` — read SQLite, call Ollama with personal-relevance rubric, cache per-dimension scores + final rank (D-17-137 only)
6. `classify-technical-output` — read SQLite with technical scores ≥11, call Ollama with output-classifier logic, emit routing decision + template fills
7. `emit-openproject-wps` — consume classifier output, write OpenProject WPs via API (D-17-136 only)
8. `emit-benchmark-prompts` — consume classifier output, write benchmark prompts to substrate (D-17-126/129 targets)
9. `emit-aider-task-briefs` — consume classifier output, write task briefs to queue (D-17-XXX task queue)
10. `emit-personal-briefing` — consume personal-relevance scores, aggregate, write to operator-chosen sink per KI-B-02 (D-17-137 only)
11. `master-orchestrator` — schedule and chain the above recipes; logs stage latencies, handles failures, emits Zabbix signals

## Model routing per stage

| Stage | Model class | Specific model (baseline) | Route | Reasoning |
|---|---|---|---|---|
| embed-summarize | Embedding + summarization | nomic-embed-text:latest + qwen2.5-coder:14b (inference) | Mac Studio → litellm-gateway | Embedding required for RAG; summary for context window. Baseline from D-17-12; may change per B3.T2 benchmark results. |
| score-technical-relevance | Scoring (rubric-guided) | qwen2.5-coder:32b (inference) | Mac Studio → litellm-gateway | Sufficient for structured scoring; T1 priority tier. |
| score-personal-relevance | Scoring (rubric-guided) | qwen2.5-coder:32b (inference) | Mac Studio → litellm-gateway | Same as technical-relevance; parallel pipeline. |
| classify-technical-output | Routing decision + template fill | qwen2.5-coder:32b (inference) | Mac Studio → litellm-gateway | Deterministic routing rules in prompt context; template fill handled by same model. |

**Model selection rationale:** T1 priority tier (qwen2.5-coder:32b on Mac Studio Ollama) is the baseline for routine platform work per `PROJECT_FRAMEWORK.md` §3.1. Subsequent model choices (B3.T2 benchmark) may justify T2 (subagent chain decomposer/implementer) or T3 (specialty models) if measurably superior on RSS tasks. Recipes specify model class + role; specific model swapped via config file without recipe reimplementation.

## State management

**SQLite metadata store** (per substrate doctrine): canonical query layer. Each recipe writes idempotent outputs:
- `articles` table: article_id (URL hash), raw_text, source_url, fetch_timestamp, normalized_text, embed_vector, summary
- `scores_technical` table: article_id, source_q, domain_fit, actionability, novelty, depth, operational_impact, time_sensitivity, final_rank, reasoning
- `scores_personal` table: article_id, source_q, interest_fit, actionability, novelty, depth, time_sensitivity, final_rank, reasoning (D-17-137)
- `routing_decisions` table: article_id, output_type (enum: digest-only / openproject-wp / benchmark-prompt / aider-task-brief), template_rendered_json, sink_status (pending / emitted / failed)
- `feed_health` table: feed_url, last_fetch_timestamp, consecutive_failures, status_enum (healthy / unavailable / deprecated)

**Idempotency:** Each recipe is re-entrant; running stage `N` twice does not duplicate output. Implemented via upserts on article_id (primary key) and idempotent sink writes (OpenProject checks for WP existence before creating).

## Trigger and scheduling

**Launchd timer on Mac Mini Pro (.145):** Master orchestrator runs daily via launchd plist (location: `~/Library/LaunchAgents/com.operatorai.rss-pipeline.plist` or similar). Invocation: `goose run --config config/goose/config.yaml --recipe master-orchestrator`.

**Rationale for launchd:** Phase B Linux VM substrate (running containers on self-hosted orchestration cluster) does not yet exist (expected Phase B4 delivery per full-upgrade-master-project-plan). Once Linux VM substrate exists, migrate to systemd timer on orchestration node. Recipes remain unchanged; only trigger mechanism changes.

**Development/testing:** Operator can invoke individual recipes manually via `goose run --recipe <recipe-name>` for debugging without waiting for scheduled run.

## Failure handling

**Transient errors (network, Ollama timeout):** Retry once after 5-second backoff. If retry succeeds, continue. If retry fails, log to Zabbix and emit alert (see Monitoring below).

**Feed-level errors (feed URL 404, parser error):** Mark feed as `unavailable` in feed_health table after 3 consecutive failures. Operator review required to re-enable. Do not halt pipeline; continue with remaining feeds.

**LLM scoring errors (Ollama unresponsive, model timeout):** Retry once. If persistent, fail the article to digest-only (default route in output classifier) and log error. Do not block downstream recipes.

**Sink write errors (OpenProject API 500, queue full):** Queue article for retry on next orchestrator run (state persisted in routing_decisions table). Max 3 retries; after that, manual operator intervention required.

## Sink integration touchpoints

**D-17-136 outputs:**
- OpenProject WP sink: `emit-openproject-wps` recipe writes via OpenProject REST API (authenticated; credentials in Vault)
- Benchmark prompt sink: `emit-benchmark-prompt` recipe appends to SQLite benchmark-intake table (D-17-126 job reads this table separately)
- Aider task brief sink: `emit-aider-task-briefs` recipe writes JSON to `~/.config/aider/rss-task-queue.jsonl` (Aider reads this file for task suggestions)

**D-17-137 outputs:**
- Personal briefing sink: `emit-personal-briefing` recipe writes to operator-chosen sink (pending KI-B-02 decision: Obsidian Vault / Nextcloud / daily email). Abstraction: sink-specific writer plugin in recipes.

## Relationship to D-17-160 (media-ops recipes) — NOTE: D-17-160 unverified in PROJECT_FRAMEWORK

Both D-17-136 (RSS) and D-17-160 (media-ops) recipe sets run on Mac Mini Pro (.145) as Goose deployments. Shared infrastructure:
- Goose configuration: `config/goose/config.yaml` (single provider + model config; recipes read this)
- Ollama backend: Mac Studio .142 (both recipes call same Ollama instance via litellm-gateway)
- SQLite paths: separate metadata databases per system (`~/.local/share/rss-metadata.db` vs `~/.local/share/media-metadata.db`); no cross-system query.
- Logging: both emit to Zabbix under separate item keys (rss.recipe.poll vs media.recipe.transcode)

Separate domains: RSS recipes score articles for ingestion; media-ops recipes orchestrate media transcoding / archival. No recipe-to-recipe dependencies.

## Relationship to B2.2 Goose evaluation — NOTE: B2.2 tracks unverified in PROJECT_FRAMEWORK / full-upgrade-master-project-plan

This RSS recipe set proceeds in design phase independent of B2.2 broad-evaluation outcome. The B2 roadmap evaluates whether Goose is the platform's default agent for autonomous coding, workstation orchestration, and operational tasks. If B2.2 concludes that Goose is NOT the winner (e.g., OpenHands, Claude Code, or another agent wins), then:

1. **RSS recipes remain as a bounded Goose deployment:** Mac Mini Pro continues to run RSS Goose recipes because they are stable, tested, and self-contained. B2.2 winner does not replace them.
2. **OR: Recipes are ported to the B2.2 winner:** If the B2.2 winner is compatible (has recipes / workflow / orchestration capability), port the recipe set to that agent. Pipeline logic is recipe-agnostic; only the recipe DSL and orchestrator invocation changes. Estimated porting effort: 20–40% (test suite re-run, minor syntax updates, agent-specific capability checks).

No blocking dependency. Design proceeds.

## Open questions for operator validation

1. **D-17-160 precedent:** The task references D-17-160 (media-ops Goose recipes, DESIGN COMPLETE) as parallel work. Verify that D-17-160 exists in PROJECT_FRAMEWORK.md and that its recipe structure is accurately characterized here. (Lookup: grep PROJECT_FRAMEWORK for D-17-160; check for docs/architecture-facts/d-17-160-* or similar.)

2. **B2.2 / B2.8 / B4 roadmap tracks:** The task references full-upgrade-master-project-plan with B2.2 (Goose evaluation), B2.8 (??), and B4 (??). Verify that this document exists and that the track descriptions match the framing here (B2.2 is agent-selection eval, B4 is Linux VM substrate for Phase B orchestration).

3. **Goose recipe scheduling capability:** This doctrine assumes Goose has a native `--recipe` invocation mode. Verify that Goose 1.33.1 supports recipe execution via CLI. If uncertain, clarify launchd-invocation approach.

4. **Sink write abstraction:** This doctrine assumes individual recipes can write to D-17-136 sinks (OpenProject API, benchmark intake, task-queue file). If some sinks require authentication/credentials, specify whether those credentials are Vault-stored (and thus require `developer` extension re-enabled for Vault access) or file-based (~/.config/).

5. **Cross-recipe state coordination:** In the event that two recipes run concurrently (e.g., operator manually runs `score-technical-relevance` while scheduled orchestrator is running `embed-summarize`), SQLite concurrent-write locking is sufficient to prevent corruption. Verify this assumption or add explicit recipe-lock file.

6. **Model backend swap at runtime:** This doctrine specifies models via config.yaml. If operator wants to use a different model for, say, technical-relevance scoring (Ollama model swap), can the recipe read a per-recipe model override from config/goose/recipes/*.yaml without recipe code changes? (Specificity: is the Goose recipe DSL that flexible?)

## Pipeline integration

The orchestrator layer executes the **chained execution** of the RSS pipeline stages, consuming outputs from the technical-relevance and personal-relevance rubrics (per-dimension scores + final rank cached in SQLite), and applying the output classifier routing logic to emit structured outputs. The master recipe schedules stage recipes on a daily cadence (configurable interval) and logs per-stage latency, memory usage, and error counts to Zabbix for operator observability.

Template iteration: After first week of deployed recipes, review actual execution times, Ollama model latency per stage, and whether recipe boundaries (stage granularity) make sense in practice. Refine recipe structure, model routing, or scheduling based on observed metrics.

## Small follow-up commit

A subsequent commit (separate, not this one) will add cross-references FROM the existing rubric and classifier docs TO this orchestrator doctrine. Files to update:
- `rss-technical-relevance-rubric.md` — "Pipeline Integration" section notes the orchestrator doctrine
- `rss-personal-relevance-rubric.md` — same cross-reference update
- `rss-technical-output-classifier.md` — same

## Cross-references

- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — substrate plumbing (parent)
- `docs/architecture-facts/rss-technical-relevance-rubric.md` — technical signals (upstream input to orchestrator)
- `docs/architecture-facts/rss-personal-relevance-rubric.md` — personal signals (upstream input to orchestrator)
- `docs/architecture-facts/rss-technical-output-classifier.md` — routing logic (stage-6 input to emit recipes)
- `docs/architecture-facts/goose-capability-boundary.md` — Goose posture (capability-validation phase, extensions enabled/disabled)
- `docs/architecture-facts/goose-session-pipeline.md` — Goose execution evidence / chronicle pattern
- `docs/PROJECT_FRAMEWORK.md` — D-17-136, D-17-137, D-17-160 (unverified), B2.2/B4 track references (unverified)
- `docs/PHASE_ROADMAP.md` — Phase B Linux VM substrate timeline
- `config/goose/config.yaml` — Goose provider/model configuration (orchestration host)
- userMemories — "Goose+Ollama for non-coding agentic tasks" (locked choice rationale)
