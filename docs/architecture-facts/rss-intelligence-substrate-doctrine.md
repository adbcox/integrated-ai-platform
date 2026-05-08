# RSS Intelligence Substrate Doctrine

**Status:** ACTIVE
**Date authored:** 2026-05-08 (Tokyo travel session, `feat/rss-intelligence` branch)
**Source of truth:** `integrated_ai_workstation_complete_master_log.md` Sections 16, 17, 32 (operator-authored consolidated discussion document, 2026-05-06; pending QNAP ingest via `roadmap-create.sh` per D-17-35 PENDING-OPERATOR-INGEST pattern)
**Consumers:** D-17-136 (Technical Intelligence RSS), D-17-137 (Personal Briefing Engine)
**Substrate:** D-17-37 (artifact storage), D-17-39 (ingestion flow)

## Purpose

Codify the shared infrastructure between two deliberately-separate RSS-derived systems so neither deliverable reinvents substrate decisions. The two consumer systems share infrastructure but NOT policy; this doctrine fixes the shared layer.

## The two-system split (locked, not subject to merge)

Per master log Section 32:

**System A — Technical Intelligence RSS (D-17-136)**
- Goal: improve local AI workstation freshness and engineering decisions
- Output: local archive, technical digest, OpenProject WPs (formerly "Plane tickets" pre-D-17-04), benchmark candidates, Aider/OpenCode task briefs
- Scoring: technical relevance, model/tool relevance, release-tracking signal

**System B — Personal Briefing Engine (D-17-137)**
- Goal: daily personal/business/news awareness
- Output: Roca-style concise source-linked cards, perspective checks, personal relevance ranking
- Scoring: news/source/personal relevance; outrage-framing rejected
- Anti-pattern (locked from §17): "Do not build Roca RSS clone. Build local-first personal briefing engine." The point is not to reproduce Roca; it is to produce equivalent briefing utility on locally-controlled substrate without surveillance/ad framing.

These are two deliverables, not one. Splitting matters because scoring criteria, output shape, and personal-vs-technical relevance metrics diverge.

## Locked substrate (shared between A and B)

| Component | Choice | Reason |
|---|---|---|
| Aggregator | Miniflux (default) or FreshRSS (if UI/extensions matter) | Both true OSS. Miniflux is single Go binary, fewer moving parts. |
| Fetcher | Python fetch/export job | Deterministic, Git-trackable, no fair-code dependency on shared infra. |
| Metadata store | SQLite first, PostgreSQL when scale demands | Start simple. Promote on evidence. |
| Raw archive | QNAP (per D-17-37 substrate or sibling roadmap-artifacts tree) | Durable, AI-consultable via xindex. |
| Summarization | Ollama (existing T1-T4 worker pool) | No external API. Routes via litellm-gateway when deployed. |
| Output sink (technical) | OpenProject WPs via existing OP sync | Plane CE retired in D-17-04; OpenProject is canonical. |
| Output sink (briefing) | Operator decision (Obsidian / Nextcloud / daily email) | Different consumer, different sink. |
| Normalizer / dedupe / classifier | Python idempotent job (runs after raw archive, before metadata insert) | Re-runnable. Source bytes already preserved upstream so this stage can be re-run without re-fetching. |
| Metadata filters | Per-system policy layer over SQLite/Postgres | Explicitly the divergence point between D-17-136 (technical filters) and D-17-137 (personal filters). |
| Monitoring | Zabbix | Existing platform monitoring; new items per D-17-105 doctrine. |


## Pipeline order (canonical)

Per master log §16 and §17, the canonical flow shared by both systems is:

```
RSS feeds
  ↓
Miniflux / FreshRSS (aggregator polls)
  ↓
QNAP raw archive  ←── preserve source bytes BEFORE any transformation
  ↓
Python normalizer / dedupe / classifier (idempotent)
  ↓
SQLite / Postgres metadata (canonical query layer)
  ↓
Ollama embeddings + summaries (local; no external API)
  ↓
Per-system divergence:
  D-17-136 (Technical):  daily/weekly digest  →  OpenProject WPs / benchmark prompts / Aider+OpenCode task briefs
  D-17-137 (Briefing):   story clustering  →  source/perspective scoring  →  personal relevance ranker  →  daily briefing (Obsidian / Nextcloud / email / markdown)  →  archive + RAG loop
```

