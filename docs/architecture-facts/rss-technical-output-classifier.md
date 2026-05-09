# D-17-136 Technical Intelligence RSS: Output Classifier

**Status:** DRAFT — first iteration (refine after first week of routed output)
**Date authored:** 2026-05-09 (feat/rss-intelligence branch)
**Source of truth:** D-17-136 goals; technical-relevance rubric per-dimension signals; master log Section 16
**Consumer:** D-17-136 (Technical Intelligence RSS)
**Related:** `rss-technical-relevance-rubric.md` (upstream signal source); `rss-intelligence-substrate-doctrine.md` (pipeline context)

## Purpose

This classifier routes articles that score ≥11 on the technical-relevance rubric to one of four output buckets: digest-only (included in weekly digest, no further action), OpenProject WP (operator-tracked work item), benchmark prompt (new benchmark scenario), or Aider/OpenCode task brief (delegatable coding task). It consumes per-dimension scores from the technical-relevance rubric (Source Quality, Technical-Domain Fit, Actionability, Novelty, Depth, Operational Impact, Time Sensitivity) and applies deterministic routing rules to emit structured output for each bucket.

## Output Types

**Digest-only:** Article included in the weekly/daily technical digest but requires no further routing. Default fallback when no routing patterns match.

**OpenProject WP:** Operational work item the operator should track and prioritize for execution. Examples: critical security update affecting your stack, breaking change in a tool you actively use, new capability enabling a platform improvement.

**Benchmark prompt:** Suggests a new evaluation scenario, candidate model, or performance dimension for D-17-126 (benchmark substrate) or related benchmark tracks. Examples: novel ML benchmark, new optimization technique applicability, performance trade-off worth measuring.

**Aider/OpenCode task brief:** Concrete, delegatable coding task with a bounded change scope. Examples: implement a feature from an open-source tool release, fix a compatibility issue, add support for a new hardware platform.

## Routing Logic

**OpenProject WP triggers (any of):**
- Source ≥ 2 AND Operational Impact = 3 AND Time Sensitivity = 2 (trustworthy operational urgency)
- Source = 3 AND Operational Impact ≥ 2 (locked source + direct impact)
- Actionability = 3 AND Operational Impact = 3 AND Time Sensitivity = 2 (urgent, actionable, high impact)

**Benchmark prompt triggers (any of):**
- Domain Fit = 3 AND Depth ≥ 2 AND Novelty ≥ 2 (deep novel research in your domains)
- Novelty = 3 AND Domain Fit ≥ 2 AND Depth ≥ 2 (groundbreaking result with relevance)
- (Example subdomains: AI/ML research papers, model layer architecture innovation, agent stack capability gap identification)

**Aider/OpenCode task brief triggers (any of):**
- Actionability = 3 AND Operational Impact = 3 AND Time Sensitivity ≤ 1 (actionable, important, not urgent → delegatable)
- Actionability = 3 AND Domain Fit ∈ {2, 3} AND Depth ≥ 2 AND Time Sensitivity = 0 (clear technical direction, evergreen)

**Tie-breaking:** If an item qualifies for multiple buckets, prioritize in this order: OpenProject WP (operational urgency) > Aider task brief (code-level action) > Benchmark prompt (research signal) > Digest-only.

**Default:** If no pattern matches, route to digest-only.

## Output Templates

### OpenProject WP Template (DRAFT)

```
Title: "[D-17-136] {article_title}"
Category: rss-derived
Labels: rss-derived, {technical-domain}, {urgency-tier}
Body:
  **Context:**
  {article_summary_2-3_sentences}

  **Source:** {url}

  **Proposed Action:**
  {concrete_next_step_or_decision}

  **Acceptance Criteria:**
  - [ ] {criterion_1}
  - [ ] {criterion_2}
  - [ ] {criterion_3}

  **Rubric Scores:** Source={S}, Domain={D}, Actionability={A}, Novelty={N}, Depth={De}, Impact={I}, Time={T}
```

### Benchmark Prompt Template (DRAFT)

```
Target Suite: D-17-126 (primary) or D-17-129 (codex51)
Prompt: "Evaluate whether the following technique improves benchmark performance:
{technique_description}

Reference: {article_url}
Metric to measure: {proposed_metric}
Expected impact: {hypothesis}
Model(s): {default_model_list_or_operator_selection}"

Success Criteria:
- Measurement runs without error
- Results comparative to baseline (including null-hypothesis case)
- Finding logged to benchmark substrate
```

