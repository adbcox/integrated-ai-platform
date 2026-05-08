# Sakana AI — RL Conductor / Fugu (multi-agent orchestration)

**Date evaluated:** 2026-05-08
**Source:** `https://venturebeat.com/orchestration/how-sakana-trained-a-7b-model-to-orchestrate-gpt-5-claude-sonnet-4-and-gemini-2-5-pro` (VentureBeat, paywalled/429-blocked); primary source `https://sakana.ai/learning-to-orchestrate/` (Sakana AI's own blog post, April 27 2026); paper `https://arxiv.org/abs/2512.04388` (ICLR 2026 accepted)
**Authors:** Sakana AI research team (correspondence: Stefan Nielsen, Edo, Yujin Tang)
**Publication venue:** ICLR 2026 (accepted, peer-reviewed)
**Evaluator:** Claude (Opus 4.7) session, 2026-05-08
**Status:** EVALUATED — protocol applied through Step 4
**Protocol reference:** `architecture-facts/article-intake-protocol.md`

## Source notes (Step 1)

Read primary Sakana post + arxiv abstract + multiple aggregator articles for triangulation. Article CLAIMS:

- **Architecture:** Train a 7B model (base: Qwen2.5-7B) via Reinforcement Learning to orchestrate a worker pool of LLMs. Conductor outputs natural-language workflows specifying:
  1. Which agent to call at each step
  2. What subtask to give them (acting as a meta-prompt-engineer)
  3. What context-window visibility (which prior messages they see)
- **Worker pool used in research:** Closed (Gemini 2.5 Pro, Claude Sonnet 4, GPT-5) + Open (DeepSeek-R1-Distill-Qwen-32B, Gemma3-27B-instruct, Qwen3-32B). Up to 5-step workflows.
- **Performance numbers claimed:**
  - 77.27% average across all benchmarks tested
  - 93.3% AIME25 (math)
  - 87.5% GPQA-Diamond (graduate-level science Q&A)
  - 83.93% LiveCodeBench (coding)
  - "New records" claimed at time of publication for LiveCodeBench and GPQA-Diamond
- **Compared against:** Individual frontier models acting alone (GPT-5, Claude, Gemini); self-reflection iterative agents; SOTA multi-agent routing frameworks (MASRouter, Mixture-of-Agents, RouterDC, Smoothie)
- **Claimed cost advantage:** "Fraction of the cost" with "fewer API calls than competitors"
- **Behavioral claims:** Conductor learned to (a) 1-shot easy questions, (b) spin up planner-executor-verifier pipelines for hard problems, (c) sometimes hand entire planning to Gemini 2.5 Pro and itself become a worker, (d) recursive self-call for test-time scaling
- **Training dataset:** 960 problems across MATH, MMLU, RLPR (real-world reasoning), and LiveCodeBench-style coding
- **Commercial productization:** Backbone of Sakana Fugu, a commercial multi-agent service. Two tiers: Mini (latency) and Ultra (full pool). OpenAI-compatible API.
- **Companion research:** TRINITY (announced separately, also powering Fugu)

## Validation (Step 2)

### Prior conversation search

Did not find prior evaluation of Sakana RL Conductor specifically in our session memory. Sakana AI has been mentioned in passing in roadmap context as a research lab to watch, but no prior structured evaluation. **First evaluation** (this is the worked example).

### Repo search

`docs/architecture-facts/strategic-watch.md` exists but Sakana not currently listed. `docs/architecture-patterns/strategic-watch.md` is the canonical strategic-watch register.

`work-routing-doctrine.md` (D-17-95) is operator's existing routing doctrine. `local-model-tier-doctrine.md` is operator's tier framework. `system-prompts/tiers/` contains T1-T4 tier-specific prompts. These are the OPERATOR'S existing routing infrastructure — human-designed, pre-RL.

### Web cross-references

- arxiv 2512.04388 confirms ICLR 2026 acceptance (peer-reviewed, not just blog claim)
- Sakana's own page (sakana.ai/learning-to-orchestrate) is the primary source
- VentureBeat aggregation adds operator commentary from Yujin Tang (Sakana co-founder); confirms Fugu is in commercial use internally for "software development, deep research, strategy development, and even visual tasks like slide generation"
- Independent aggregator (dataworldbank.net) confirms benchmark scores match
- TRINITY companion research separately announced (~April 2026)

### Correctness verdict

**SUBSTANTIATED-WITH-CAVEATS.** The methodology is real, the benchmarks are public, the peer-review acceptance is verifiable. The numbers are credible. Caveats:

1. **"Fraction of the cost"** is misleading at face value. The Conductor's worker pool includes paid frontier APIs (GPT-5, Claude Sonnet 4, Gemini 2.5 Pro). Cost reduction is from FEWER calls per task (smarter orchestration), not from cheaper unit cost. Total inference cost = Conductor inference (cheap, 7B) + multiple frontier API calls per query (expensive). Compared to a single GPT-5 call per query, you might save money by routing simple queries to a cheap open model. Compared to MoA which calls multiple expensive models in parallel, this is genuinely cheaper. But this is NOT free or near-free.

2. **Benchmark scope is narrow.** AIME25, GPQA-Diamond, LiveCodeBench. Strong on math/science/coding reasoning; not evaluated on tasks like long-document summarization, conversation, or domain-specific work outside the training distribution.

3. **"Beats individual frontier models"** holds for these benchmark suites only. Not a claim about general capability.

4. **License of Conductor weights is unclear.** Sakana's blog says Fugu is commercial. The arxiv paper may release training methodology + weights for reproducibility (ICLR norms vary). Without open weights, this is APIs-as-a-service (Fugu), not a self-hostable component. Need to verify weight release status before any adoption decision.

5. **Training cost not disclosed.** RL with frontier-API workers in the loop is expensive. The 960-problem dataset suggests training at scale; reproducing this on operator's hardware (Mac Studio + Threadripper #1 + RTX 4070 12GB) is unlikely without weeks of dedicated time.

## Roadmap fit (Step 3)

### Conceptual fit

**STRONG.** The Conductor pattern directly maps to operator's existing routing infrastructure:

- Operator's `work-routing-doctrine.md` (D-17-95) — TIER 1 Aider / TIER 2 Claude Code+Codex / TIER 3 Frontier escalation — is human-designed routing
- Operator's `local-model-tier-doctrine.md` — T1-general / T2-throughput / T3-specialty / T4-distributed — is human-designed tier mapping
- Operator's `local-prompt-library-doctrine.md` (D-17-90) — voice-fast / deliberate-analysis / code-review / decomposition-planning / capability-permission modes — is human-designed prompt routing
- Operator's `litellm-routing.md` — gateway pattern for routing to right backend

The Sakana Conductor pattern is essentially "what if we replaced the human-designed routing logic with an RL-trained 7B model that learns the routing from outcomes?" This is a GENERALIZATION of existing routing infrastructure, not a replacement.

### Hardware fit

**ADEQUATE for inference; insufficient for training.**

- Conductor inference (7B Qwen2.5 base): fits trivially on Mac Mini Pro M4 Pro 48GB via Ollama (~5-10 GB at common quantizations). Mac Mini Pro is the orchestration host per the circulatory doctrine; the Conductor's function IS orchestration, so this is the doctrinally-correct placement (NOT Mac Studio, which is the inference organ for the worker pool).
- Worker pool inference: already supported via Mac Studio Ollama (Qwen2.5-Coder-32B/14B, Gemma 2 27B, Qwen3-Coder-30B per existing `local-model-tier-doctrine.md`). Frontier-API workers via Anthropic Pro (`claude-pro` alias) for the rare escalation case.
- Conductor TRAINING: not feasible on this hardware. RL with 960 problems × multi-step rollouts × frontier API calls per rollout = significant compute + significant API spend. Would need dedicated GPU cluster + budget for frontier APIs in training loop.

So: the PATTERN is hardware-fit (inference); the SPECIFIC SAKANA TRAINING is not (we won't reproduce their RL training).

### Software / license fit

**MIXED — depends on weight release.**

- Operator doctrine: 100% OSS self-hosted. Proton is the single accepted exception. Symfonium is the single proprietary-app exception. Anthropic API via Pro subscription is the single AI API exception (covered by `claude-pro` alias).
- Sakana Fugu (the productized service) is commercial; using Fugu API would be a NEW exception requiring explicit doctrine update. **Not aligned.**
- Sakana Conductor weights — unclear. ICLR 2026 paper acceptance suggests methodology is published; weight release is paper-specific. Need to verify.
- Sakana research methodology (RL-trained orchestrator) — published as paper; reproducible in principle by anyone with the compute budget.

### Doctrine fit

- **Circulatory doctrine fit:** YES. A Conductor model fits cleanly on the AI orchestration host (Mac Mini Pro). Worker pool is on the AI inference host (Mac Studio). Information flow: orchestrator ← intent → worker pool → result. Same flow shape as existing tier-routing.
- **Work-routing doctrine fit:** This is a NEW LAYER above existing TIER 1/2/3 routing — the Conductor decides which TIER+MODEL to use, then routes. Doesn't conflict; extends.
- **Host-portability doctrine fit:** YES — 7B model on Ollama is portable across hosts.
- **Promotion criteria fit:** A Conductor-pattern POC would land in the agentic-class promotion gate, capability-validation phase. Aligns with existing Goose Posture 1 framing (read-only substrate, operator review mandatory before write actions).

### Recommendation

**STRATEGIC-WATCH for the specific Sakana implementation; ADOPT-PATTERN-NOT-IMPLEMENTATION for the architectural insight.**

Two parallel tracks:

**Track A — Strategic watch on Sakana Conductor weights / open release.**
- Add to `architecture-patterns/strategic-watch.md`
- Re-review trigger: (a) Sakana releases Conductor weights under permissive license, OR (b) an OSS analog (similar RL methodology, open weights) emerges
- Re-review cadence: every 90 days unless trigger fires earlier
- Watch sources: Sakana blog/GitHub, ICLR 2026 conference materials, Hugging Face for OSS analogs

**Track B — Pattern adoption: build a Conductor-pattern POC using existing local stack.**
- Create new deliverable D-NN-NNN (TBD; needs phase assignment by operator)
- Pattern: a Conductor is just a small LLM with a system prompt that knows the worker pool and routes
- POC implementation:
  - Conductor: Qwen2.5-7B-Instruct (already in our `_provenance/` corpus) on Mac Mini Pro Ollama (orchestration host per circulatory doctrine — orchestration function lives on the orchestration organ)
  - Worker pool: existing T1-T4 Ollama models on Mac Studio + `claude-pro` for frontier escalation
  - Routing surface: extend existing LiteLLM Gateway with a "/conductor" route that calls Qwen2.5-7B with a meta-prompt describing the pool
  - Initial Conductor logic: prompt-engineered (not RL-trained); essentially a smarter version of the existing tier-routing rules
- Effort: medium (1-2 weeks; mostly meta-prompt iteration and integration with LiteLLM)
- Dependencies: T1 System Prompt Library deliverable (already on locked roadmap) provides the substrate
- Critical path: NOT critical. This is an enhancement, not a blocker.
- Success criteria: measurable improvement on a defined benchmark (e.g., subset of LiveCodeBench-style problems) over the existing static T1-T4 routing rules

**Anti-recommendation: do NOT adopt Sakana Fugu commercial API.**
Violates 100% OSS self-hosted doctrine. Adds external dependency. Adds frontier-API cost on top of the operator's existing Anthropic Pro subscription. Reject this path with explicit rationale captured here so future re-surfacing has prior reasoning.

## Scope (Step 4)

### Track A — Strategic-watch entry

```yaml
# Append to docs/architecture-patterns/strategic-watch.md

- name: Sakana RL Conductor (open weights)
  added: 2026-05-08
  source: https://sakana.ai/learning-to-orchestrate/
  paper: https://arxiv.org/abs/2512.04388
  trigger:
    - sakana releases conductor weights under permissive license
    - oss analog (rl-trained orchestrator with open weights) appears
  next_review: 2026-08-08
  evaluation: docs/_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md
  related_doctrines:
    - work-routing-doctrine
    - local-model-tier-doctrine
    - local-prompt-library-doctrine
```

### Track B — Roadmap candidate

**Proposed deliverable:** `D-NN-NNN: Conductor-pattern POC using local stack`

- **Phase assignment:** TBD (operator owns phase placement; suggest Phase 18+ or new phase given Phase 17 work-in-flight)
- **Title:** Conductor-pattern POC — small-LLM orchestrator over local worker pool
- **Pattern:** apply Sakana RL Conductor architectural insight using existing stack
- **Substrate:** Qwen2.5-7B-Instruct on Mac Mini Pro Ollama as orchestrator (orchestration host per circulatory doctrine); existing T1-T4 worker pool on Mac Studio Ollama; LiteLLM Gateway on MS-01 Linux VM as routing surface
- **Initial implementation:** prompt-engineered (NOT RL-trained); future enhancement could explore RL training if compute budget surfaces
- **Effort:** medium
- **Dependencies:**
  - T1 System Prompt Library deliverable (locked roadmap; already T1-priority)
  - LiteLLM Gateway (existing)
  - Mac Studio Ollama (existing) — for the worker pool
  - Mac Mini Pro Ollama (NEW; small substrate to stand up) — for the Conductor itself
- **Risks:**
  - R-NN: meta-prompt-engineered Conductor may not outperform existing static T1-T4 routing rules; success criteria must be measurable up front
  - R-NN: integration with LiteLLM Gateway may surface routing-loop edge cases (Conductor calls itself recursively)
- **Critical-path:** NOT critical
- **Success criteria:** measurable improvement on defined benchmark vs existing static routing
- **Created via:** `scripts/roadmap-create.sh` once operator approves phase assignment

### Track C — Reject (Sakana Fugu commercial API)

Explicit rejection record:

- **Candidate:** Sakana Fugu commercial API (the productized service)
- **Reject rationale:**
  1. Violates 100% OSS self-hosted doctrine
  2. Adds external commercial dependency on Sakana
  3. Adds frontier-API spend on top of existing Anthropic Pro budget
  4. Sakana's own marketing positions Fugu as a paid service
- **Future re-surfacing condition:** if doctrine itself changes (operator decides to accept additional commercial AI APIs), re-evaluate; otherwise Fugu stays rejected

## Notes / observations

- This article is exceptionally well-aligned with operator's existing direction. The fact that operator's locked roadmap already includes "T1: System Prompt Library" suggests operator was independently arriving at the same insight (small-model-with-meta-prompt as orchestrator).
- The 7B Qwen2.5-7B base model is **already in operator's verified-models corpus** (`_provenance/Qwen__Qwen2.5-Coder-7B-Instruct.json`). Operator has the substrate to start a Conductor POC TODAY without any new model downloads.
- This is an example of where the "review thoroughly before dismissing" rule prevents value loss. A surface-level pattern-match might have read this as "another routing framework" and dismissed; the actual contribution is "RL-trainable meta-prompt-engineering" which is novel and useful even if we don't reproduce the training.

## Cross-references

- `architecture-facts/article-intake-protocol.md` — the protocol applied here (this is the first worked example)
- `architecture-facts/work-routing-doctrine.md` (D-17-95) — operator's existing routing doctrine
- `architecture-facts/local-model-tier-doctrine.md` — operator's tier framework
- `architecture-facts/local-prompt-library-doctrine.md` (D-17-90) — operator's prompt library doctrine
- `architecture-patterns/strategic-watch.md` — where Track A entry lands
- `_provenance/Qwen__Qwen2.5-Coder-7B-Instruct.json` — base-model substrate already verified
- Locked roadmap T1 priority: System Prompt Library + Cisco Provenance Kit (per `userMemories`)
- Master log Findings AA + BB — architectural truth substrate gap and misdiagnosis-via-tool-blame patterns this protocol guards against