**Critical invariant:** raw archive happens BEFORE any normalization, dedupe, or filtering. This preserves source bytes for forensic re-processing, model retraining, and time-travel debugging. Downstream stages can be re-run without re-fetching from sources (rate-limit safe).

**Different policies, same plumbing** (per master log §16/§17 framing):

| Axis | D-17-136 (Technical) | D-17-137 (Briefing) |
|---|---|---|
| Scoring | technical relevance, model/tool relevance | news/source scoring, personal relevance |
| Output unit | benchmark prompts, OpenProject WPs, task briefs | concise source-linked briefing cards |
| Filter dimension | model/tool/release-tracking | personal interest, perspective diversity, no-outrage |
| RAG loop | n/a (digests are write-once) | archive + RAG (briefings searchable for operator queries) |

## Excluded substrate (locked, with reasons)

Per master log Section 16 "Avoid as defaults":

| Tool | Why excluded for RSS pipeline |
|---|---|
| **n8n** | Source-available/fair-code (Sustainable Use License), NOT true OSS default. Per platform doctrine, infrastructure that touches every other system should be true OSS. n8n remains acceptable as a general workflow automation tool elsewhere on the platform per April 2026 planning, and remains acceptable as agent control plane substrate per the locked Symphony framing. The exclusion is RSS-pipeline-specific. |
| Pinecone (and any cloud vector DB) | Cloud/managed mismatch with 100% self-hosted doctrine. |
| Cloud RSS generators (RSS.app, Feedly, Inoreader) | Brittle, third-party-dependent, surveil reading habits. |
| Massive unfiltered Reddit/newsletter ingestion | Noise. Curation precedes ingestion. |

## Substitutions from master log writing date to current architecture

The master log (2026-05-06) referenced platform components that have since changed. Apply these substitutions when reading §16/§17/§32 against current substrate:

| Master log says | Current substrate |
|---|---|
| Plane CE output | OpenProject (Plane retired in D-17-04, commit 37f874c) |
| Mac Studio at .142 (and .146 in some references) | Mac Studio at .142 confirmed |
| "Mac Mini Pro" (orchestration) | Per circulatory doctrine: orchestration on Mac Mini Pro (.145); inference worker pool on Mac Studio (.142) |

Future substitutions land here as architecture evolves.

## Master log artifact handling

The master log is a 47KB consolidated discussion document at `/Users/adriancox/Downloads/integrated_ai_workstation_complete_master_log.md`. It is **research input**, not platform documentation; it does not belong in the integrated-ai-platform repo as committed markdown. Per D-17-37 storage substrate and D-17-39 ingestion flow, the canonical placement is:

```
/Users/admin/mnt/qnap-downloads/manual/roadmap-artifacts/<phase>/<deliverable>/source/integrated_ai_workstation_complete_master_log.md
```

Pointer scheme: `qnap://download/manual/roadmap-artifacts/<phase>/<deliverable>/source/integrated_ai_workstation_complete_master_log.md`

Ingest command (operator-side, requires QNAP mount on macmini):

```
scripts/roadmap-create.sh D-17-136 \
  "Technical Intelligence RSS" \
  --artifact /Users/adriancox/Downloads/integrated_ai_workstation_complete_master_log.md \
  --class source-files \
  --update-existing
```

Same artifact serves both D-17-136 and D-17-137 — second deliverable references via `qnap://` pointer without re-ingest.

## Cross-references

- Master log Section 16 (RSS intelligence ingestion) — verdict: PURSUE bounded
- Master log Section 17 (Roca-style Personal Briefing Engine) — verdict: PURSUE
- Master log Section 32 (RSS/RAG relationship) — explicit two-system split
- Master log Section 33 (research backlog) — `every future item gets logged, even if SKIP`; sweep into strategic-watch.md / candidate-tools.md as separate work
- D-17-37 — artifact storage substrate (DONE)
- D-17-39 — roadmap ingestion flow (DONE)
- D-17-04 — Plane → OpenProject migration (DONE; closes the doctrine-says-Plane gap)
- candidate-tools.md — "Inbox Zero" entry (related; Gmail tier scope-gated bookmark)
- circulatory-doctrine.md — orchestration/inference organ split (Mac Mini Pro / Mac Studio)

## Status

ACTIVE. This doctrine is the shared-substrate layer. D-17-136 and D-17-137 codify the per-system policy on top.