### Aider/OpenCode Task Brief Template (DRAFT)

```
Component: {target_file_or_module}
Problem: {concrete_technical_gap}
Change Description: {what_needs_to_change}
Validation:
  - Run {test_command}
  - Verify {behavioral_outcome}
Expected diff: {rough_line_count_estimate} lines
Reference: {article_url}
```

## Routing Decision Examples

**Example 1: Ollama v0.5 Security Fix**
- Scores: Source=3, Domain=3, Actionability=3, Novelty=1, Depth=2, Impact=3, Time=2
- Patterns matched: OpenProject WP (Source≥2 + Impact=3 + Time=2)
- Route: OpenProject WP (operational security urgency)
- Output: WP title "[D-17-136] Ollama v0.5 Security Patch — High-Priority Upgrade", labels: rss-derived, model-layer, security-urgent

**Example 2: Novel Research Paper on Local LLM Quantization**
- Scores: Source=2, Domain=3, Actionability=1, Novelty=3, Depth=3, Impact=1, Time=0
- Patterns matched: Benchmark prompt (Domain=3 + Depth=3 + Novelty=3)
- Route: Benchmark prompt (research signal without operational urgency)
- Output: Prompt targets D-17-126; proposes quantization technique evaluation; references paper; expects metric comparison

**Example 3: Feature Request: Add Support for New Hardware Platform**
- Scores: Source=2, Domain=2, Actionability=3, Novelty=1, Depth=2, Impact=3, Time=0
- Patterns matched: Aider task brief (Actionability=3 + Impact=3 + Time≤1)
- Route: Aider/OpenCode task brief
- Output: Component target identified, change scope estimated, validation steps clear, reference to upstream feature request

**Example 4: Historical Analysis of LLM Training Approaches**
- Scores: Source=2, Domain=2, Actionability=0, Novelty=0, Depth=3, Impact=0, Time=0
- Patterns matched: None
- Route: Digest-only (reference material, no triggering pattern)

## Open Questions for Operator Validation

1. **Benchmark trigger specificity:** Should benchmark prompts further filter by subdomain (e.g., only AI/ML research + model layer, exclude infrastructure/hardware)? Current rule admits all Domain=3 + Depth≥2 + Novelty≥2.

2. **Multi-bucket priority:** When an item triggers both WP and task-brief (high actionability + high impact, but split on time sensitivity threshold), should the urgency flag determine routing, or should both outputs be generated?

3. **Source quality gatekeeping:** OpenProject WP rule requires Source≥2. Should operator-locked feeds (Source=3) auto-floor to WP even if other signals are weak (e.g., Source=3 + high actionability, low impact)?

4. **Aider task brief delegation:** Who receives the task brief? Local Aider invocation via prompt, or OpenProject task linked to a work assignment?

5. **False-positive handling:** If a high-depth article from a trusted source matches WP rules but is actually evergreen (Time=0), should the classifier defer to manual review, or should Time=0 override the WP trigger?

## Pipeline Integration

The classifier operates as the **routing stage** downstream of the technical-relevance ranker in the D-17-136 pipeline. Per-dimension scores and the final relevance rank (0–18) are cached in SQLite metadata from the ranker stage. The classifier (Ollama, model TBD; same instance as relevance ranker) receives the routing-logic rules as **prompt context** and generates output template fills + routing decision + reasoning. Output routers (separate jobs, not this WP) consume the classifier's decision and dispatch to OpenProject API (WPs), benchmark substrate (prompts), or task-brief queue (Aider).

Template iteration: After first week of routed output, review rendering quality, manual vs automated precision, and whether templates capture sufficient context for downstream consumers. Refine templates and routing thresholds based on operator feedback.

## Cross-references

- `docs/architecture-facts/rss-technical-relevance-rubric.md` — upstream signal source (7 per-dimension scores)
- `docs/architecture-facts/rss-intelligence-substrate-doctrine.md` — pipeline context
- `docs/PROJECT_FRAMEWORK.md` D-17-136 — Technical Intelligence RSS framework row
- D-17-126 — benchmark substrate (target for benchmark-prompt output)
- D-17-129 — codex51 benchmark track (alternate target)
- Master log Section 16 (RSS intelligence ingestion, 2026-05-06) — D-17-136 goals and output types
