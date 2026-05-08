# Article Intake Protocol

**Date:** 2026-05-08
**Status:** Active doctrine
**Originating session:** 2026-05-08 architectural rework — operator surfaced quality problem
**Pairs with:** `architecture-patterns/strategic-watch.md`, `integration-audit-doctrine.md` Findings AA + BB

## Why this protocol exists

Across many sessions, articles describing potentially-relevant tools, patterns, or research have been:

- **Dismissed too quickly without thorough review.** Pattern-matched against memory and rejected without reading the actual content. Specific examples have been lost because they were never recorded.
- **Implemented too quickly without thorough review.** Pattern-matched against memory and partially adopted before the actual claims, license, and stack-fit were verified. This produced wasted effort and substrate residue.

Both failure modes share the same root cause: **the article was not actually read and evaluated against the operator's locked architecture before a verdict was rendered.** Memory and pattern-matching are not substitutes for reading.

This protocol forces the discipline. Every article goes through the same four steps. Every evaluation produces a written record. Every roadmap candidate (whether accepted, rejected, watched, or deferred) is captured durably so the work is never lost.

This is a meta-doctrine — it governs how we decide what to add to the platform.

## The protocol — four mandatory steps

### Step 1: Read the source

Before any other step, the article (or paper, or repo README, or research blog post) must be **actually read** by Claude or the operator.

Operational rules:
- Use `web_fetch` for the URL provided. If the canonical source is paywalled or 429-rate-limited, fall back to:
  - The publisher's own page (e.g., `sakana.ai/learning-to-orchestrate/` instead of VentureBeat aggregation)
  - The arxiv preprint if cited
  - The official GitHub repo README
  - Multiple aggregator articles to triangulate (with explicit acknowledgement that aggregators add interpretation)
- If the source can't be fetched at all, the evaluation MUST state that explicitly. Memory-based evaluation is forbidden.
- Quote the article minimally and never reproduce significant copyrighted passages — the evaluation document records the article's CLAIMS in our own words, not its prose.

Output: notes on actual claims, methodology, license, scope, performance numbers, dependencies. Distinguish claims that are well-substantiated from claims that need scrutiny.

### Step 2: Validate correctness via exhaustive research

Once claims are in hand, validate them against external evidence:

