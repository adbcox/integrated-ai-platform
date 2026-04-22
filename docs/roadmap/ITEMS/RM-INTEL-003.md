# RM-INTEL-003

- **ID:** `RM-INTEL-003`
- **Title:** Personalized real-news briefing with interest-aware ranking, source-quality controls, and anti-clickbait summarization
- **Category:** `INTEL`
- **Type:** `System`
- **Status:** `Accepted`
- **Maturity:** `M2`
- **Priority:** `High`
- **Priority class:** `P2`
- **Queue rank:** `4`
- **Target horizon:** `soon`
- **LOE:** `M`
- **Strategic value:** `4`
- **Architecture fit:** `4`
- **Execution risk:** `2`
- **Dependency burden:** `2`
- **Readiness:** `near`

## Description

Build a personalized news-briefing system that surfaces real, relevant, non-clickbait news based on the user’s interests, with source-quality controls, bias/quality checks, and concise briefings.

The system should prioritize categories such as:
- AI
- technology
- sports
- world news
- business

It must explicitly avoid low-quality clickbait ranking behavior and instead produce a briefing format closer to “need to know” plus “worth knowing” than viral-feed behavior.

## Why it matters

This is a high-value personal-assistant and intelligence feature because it converts broad news volume into something curated, usable, and actually relevant. It also fits the system’s preference for governed, explainable outputs rather than opaque attention-maximizing feeds.

## Key requirements

- ingest real news from vetted or approved sources
- rank stories by user relevance and topic interest
- suppress low-quality clickbait-style items
- expose why a story was chosen
- support multiple briefing categories (AI, tech, sports, world, business)
- support daily briefing and on-demand briefing modes
- support concise summarization with links back to source identity
- preserve source diversity and quality-awareness

## Affected systems

- intelligence/news branch
- future personal-assistant briefing surfaces
- control/dashboard surfaces where briefings may be displayed

## Expected file families

- future source registry and source-quality policy files
- future briefing-generation logic
- future ranking/config files
- future UI/display surfaces for briefings

## Dependencies

- `RM-GOV-009` for external connector and intake posture if feeds/APIs are used
- future personal-assistant or dashboard consumption surfaces

## Risks and issues

### Key risks
- source-quality drift
- hidden bias from source overconcentration
- weak clickbait filtering if source/ranking policy is too loose

### Known issues / blockers
- exact source acquisition strategy still needs bounding
- source-trust and ranking policy must be explicit before broad rollout

## CMDB / asset linkage

- minimal direct CMDB linkage; primarily a user-facing intelligence surface

## Grouping candidates

- `RM-GOV-009`
- future personal-assistant branch items

## Grouped execution notes

- Shared-touch rationale: connector policy, feed ingestion, and personal-assistant consumption overlap.
- Repeated-touch reduction estimate: medium.
- Grouping recommendation: `Bundle after connector policy is stable`

## Recommended first milestone

Define a bounded daily briefing slice for a small set of approved sources and a small set of user-interest categories, with explicit source-quality and anti-clickbait ranking rules.

## Status transition notes

- Expected next status: `Planned`
- Transition condition: source policy, briefing shape, and ranking rules are defined
- Validation / closeout condition: one daily/on-demand briefing slice exists with source-aware ranking and non-clickbait behavior

## Notes

This item is the canonical roadmap home for the “real news I care about” feature and should remain distinct from generic search or noisy social/newsfeed behavior.