1. **Conversation search** (`conversation_search`) — has this article, this tool, or this pattern come up before in our sessions? Are there prior evaluations or prior dismissals to reconcile?
2. **Repo search** (Desktop Commander `start_search`) — does the repo already contain references, prior research, or partial implementations?
3. **Web validation** — independent sources confirming the claims. Beware of press-release reposts; prefer primary sources (papers, official repos, the project's own page).
4. **Stack-fit probe** — does the tool/pattern require dependencies that violate locked architecture decisions? (e.g., proprietary cloud APIs vs 100% OSS doctrine; specific cloud provider lock-in; closed-source weights when our doctrine requires open).

Output: correctness verdict ranked as one of:
- **Substantiated** — claims hold up; methodology is real; benchmarks are legitimate
- **Substantiated-with-caveats** — claims hold up but with material qualifications (e.g., "fraction of the cost" really means "fewer API calls, but still uses paid APIs")
- **Unsubstantiated** — claims overstated, benchmarks cherry-picked, or methodology insufficient
- **Cannot-verify** — we lack the evidence to rule either way

### Step 3: Decide roadmap fit given locked architecture

The platform has substantial locked architecture (`PROJECT_FRAMEWORK.md`, the architecture-facts corpus, the ADR series, the tier doctrines, the master log Findings). New candidates are evaluated against this corpus:

1. **Conceptual fit** — does the candidate solve a problem the platform actually has? Does it generalize, replace, or conflict with existing doctrine?
2. **Hardware fit** — does the candidate fit the current/near-future hardware fleet? (Per `2026-05-08-converged-platform-architecture.md`.)
3. **Software/license fit** — does the candidate's license match the 100% OSS self-hosted doctrine? Proton is the single accepted exception. Symfonium is the single proprietary-app exception. Anthropic API via Pro subscription is the single AI API exception.
4. **Doctrine fit** — does the candidate cohere with the operator's circulatory doctrine, work-routing doctrine, tier doctrine, host-portability doctrine?

Output: roadmap recommendation ranked as one of:
- **Adopt-now** — candidate clearly fits; create a deliverable with PMP+ITIL labels
- **Adopt-pattern-not-implementation** — the pattern is useful but the specific tool isn't; create a deliverable to apply the pattern using existing stack
- **Strategic-watch** — candidate may fit later; add to `strategic-watch.md` with explicit re-review trigger and review cadence
- **Defer** — candidate fits but blocked on prerequisite; capture the prerequisite explicitly
- **Reject** — candidate doesn't fit doctrine; capture WHY in the evaluation so future re-surfacing has prior reasoning to reference

### Step 4: Apply scope discipline + PMP+ITIL labels

Adopted candidates produce structured roadmap entries:

- Deliverable ID per `identifier-conventions.md`: D-NN-MM (where NN = phase, MM = sequence within phase)
- Severity / impact rating where applicable
- Dependencies (other D-NN-MMs, KI-NNNs, hardware acquisitions, license-availability)
- Effort estimate (low/medium/high; not weeks per operator's rule)
- Critical-path identification — does this deliverable gate other deliverables?
- Risks (R-NN) where applicable
- Knowledge items (KI-NNN) for blocked or watched candidates

Strategic-watch candidates get:
- Watch entry in `strategic-watch.md`
- Re-review trigger ("when X happens, re-evaluate")
- Re-review cadence (e.g., every 90 days unless trigger fires earlier)

Rejected candidates get:
- Evaluation document preserved in `_audit/article-evaluations/<slug>-<date>.md`
- Reasoning captured so future operators (or future Claude sessions) understand why this was rejected
- Reject is NOT silent — silent dismissal is the failure mode this protocol exists to prevent

### Step 5 (implied — never lose the work)

Every evaluation produces a written artifact in `docs/_audit/article-evaluations/`. Every roadmap candidate flows through `roadmap-create.sh` per the existing Roadmap Ingestion Flow Doctrine (D-17-39). Every strategic-watch item lives in `strategic-watch.md`.

If an evaluation is in-progress and the session ends, the in-progress artifact is committed with a clear `[STATUS: IN-PROGRESS]` header so the next session picks up where this one left off.

## Evaluation document template

Save evaluations at `docs/_audit/article-evaluations/<slug>-<YYYY-MM-DD>.md`.

```markdown
# <Article title>

**Date evaluated:** YYYY-MM-DD
**Source:** <URL>
**Authors:** <names or org>
**Publication venue:** <venue, peer-reviewed status>
**Evaluator:** <Claude session id or operator>
**Status:** <protocol step reached: read | researched | evaluated | decided>

## Source notes (Step 1 output)
[Bullet points capturing the article's actual claims in our own words]

## Validation (Step 2 output)
- Prior conversation search results: [findings]
- Repo search results: [findings]
- Web cross-references: [findings]
- Correctness verdict: <Substantiated | Substantiated-with-caveats | Unsubstantiated | Cannot-verify>
- Caveats: [list]

## Roadmap fit (Step 3 output)
- Conceptual fit: [assessment]
- Hardware fit: [assessment]
- Software/license fit: [assessment]
- Doctrine fit: [assessment]
- Recommendation: <Adopt-now | Adopt-pattern-not-implementation | Strategic-watch | Defer | Reject>

## Scope (Step 4 output)
[If adopted: deliverable ID + dependencies + effort estimate + critical-path]
[If watched: re-review trigger + cadence]
[If rejected: rationale, with sufficient detail for future re-surfacing]

## Cross-references
- Related architecture-facts: [list]
- Related ADRs: [list]
- Related master log Findings: [list]
```

## Anti-patterns this protocol rules out

- **Silent dismissal.** "I've seen something like this before" without naming the prior thing or capturing the comparison. If you can't name it, you don't actually know.
- **Pattern-match adoption.** "This sounds like X, let's adopt it." Without reading the actual claims, the comparison to X is unverified.
- **License ignorance.** Adopting a tool without checking its license against the OSS doctrine. The operator has explicit doctrine; protocol enforces checking.
- **No-record reject.** Rejecting without writing down why. Future re-surfacing of the same article re-runs the evaluation from scratch.
- **No-record adopt.** Adopting without writing down what was promised vs what was delivered. Drift goes undetected.
- **Memory-only evaluation.** Evaluating from training-data recall instead of fetching the article. Especially dangerous for dated content where Claude's knowledge may be stale.

## Application discipline

This protocol is applied EVERY time a new article, paper, tool, or pattern is surfaced for consideration. There are no exceptions for "obvious" cases:

- "Obviously good" tools still need license check + doctrine check
- "Obviously bad" tools still need a reject record so future operators don't re-surface them
- "Obviously already covered" tools still need a comparison record to verify they really are covered

The protocol is cheap (15-30 minutes per article) compared to the cost of unprincipled adoption (waste) or unprincipled dismissal (missed value).

## Application sub-rule for time-sensitive items

When an article surfaces something that may be time-bounded (a feature about to ship, a tool with a known sunset, a model with limited release window), the protocol can be compressed but never skipped:

1. Read source (mandatory)
2. Validate (compressed to web cross-references; defer prior-session search if urgent)
3. Decide fit (mandatory)
4. Capture (mandatory; as `[STATUS: PRELIMINARY]` if compressed)
5. Schedule full evaluation as a follow-up

The compression is logged in the evaluation document. A preliminary evaluation that becomes long-lived without ever being upgraded to a full evaluation is itself a doctrine violation.

## Cross-references

- `architecture-patterns/strategic-watch.md` — where strategic-watch items live
- `architecture-facts/integration-audit-doctrine.md` — Findings AA + BB about misdiagnosis-via-tool-blame and architectural truth substrate
- `_audit/article-evaluations/` — where evaluation records live (this directory may not exist yet; first evaluation creates it)
- `architecture-facts/identifier-conventions.md` — D-NN-MM, KI-NNN, R-NN labeling conventions
- Roadmap Ingestion Flow Doctrine (D-17-39) — `scripts/roadmap-create.sh` for creating new D-NN-MM rows from adopted candidates

## Status

**Active doctrine** as of 2026-05-08. First worked example is the Sakana RL Conductor evaluation at `_audit/article-evaluations/sakana-rl-conductor-2026-05-08.md`.
